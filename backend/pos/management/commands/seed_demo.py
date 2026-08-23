from django.core.management.base import BaseCommand
from pos.models import Category, Customer, Product, Supplier, User

class Command(BaseCommand):
    help = 'Create the LinuxLogos demo account and starter catalog'

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(id='USR-000001', defaults={'email': 'admin@linuxlogos.tg', 'nom': 'Admin', 'prenom': 'Principal', 'role': 'ADMIN'})
        admin.email = 'admin@linuxlogos.tg'; admin.role = 'ADMIN'; admin.nom = 'Admin'; admin.prenom = 'Principal'; admin.actif = True; admin.set_password('admin123'); admin.save()
        for ident, email, role, first_name, last_name in [
            ('USR-CAISSE', 'caissier@linuxlogos.tg', 'CAISSIER', 'Awa', 'Caisse'),
            ('USR-STOCK', 'magasinier@linuxlogos.tg', 'MAGASINIER', 'Koffi', 'Stock'),
            ('USR-VENTE', 'vendeur@linuxlogos.tg', 'VENDEUR', 'Mina', 'Vente'),
        ]:
            operator, _ = User.objects.get_or_create(id=ident, defaults={'email': email, 'nom': last_name, 'prenom': first_name, 'role': role})
            operator.email = email; operator.nom = last_name; operator.prenom = first_name; operator.role = role; operator.actif = True; operator.set_password('demo123'); operator.save()
        customer, _ = Customer.objects.get_or_create(id='CUS-000001', defaults={'nom': 'Client de passage', 'type': 'PARTICULIER'})
        category, _ = Category.objects.get_or_create(id='CAT-000001', defaults={'nom': 'Informatique', 'description': 'Matériel informatique'})
        supplier, _ = Supplier.objects.get_or_create(id='SUP-000001', defaults={'nom': 'Dell Technologies', 'entreprise': 'Dell', 'pays': 'USA'})
        products = [
            ('PRD-000001', 'Dell Inspiron 15', 'Dell', 'SERIE', 350000, 450000, 3),
            ('PRD-000002', 'SSD Kingston 512GB', 'Kingston', 'LOT', 28000, 35000, 5),
            ('PRD-000003', 'RJ45 Cat6', 'Generic', 'LOT', 180, 250, 10),
        ]
        for ident, name, brand, trace, buy, sell, threshold in products:
            Product.objects.update_or_create(id=ident, defaults={'nom': name, 'marque': brand, 'type_tracabilite': trace, 'prix_achat': buy, 'prix_vente': sell, 'seuil_min': threshold, 'categorie': category, 'fournisseur': supplier})
        self.stdout.write(self.style.SUCCESS('Demo data ready: admin@linuxlogos.tg / admin123'))
