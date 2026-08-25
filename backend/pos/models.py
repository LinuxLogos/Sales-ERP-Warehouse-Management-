from decimal import Decimal
from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Magasin(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    nom = models.CharField(max_length=120)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class User(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, default='COMMERCIAL')
    nom = models.CharField(max_length=120)
    prenom = models.CharField(max_length=120, blank=True)
    actif = models.BooleanField(default=True)
    magasin = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    def set_password(self, raw): self.password = make_password(raw)
    def verify_password(self, raw): return check_password(raw, self.password)


class Permission(models.Model):
    code = models.CharField(primary_key=True, max_length=60)
    name = models.CharField(max_length=120)
    level = models.CharField(max_length=10, default='READ')


class Role(models.Model):
    code = models.CharField(primary_key=True, max_length=30)
    name = models.CharField(max_length=120)
    permissions = models.ManyToManyField(Permission, through='RolePermission')


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, default='READ')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['role', 'permission'], name='unique_role_permission')]


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'role'], name='unique_user_role')]


class Category(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    nom = models.CharField(max_length=120)
    parent_id = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Supplier(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    nom = models.CharField(max_length=160)
    entreprise = models.CharField(max_length=160, blank=True)
    telephone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    pays = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Product(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    nom = models.CharField(max_length=180)
    marque = models.CharField(max_length=120, blank=True)
    modele = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    categorie = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    type_tracabilite = models.CharField(max_length=10, default='LOT')
    prix_achat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    prix_vente = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    seuil_min = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fournisseur = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    statut = models.CharField(max_length=10, default='ACTIF')
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def stock(self):
        if self.type_tracabilite == 'SERIE': return self.units.filter(etat='DISPONIBLE').count()
        return self.lots.aggregate(total=models.Sum('quantite_restante'))['total'] or Decimal('0')


class Customer(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    type = models.CharField(max_length=20, default='PARTICULIER')
    nom = models.CharField(max_length=120)
    prenom = models.CharField(max_length=120, blank=True)
    telephone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    entreprise = models.CharField(max_length=160, blank=True)
    points_fidelite = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Coupon(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    code = models.CharField(max_length=40, unique=True)
    type_remise = models.CharField(max_length=20, default='POURCENTAGE')  # POURCENTAGE, MONTANT_FIXE
    valeur = models.DecimalField(max_digits=14, decimal_places=2)
    actif = models.BooleanField(default=True)
    date_expiration = models.DateField(null=True, blank=True)


class ServiceContract(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    reference = models.CharField(max_length=32, unique=True)
    client = models.ForeignKey(Customer, on_delete=models.CASCADE)
    titre = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    type_service = models.CharField(max_length=80, default='DEPLOIEMENT')  # DEPLOIEMENT, RESEAU, MAINTENANCE, SECURITE
    montant = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, default='EN_COURS')  # PLANIFIE, EN_COURS, TERMINE, ANNULE
    created_at = models.DateTimeField(auto_now_add=True)


class CaisseSession(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    magasin = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.CASCADE)
    caissier = models.ForeignKey(User, on_delete=models.CASCADE)
    date_ouverture = models.DateTimeField(auto_now_add=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)
    fond_de_caisse_initial = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_final_especes = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ecart = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, default='OUVERTE')
    notes = models.TextField(blank=True)


class Purchase(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    reference = models.CharField(max_length=32, unique=True)
    fournisseur = models.ForeignKey(Supplier, null=True, on_delete=models.SET_NULL)
    date = models.DateField()
    sous_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    frais_acquisition = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cout_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    mode_paiement = models.CharField(max_length=20, default='ESPECES')
    statut = models.CharField(max_length=20, default='VALIDE')
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    allocated_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)


class Lot(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    code = models.CharField(max_length=32)
    magasin = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.SET_NULL)
    produit = models.ForeignKey(Product, related_name='lots', on_delete=models.CASCADE)
    achat = models.ForeignKey(Purchase, null=True, blank=True, on_delete=models.SET_NULL)
    quantite_initiale = models.DecimalField(max_digits=14, decimal_places=2)
    quantite_restante = models.DecimalField(max_digits=14, decimal_places=2)
    cout_unitaire_reel = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Unit(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    code = models.CharField(max_length=32)
    magasin = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.SET_NULL)
    produit = models.ForeignKey(Product, related_name='units', on_delete=models.CASCADE)
    achat = models.ForeignKey(Purchase, null=True, blank=True, on_delete=models.SET_NULL)
    etat = models.CharField(max_length=20, default='DISPONIBLE')
    cout_unitaire_reel = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sale = models.ForeignKey('Sale', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class Sale(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    reference = models.CharField(max_length=32, unique=True)
    magasin = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.SET_NULL)
    client = models.ForeignKey(Customer, on_delete=models.PROTECT)
    vendeur = models.ForeignKey(User, on_delete=models.PROTECT)
    date = models.DateField()
    heure = models.TimeField()
    sous_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remise_totale = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_recu = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monnaie_rendue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    mode_paiement = models.CharField(max_length=20, default='ESPECES')
    statut_paiement = models.CharField(max_length=20, default='EN_ATTENTE')
    statut = models.CharField(max_length=20, default='VALIDEE')  # PROFORMA, VALIDEE, PAYEE, LIVREE
    statut_livraison = models.CharField(max_length=20, default='EN_ATTENTE')
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    proforma_commercial = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='proformas')
    created_at = models.DateTimeField(auto_now_add=True)


class SaleDetail(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    vente = models.ForeignKey(Sale, related_name='details', on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.PROTECT)
    produit_nom = models.CharField(max_length=180)
    quantite = models.DecimalField(max_digits=14, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=14, decimal_places=2)
    remise = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sous_total = models.DecimalField(max_digits=14, decimal_places=2)
    unite_id = models.TextField(blank=True)
    lot_id = models.TextField(blank=True)
    source_type = models.CharField(max_length=10, blank=True, default='')
    source_id = models.CharField(max_length=32, blank=True, default='')
    montant_vente_net = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cout_unitaire_reel = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cout_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    marge_brute = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_marge = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cout_statut = models.CharField(max_length=20, default='NON_RECONCILIE')
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gross_margin = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    margin_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)


class SaleCostAllocation(models.Model):
    sale_item = models.ForeignKey(SaleDetail, related_name='cost_allocations', on_delete=models.CASCADE)
    source_type = models.CharField(max_length=10)
    inventory_unit = models.ForeignKey(Unit, null=True, blank=True, on_delete=models.PROTECT)
    inventory_lot = models.ForeignKey(Lot, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)


class Payment(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    sale = models.ForeignKey(Sale, related_name='payments', on_delete=models.CASCADE)
    caisse_session = models.ForeignKey(CaisseSession, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    monnaie_rendue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    method = models.CharField(max_length=30)
    date = models.DateField()
    status = models.CharField(max_length=20, default='PAID')
    reference = models.CharField(max_length=80, blank=True)


class CashMovement(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    date = models.DateField()
    heure = models.TimeField()
    type = models.CharField(max_length=20)
    reference = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    montant_entree = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_sortie = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    mode_paiement = models.CharField(max_length=20, blank=True)
    categorie = models.CharField(max_length=80, blank=True)
    utilisateur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class Expense(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    reference = models.CharField(max_length=32, unique=True)
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    categorie = models.CharField(max_length=80)
    sous_categorie = models.CharField(max_length=80, blank=True)
    date = models.DateField()
    heure = models.TimeField()
    beneficiaire = models.CharField(max_length=160, blank=True)
    mode_paiement = models.CharField(max_length=20, default='ESPECES')
    type = models.CharField(max_length=20, default='GENERALE')
    description = models.TextField(blank=True)
    utilisateur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class StockMovement(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    date = models.DateField()
    heure = models.TimeField()
    type = models.CharField(max_length=20)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    magasin_source = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.SET_NULL, related_name='movements_out')
    magasin_dest = models.ForeignKey(Magasin, null=True, blank=True, on_delete=models.SET_NULL, related_name='movements_in')
    quantite = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=40)
    motif = models.CharField(max_length=120)
    stock_avant = models.DecimalField(max_digits=14, decimal_places=2)
    stock_apres = models.DecimalField(max_digits=14, decimal_places=2)
    utilisateur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class StockTransfer(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    reference = models.CharField(max_length=40, unique=True)
    magasin_source = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name='transfers_out')
    magasin_dest = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name='transfers_in')
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.DecimalField(max_digits=14, decimal_places=2)
    statut = models.CharField(max_length=20, default='EFFECTUE')
    demandeur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class Return(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    reference = models.CharField(max_length=32, unique=True)
    vente = models.ForeignKey(Sale, on_delete=models.PROTECT)
    produit = models.ForeignKey(Product, on_delete=models.PROTECT)
    produit_nom = models.CharField(max_length=180)
    quantite = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField()
    motif = models.CharField(max_length=120)
    gravite = models.CharField(max_length=20, default='MOYENNE')
    description = models.TextField(blank=True)
    utilisateur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class ActivityLog(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    timestamp = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=20)
    action = models.CharField(max_length=40)
    module = models.CharField(max_length=40)
    reference = models.CharField(max_length=40, blank=True)
    details = models.TextField(blank=True)


class Setting(models.Model):
    cle = models.CharField(primary_key=True, max_length=80)
    valeur = models.TextField(blank=True)