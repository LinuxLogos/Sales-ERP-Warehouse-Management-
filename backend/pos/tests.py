from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Customer, Lot, Product, Sale, SaleCostAllocation, Supplier, User


class SalesCostTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(id='USR-TEST', email='test@example.com', role='ADMIN', nom='Test')
        self.user.set_password('secret')
        self.user.save()
        self.customer = Customer.objects.create(id='CUS-TEST', nom='Client')
        supplier = Supplier.objects.create(id='SUP-TEST', nom='Fournisseur')
        self.product = Product.objects.create(id='PRD-TEST', nom='Cable', type_tracabilite='LOT', prix_vente=250)
        for quantity, price in [(100, 185), (100, 210)]:
            response = self.client.post('/api/purchases/', {'fournisseur_id': supplier.id, 'lignes': [{'produit_id': self.product.id, 'quantite': quantity, 'prix_unitaire': price}]}, format='json', HTTP_X_USER_ID=self.user.id)
            self.assertEqual(response.status_code, 200)

    def test_fifo_sale_creates_exact_cost_allocations(self):
        response = self.client.post('/api/sales/', {'client_id': self.customer.id, 'lignes': [{'produit_id': self.product.id, 'quantite': 120, 'prix_unitaire': 250, 'remise': 0}]}, format='json', HTTP_X_USER_ID=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['total'], 30000.0)
        allocations = SaleCostAllocation.objects.all().order_by('id')
        self.assertEqual(allocations.count(), 2)
        self.assertEqual(sum((item.total_cost for item in allocations), Decimal('0')), Decimal('22700.00'))
        self.assertEqual(Lot.objects.get(pk=allocations[0].inventory_lot_id).quantite_restante, Decimal('0'))

    def test_proforma_does_not_change_stock_or_create_payment(self):
        stock_before = self.product.stock
        response = self.client.post('/api/sales/', {'proforma': True, 'client_id': self.customer.id, 'lignes': [{'produit_id': self.product.id, 'quantite': 2, 'prix_unitaire': 250, 'remise': 10}]}, format='json', HTTP_X_USER_ID=self.user.id)
        self.assertEqual(response.status_code, 200)
        sale = Sale.objects.get(pk=response.json()['data']['id'])
        self.assertEqual(sale.statut, 'PROFORMA')
        self.assertEqual(sale.total_ttc, Decimal('490'))
        self.assertEqual(self.product.stock, stock_before)
        self.assertFalse(sale.payments.exists())

    def test_proforma_conversion_and_isolation(self):
        com1 = User.objects.create(id='COM1', email='com1@test.com', role='COMMERCIAL', nom='Commercial 1')
        com2 = User.objects.create(id='COM2', email='com2@test.com', role='COMMERCIAL', nom='Commercial 2')
        res_prof = self.client.post('/api/sales/', {'proforma': True, 'client_id': self.customer.id, 'lignes': [{'produit_id': self.product.id, 'quantite': 5, 'prix_unitaire': 250}]}, format='json', HTTP_X_USER_ID=com1.id)
        sale_id = res_prof.json()['data']['id']

        # Commercial 2 list sales should not include proforma from Commercial 1
        res_c2 = self.client.get('/api/sales/', HTTP_X_USER_ID=com2.id)
        c2_ids = [s['id'] for s in res_c2.json()['data']]
        self.assertNotIn(sale_id, c2_ids)

        # Convert proforma
        res_conv = self.client.post(f'/api/proformas/{sale_id}/convert/', format='json', HTTP_X_USER_ID=com1.id)
        self.assertEqual(res_conv.status_code, 200)
        sale = Sale.objects.get(pk=sale_id)
        self.assertEqual(sale.statut, 'VALIDEE')

    def test_import_excel_sales(self):
        csv_data = f"reference,quantite,prix\n{self.product.id},3,250"
        res = self.client.post('/api/sales/import-excel/', {'content': csv_data, 'proforma': True, 'client_id': self.customer.id}, format='json', HTTP_X_USER_ID=self.user.id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['data']['statut'], 'PROFORMA')

    def test_cashier_payment_and_session(self):
        caissier = User.objects.create(id='CAI1', email='cai@test.com', role='CAISSIER', nom='Caissier 1')

        # Open session
        res_open = self.client.post('/api/caisse/session/', {'action': 'OPEN', 'fond_de_caisse_initial': 50000}, format='json', HTTP_X_USER_ID=caissier.id)
        self.assertEqual(res_open.status_code, 200)

        # Commercial creates validated sale
        res_sale = self.client.post('/api/sales/', {'client_id': self.customer.id, 'statut_paiement': 'EN_ATTENTE', 'lignes': [{'produit_id': self.product.id, 'quantite': 2, 'prix_unitaire': 250}]}, format='json', HTTP_X_USER_ID=self.user.id)
        sale_id = res_sale.json()['data']['id']

        # Caissier pays 1000 FCFA for a 500 FCFA sale (change = 500)
        res_pay = self.client.post(f'/api/payments/{sale_id}/', {'paiements': [{'montant': 1000, 'mode': 'ESPECES'}]}, format='json', HTTP_X_USER_ID=caissier.id)
        self.assertEqual(res_pay.status_code, 200)
        self.assertEqual(res_pay.json()['data']['monnaie_rendue'], 500.0)
        self.assertEqual(res_pay.json()['data']['label_facture'], 'Payé – non livré')

        # Close session
        res_close = self.client.post('/api/caisse/session/', {'action': 'CLOSE', 'montant_final_especes': 50500}, format='json', HTTP_X_USER_ID=caissier.id)
        self.assertEqual(res_close.status_code, 200)
        self.assertEqual(float(res_close.json()['data']['ecart']), 0.0)

    def test_transfers_and_service_contracts(self):
        m1 = self.client.post('/api/magasins/', {'nom': 'Magasin Principal'}, format='json', HTTP_X_USER_ID=self.user.id).json()['data']
        m2 = self.client.post('/api/magasins/', {'nom': 'Magasin Secondaire'}, format='json', HTTP_X_USER_ID=self.user.id).json()['data']

        # Transfer stock
        res_trf = self.client.post('/api/transfers/', {'magasin_source_id': m1['id'], 'magasin_dest_id': m2['id'], 'produit_id': self.product.id, 'quantite': 10}, format='json', HTTP_X_USER_ID=self.user.id)
        self.assertEqual(res_trf.status_code, 200)

        # Service contract
        res_ctr = self.client.post('/api/service-contracts/', {'client_id': self.customer.id, 'titre': 'Déploiement Réseau', 'type_service': 'RESEAU', 'montant': 150000}, format='json', HTTP_X_USER_ID=self.user.id)
        self.assertEqual(res_ctr.status_code, 200)
        self.assertEqual(res_ctr.json()['data']['titre'], 'Déploiement Réseau')
