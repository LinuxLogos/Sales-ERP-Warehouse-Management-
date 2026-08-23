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
