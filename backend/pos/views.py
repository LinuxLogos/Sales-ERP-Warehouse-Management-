from django.shortcuts import render
import uuid
import jwt
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from .models import (ActivityLog, CashMovement, Category, Customer, Expense, Lot,
					 Payment, Product, Purchase, PurchaseItem, Return, Sale,
					 SaleCostAllocation, SaleDetail, Setting, StockMovement,
					 Supplier, Unit, User)


def ok(data, message='OK'): return JsonResponse({'success': True, 'data': data, 'message': message})
def fail(message, code=400): return JsonResponse({'success': False, 'data': None, 'message': message}, status=code)


def api_root(request):
	return ok({
		'service': 'LinuxLogos POS API',
		'status': 'online',
		'endpoints': '/api/'
	})


def health_view(request):
	return ok({'service': 'LinuxLogos POS API', 'status': 'online'})


def uid(prefix): return f'{prefix}-{uuid.uuid4().hex[:10].upper()}'
def body(request):
	import json
	try: return json.loads(request.body or '{}')
	except json.JSONDecodeError: return {}
def user_from(request):
	value = request.headers.get('X-User-Id')
	bearer = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
	if bearer:
		try: value = jwt.decode(bearer, settings.SECRET_KEY, algorithms=['HS256'])['user_id']
		except (jwt.InvalidTokenError, KeyError): return None
	return User.objects.filter(id=value, actif=True).first()
def serialize(obj):
	if isinstance(obj, Product):
		return {'id': obj.id, 'nom': obj.nom, 'marque': obj.marque, 'modele': obj.modele, 'reference': obj.reference, 'categorie_id': obj.categorie_id, 'type_tracabilite': obj.type_tracabilite, 'prix_achat': float(obj.prix_achat), 'prix_vente': float(obj.prix_vente), 'seuil_min': float(obj.seuil_min), 'fournisseur_id': obj.fournisseur_id, 'statut': obj.statut, 'stock': float(obj.stock)}
	if isinstance(obj, (Customer, Supplier, Category, Expense, Return, Purchase, Sale, StockMovement, ActivityLog, CashMovement)):
		return {field.name: getattr(obj, field.attname) for field in obj._meta.fields}
	if isinstance(obj, (Lot, Unit, SaleDetail)):
		return {field.name: getattr(obj, field.attname) for field in obj._meta.fields}
	return obj
def audit(user, action, module, reference, details=''):
	ActivityLog.objects.create(id=uid('LOG'), utilisateur=user, role=user.role if user else '', action=action, module=module, reference=reference, details=details)


@csrf_exempt
@api_view(['POST'])
def login_view(request):
	data = body(request); user = User.objects.filter(email__iexact=str(data.get('email', '')).strip(), actif=True).first()
	if not user or not user.verify_password(data.get('password', '')): return fail('Identifiants invalides', 401)
	audit(user, 'LOGIN', 'AUTH', user.email, 'Connexion')
	now = datetime.now(timezone.utc)
	access = jwt.encode({'user_id': user.id, 'type': 'access', 'exp': now + timedelta(minutes=30)}, settings.SECRET_KEY, algorithm='HS256')
	refresh = jwt.encode({'user_id': user.id, 'type': 'refresh', 'exp': now + timedelta(days=7)}, settings.SECRET_KEY, algorithm='HS256')
	return ok({'access': access, 'refresh': refresh, 'user': {'id': user.id, 'email': user.email, 'role': user.role, 'nom': user.nom, 'prenom': user.prenom}})


@csrf_exempt
@api_view(['POST'])
def refresh_view(request):
	try:
		token = body(request).get('refresh', '')
		payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
		if payload.get('type') != 'refresh': raise jwt.InvalidTokenError()
		access = jwt.encode({'user_id': payload['user_id'], 'type': 'access', 'exp': datetime.now(timezone.utc) + timedelta(minutes=30)}, settings.SECRET_KEY, algorithm='HS256')
		return ok({'access': access})
	except jwt.InvalidTokenError: return fail('Refresh token invalide', 401)


@api_view(['GET'])
def me_view(request):
	user, error = require_user(request)
	if error: return error
	return ok({'id': user.id, 'email': user.email, 'role': user.role, 'nom': user.nom, 'prenom': user.prenom})


def require_user(request):
	user = user_from(request)
	return user, None if user else fail('Authentification requise', 401)


@csrf_exempt
@api_view(['GET', 'POST'])
def products_view(request):
	if request.method == 'GET': return ok([serialize(p) for p in Product.objects.all().order_by('nom')])
	user, error = require_user(request)
	if error: return error
	if user.role != 'ADMIN': return fail('Permission refusée', 403)
	data = body(request)
	product = Product.objects.create(id=uid('PRD'), nom=data.get('nom', '').strip(), prix_achat=Decimal(str(data.get('prix_achat', 0) or 0)), prix_vente=Decimal(str(data.get('prix_vente', 0) or 0)), seuil_min=Decimal(str(data.get('seuil_min', 0) or 0)), type_tracabilite=data.get('type_tracabilite', 'LOT'))
	audit(user, 'CREATE', 'PRODUCTS', product.id, product.nom)
	return ok(serialize(product), 'Produit créé')

@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def product_detail_view(request, product_id):
	product = Product.objects.filter(id=product_id).first()
	if not product: return fail('Produit introuvable', 404)
	if request.method == 'GET': return ok(serialize(product))
	user, error = require_user(request)
	if error: return error
	if user.role != 'ADMIN': return fail('Permission refusée', 403)
	if request.method == 'DELETE': product.delete(); return ok(True)
	data = body(request)
	for field in ['nom', 'marque', 'modele', 'reference', 'type_tracabilite', 'statut']:
		if field in data: setattr(product, field, data[field])
	for field in ['prix_achat', 'prix_vente', 'seuil_min']:
		if field in data: setattr(product, field, Decimal(str(data[field] or 0)))
	product.save(); return ok(serialize(product))


def crud_view(request, model, prefix, fields, admin_only=False):
	user, error = require_user(request)
	if error: return error
	if request.method == 'GET': return ok([serialize(o) for o in model.objects.all().order_by('-created_at')])
	if admin_only and user.role != 'ADMIN': return fail('Permission refusée', 403)
	data = body(request); values = {field: data.get(field, '') for field in fields}
	if model is Expense:
		values['montant'] = Decimal(str(values['montant'] or 0)); values['date'] = values['date'] or date.today(); values['heure'] = values['heure'] or datetime.now().time()
	if model is Customer: values['nom'] = values.get('nom') or 'Client de passage'
	obj = model.objects.create(id=uid(prefix), **values)
	audit(user, 'CREATE', model.__name__.upper(), obj.id)
	return ok(serialize(obj), 'Créé')

@csrf_exempt
@api_view(['GET', 'POST'])
def customers_view(request): return crud_view(request, Customer, 'CUS', ['type','nom','prenom','telephone','email','adresse','entreprise'])
@csrf_exempt
@api_view(['GET', 'POST'])
def suppliers_view(request): return crud_view(request, Supplier, 'SUP', ['nom','entreprise','telephone','email','adresse','pays'], True)


@csrf_exempt
@api_view(['GET', 'POST'])
@transaction.atomic
def purchases_view(request):
	user, error = require_user(request)
	if error: return error
	if request.method == 'GET': return ok([serialize(x) for x in Purchase.objects.all().order_by('-created_at')])
	if user.role != 'ADMIN': return fail('Permission refusée', 403)
	data = body(request); lines = data.get('lignes', [])
	if not lines: return fail('L’achat doit contenir au moins un produit')
	purchase = Purchase.objects.create(id=uid('ACH'), reference=uid('ACH'), fournisseur_id=data.get('fournisseur_id'), date=data.get('date') or date.today(), mode_paiement=data.get('mode_paiement', 'ESPECES'))
	subtotal = Decimal('0'); created_lines = []
	for line in lines:
		product = Product.objects.get(id=line['produit_id']); qty = Decimal(str(line.get('quantite', 0))); price = Decimal(str(line.get('prix_unitaire', 0)))
		if qty <= 0 or price < 0: return fail('Quantité ou prix invalide')
		subtotal += qty * price
		created_lines.append((product, qty, price))
		PurchaseItem.objects.create(purchase=purchase, product=product, quantity=qty, unit_price=price, subtotal=qty * price)
		stock_before = product.stock
		StockMovement.objects.create(id=uid('MOV'), date=date.today(), heure=datetime.now().time(), type='ENTREE', produit=product, quantite=qty, reference=purchase.reference, motif='Achat', stock_avant=stock_before, stock_apres=stock_before + qty, utilisateur=user)
	purchase.sous_total = subtotal; purchase.frais_acquisition = Decimal(str(data.get('frais_acquisition', 0) or 0)); purchase.cout_total = subtotal + purchase.frais_acquisition; purchase.save()
	for product, qty, price in created_lines:
		fee = (purchase.frais_acquisition * qty * price / subtotal) / qty if subtotal else Decimal('0')
		actual_cost = price + fee
		if product.type_tracabilite == 'SERIE':
			for index in range(int(qty)): Unit.objects.create(id=uid('UNT'), code=uid('UNT'), produit=product, achat=purchase, cout_unitaire_reel=actual_cost, actual_unit_cost=actual_cost)
		else: Lot.objects.create(id=uid('LOT'), code=uid('LOT'), produit=product, achat=purchase, quantite_initiale=qty, quantite_restante=qty, cout_unitaire_reel=actual_cost, actual_unit_cost=actual_cost)
		PurchaseItem.objects.filter(purchase=purchase, product=product).update(allocated_costs=fee * qty)
	CashMovement.objects.create(id=uid('CASH'), date=date.today(), heure=datetime.now().time(), type='ACHAT', reference=purchase.reference, description='Achat', montant_sortie=purchase.cout_total, mode_paiement=purchase.mode_paiement, categorie='Achats', utilisateur=user)
	audit(user, 'CREATE', 'PURCHASES', purchase.id, str(purchase.cout_total)); return ok({'id': purchase.id})


@csrf_exempt
@api_view(['GET', 'POST'])
@transaction.atomic
def sales_view(request):
	user, error = require_user(request)
	if error: return error
	if request.method == 'GET': return ok([serialize(x) for x in Sale.objects.all().order_by('-created_at')])
	data = body(request); lines = data.get('lignes', [])
	if not lines: return fail('La vente doit contenir au moins un produit')
	is_proforma = bool(data.get('proforma'))
	sale = Sale.objects.create(id=uid('DEV') if is_proforma else uid('VTE'), reference=uid('DEV') if is_proforma else uid('VTE'), client_id=data.get('client_id'), vendeur=user, date=date.today(), heure=datetime.now().time(), mode_paiement=data.get('mode_paiement', 'ESPECES'), statut_paiement='EN_ATTENTE' if is_proforma else data.get('statut_paiement', 'PAYE'), statut='PROFORMA' if is_proforma else data.get('statut', 'PAYEE'))
	if is_proforma:
		subtotal = Decimal('0'); discount = Decimal('0')
		for line in lines:
			product = Product.objects.get(id=line['produit_id']); qty = Decimal(str(line.get('quantite', 0))); price = Decimal(str(line.get('prix_unitaire', product.prix_vente))); rem = Decimal(str(line.get('remise', 0) or 0))
			if qty <= 0 or price < 0 or rem < 0 or rem > price * qty: return fail('Quantité, prix ou remise invalide')
			line_total = price * qty - rem; subtotal += price * qty; discount += rem
			SaleDetail.objects.create(id=uid('DEVD'), vente=sale, produit=product, produit_nom=product.nom, quantite=qty, prix_unitaire=price, remise=rem, sous_total=line_total, montant_vente_net=line_total, net_amount=line_total, cout_statut='NON_RECONCILIE')
		sale.sous_total = subtotal; sale.remise_totale = discount; sale.total_ttc = subtotal - discount; sale.save(update_fields=['sous_total', 'remise_totale', 'total_ttc'])
		audit(user, 'CREATE', 'PROFORMAS', sale.id, str(sale.total_ttc)); return ok({'id': sale.id, 'reference': sale.reference, 'total': float(sale.total_ttc), 'statut': sale.statut}, 'Proforma créée')
	subtotal = Decimal('0'); discount = Decimal('0')
	for line in lines:
		product = Product.objects.select_for_update().get(id=line['produit_id']); qty = Decimal(str(line.get('quantite', 0))); price = Decimal(str(line.get('prix_unitaire', product.prix_vente))); rem = Decimal(str(line.get('remise', 0) or 0)); before = Decimal(str(product.stock))
		if qty <= 0 or before < qty: return fail(f'Stock insuffisant pour {product.nom} (dispo: {before})')
		if product.type_tracabilite == 'SERIE':
			selected = list(product.units.select_for_update().filter(etat='DISPONIBLE').order_by('created_at')[:int(qty)]); [Unit.objects.filter(pk=u.pk).update(etat='VENDU', sale=sale) for u in selected]; trace = ';'.join(u.id for u in selected)
			allocations = [(u, None, Decimal('1'), u.actual_unit_cost) for u in selected]
		else:
			left = qty; traces = []; allocations = []
			for lot in product.lots.select_for_update().filter(quantite_restante__gt=0).order_by('created_at'):
				take = min(left, lot.quantite_restante); lot.quantite_restante -= take; lot.save(); traces.append(lot.id); allocations.append((None, lot, take, lot.actual_unit_cost or lot.cout_unitaire_reel)); left -= take
				if left <= 0: break
			trace = ';'.join(traces)
		line_total = price * qty - rem; subtotal += price * qty; discount += rem
		allocated_quantity = sum((quantity for _, _, quantity, _ in allocations), Decimal('0'))
		if allocated_quantity != qty: return fail(f'Impossible de rapprocher le coût de {product.nom}')
		for unit, lot, quantity, unit_cost in allocations:
			source_type = 'SERIE' if unit else 'LOT'; source_id = unit.id if unit else lot.id
			allocated_net = line_total * quantity / qty if qty else Decimal('0'); total_cost = quantity * unit_cost; margin = allocated_net - total_cost
			detail = SaleDetail.objects.create(id=uid('VTED'), vente=sale, produit=product, produit_nom=product.nom, quantite=quantity, prix_unitaire=price, remise=rem * quantity / qty if qty else Decimal('0'), sous_total=allocated_net, unite_id=source_id if unit else '', lot_id=source_id if lot else '', source_type=source_type, source_id=source_id, montant_vente_net=allocated_net, cout_unitaire_reel=unit_cost, cout_total=total_cost, marge_brute=margin, taux_marge=(margin / allocated_net * 100 if allocated_net else 0), cout_statut='RECONCILIE', net_amount=allocated_net, total_cost=total_cost, gross_margin=margin, margin_rate=(margin / allocated_net * 100 if allocated_net else 0))
			SaleCostAllocation.objects.create(sale_item=detail, source_type=source_type, inventory_unit=unit, inventory_lot=lot, quantity=quantity, unit_cost=unit_cost, total_cost=total_cost)
		StockMovement.objects.create(id=uid('MOV'), date=date.today(), heure=datetime.now().time(), type='SORTIE', produit=product, quantite=qty, reference=sale.reference, motif='Vente', stock_avant=before, stock_apres=before-qty, utilisateur=user)
	sale.sous_total = subtotal; sale.remise_totale = discount; sale.total_ttc = subtotal-discount; sale.save()
	if sale.statut_paiement == 'PAYE':
		Payment.objects.create(id=uid('PAY'), sale=sale, amount=sale.total_ttc, method=sale.mode_paiement, date=date.today(), status='PAID')
		CashMovement.objects.create(id=uid('CASH'), date=date.today(), heure=datetime.now().time(), type='VENTE', reference=sale.reference, description='Vente', montant_entree=sale.total_ttc, mode_paiement=sale.mode_paiement, categorie='Ventes', utilisateur=user)
	audit(user, 'CREATE', 'SALES', sale.id, str(sale.total_ttc)); return ok({'id': sale.id, 'total': float(sale.total_ttc)})


@csrf_exempt
@api_view(['POST'])
@transaction.atomic
def payment_view(request, sale_id):
	user, error = require_user(request)
	if error: return error
	sale = Sale.objects.select_for_update().filter(id=sale_id).first()
	if not sale: return fail('Vente introuvable', 404)
	data = body(request); payments = data.get('paiements', [])
	if not payments: return fail('Au moins un paiement est requis')
	paid = sum((Decimal(str(item.get('montant', 0) or 0)) for item in payments), Decimal('0'))
	if paid <= 0: return fail('Le montant doit être positif')
	already_paid = sum((item.amount for item in sale.payments.filter(status='PAID')), Decimal('0'))
	remaining = sale.total_ttc - already_paid
	if paid < remaining: return fail(f'Montant insuffisant : reste {remaining}')
	for item in payments:
		amount = Decimal(str(item.get('montant', 0) or 0))
		if amount <= 0: return fail('Montant de paiement invalide')
		Payment.objects.create(id=uid('PAY'), sale=sale, amount=amount, method=item.get('mode', 'ESPECES'), date=date.today(), status='PAID', reference=item.get('reference', ''))
	CashMovement.objects.create(id=uid('CASH'), date=date.today(), heure=datetime.now().time(), type='VENTE', reference=sale.reference, description='Encaissement vente', montant_entree=min(paid, remaining), mode_paiement='MIXTE' if len(payments) > 1 else payments[0].get('mode', 'ESPECES'), categorie='Ventes', utilisateur=user)
	sale.statut_paiement = 'PAYE'; sale.statut = 'PAYEE'; sale.save(update_fields=['statut_paiement', 'statut'])
	audit(user, 'PAYMENT', 'SALES', sale.id, str(paid))
	return ok({'vente_id': sale.id, 'montant_recu': float(paid), 'reste': float(remaining), 'monnaie': float(paid - remaining), 'statut_paiement': sale.statut_paiement})


@api_view(['GET'])
def cashier_pending_view(request):
	user, error = require_user(request)
	if error: return error
	if user.role not in ['ADMIN', 'CAISSIER', 'RESPONSABLE']: return fail('Permission refusée', 403)
	sales = Sale.objects.filter(statut_paiement='EN_ATTENTE', statut='PAYEE').order_by('-created_at')
	return ok([serialize(item) for item in sales])


@api_view(['GET'])
def deliveries_view(request):
	user, error = require_user(request)
	if error: return error
	sales = Sale.objects.filter(statut_paiement='PAYE', statut_livraison__in=['EN_ATTENTE', 'PREPAREE']).order_by('-created_at')
	return ok([serialize(item) for item in sales])


@csrf_exempt
@api_view(['POST'])
def confirm_delivery_view(request, sale_id):
	user, error = require_user(request)
	if error: return error
	sale = Sale.objects.filter(id=sale_id).first()
	if not sale: return fail('Vente introuvable', 404)
	if sale.statut_paiement != 'PAYE': return fail('La vente doit être payée avant livraison', 409)
	if sale.statut_livraison == 'LIVREE': return fail('La vente est déjà livrée', 409)
	sale.statut_livraison = 'LIVREE'; sale.statut = 'LIVREE'; sale.save(update_fields=['statut_livraison', 'statut'])
	audit(user, 'DELIVER', 'SALES', sale.id, 'Livraison confirmée')
	return ok(serialize(sale), 'Livraison confirmée')


@csrf_exempt
@api_view(['GET', 'POST'])
def returns_view(request):
	user, error = require_user(request)
	if error: return error
	if request.method == 'GET': return ok([serialize(x) for x in Return.objects.all().order_by('-created_at')])
	data = body(request); product = Product.objects.get(id=data.get('produit_id')); obj = Return.objects.create(id=uid('RET'), reference=uid('RET'), vente_id=data.get('vente_id'), produit=product, produit_nom=product.nom, quantite=Decimal(str(data.get('quantite', 0))), date=date.today(), motif=data.get('motif', ''), gravite=data.get('gravite', 'MOYENNE'), description=data.get('description', ''), utilisateur=user)
	audit(user, 'CREATE', 'RETURNS', obj.id); return ok({'id': obj.id})


@csrf_exempt
@api_view(['GET', 'POST'])
def expenses_view(request):
	return crud_view(request, Expense, 'DEP', ['montant','categorie','sous_categorie','date','heure','beneficiaire','mode_paiement','type','description'])

@api_view(['GET'])
def stock_movements_view(request): return ok([serialize(x) for x in StockMovement.objects.all().order_by('-date', '-heure')])
@api_view(['GET'])
def treasury_view(request):
	movements = list(CashMovement.objects.all().order_by('-date', '-heure')); balance = sum((x.montant_entree - x.montant_sortie for x in movements), Decimal('0'))
	return ok({'balance': float(balance), 'movements': [serialize(x) for x in movements]})

@api_view(['GET'])
def dashboard_view(request):
	user, error = require_user(request)
	if error: return error
	sales = Sale.objects.all(); purchases = Purchase.objects.all(); expenses = Expense.objects.all(); movements = CashMovement.objects.all(); details = SaleDetail.objects.filter(cout_statut='RECONCILIE')
	ca = sum((x.total_ttc for x in sales), Decimal('0')); cogs = sum((x.cout_total for x in details), Decimal('0')); achats = sum((x.cout_total for x in purchases), Decimal('0')); depenses = sum((x.montant for x in expenses if x.type != 'ACQUISITION'), Decimal('0')); cash = sum((x.montant_entree-x.montant_sortie for x in movements), Decimal('0'))
	stock_value = sum((x.quantite_restante * (x.cout_unitaire_reel or x.actual_unit_cost) for x in Lot.objects.all()), Decimal('0')) + sum((x.cout_unitaire_reel or x.actual_unit_cost for x in Unit.objects.filter(etat='DISPONIBLE')), Decimal('0'))
	alerts = [dict(serialize(p), statut='RUPTURE' if p.stock == 0 else 'FAIBLE') for p in Product.objects.all() if p.stock <= p.seuil_min]
	today_sales = sales.filter(date=date.today()); gross_margin = ca - cogs; return ok({'financial': {'ca': float(ca), 'cogs': float(cogs), 'achats': float(achats), 'depenses': float(depenses), 'margeBrute': float(gross_margin), 'resultat': float(gross_margin-depenses), 'tresorerie': float(cash), 'valeurStock': float(stock_value), 'nbVentes': sales.count(), 'nbAchats': purchases.count()}, 'todayCA': float(sum((x.total_ttc for x in today_sales), Decimal('0'))), 'todaySalesCount': today_sales.count(), 'alerts': alerts, 'recentSales': [serialize(x) for x in sales.order_by('-created_at')[:5]], 'salesByDay': [], 'topProducts': [], 'lowStock': len([x for x in alerts if x['statut']=='FAIBLE']), 'outOfStock': len([x for x in alerts if x['statut']=='RUPTURE'])})


@api_view(['GET'])
def accounting_view(request):
	user, error = require_user(request)
	if error: return error
	sales = Sale.objects.all(); purchases = Purchase.objects.all(); expenses = Expense.objects.all(); movements = CashMovement.objects.all()
	details = SaleDetail.objects.filter(cout_statut='RECONCILIE').select_related('vente', 'produit').order_by('-vente__created_at', 'id')
	ca = sum((item.total_ttc for item in sales), Decimal('0')); cogs = sum((item.cout_total for item in details), Decimal('0'))
	depenses = sum((item.montant for item in expenses if item.type != 'ACQUISITION'), Decimal('0')); cash = sum((item.montant_entree - item.montant_sortie for item in movements), Decimal('0'))
	stock_value = sum((item.quantite_restante * (item.cout_unitaire_reel or item.actual_unit_cost) for item in Lot.objects.all()), Decimal('0')) + sum((item.cout_unitaire_reel or item.actual_unit_cost for item in Unit.objects.filter(etat='DISPONIBLE')), Decimal('0'))
	margin = ca - cogs
	return ok({'sales': [serialize(detail) for detail in details[:200]], 'financial': {'ca': float(ca), 'cogs': float(cogs), 'achats': float(sum((item.cout_total for item in purchases), Decimal('0'))), 'depenses': float(depenses), 'margeBrute': float(margin), 'resultat': float(margin - depenses), 'tresorerie': float(cash), 'valeurStock': float(stock_value), 'nbVentes': sales.count(), 'nbAchats': purchases.count()}})

@api_view(['GET'])
def analytics_view(request): return ok({'salesByDay': [], 'topProducts': []})
@api_view(['GET'])
def forecast_view(request): return ok({'sales': [], 'treasury': []})
@api_view(['GET'])
def logs_view(request): return ok([serialize(x) for x in ActivityLog.objects.all().order_by('-timestamp')[:500]])

# Create your views here.
