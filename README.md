# LinuxLogos POS

Migration de l'application Google Apps Script vers React/TypeScript et Django REST.

## Démarrage

API Django :

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Frontend React :

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Interface : http://127.0.0.1:5173/
API : http://127.0.0.1:8000/api/

Compte de démonstration : `admin@linuxlogos.tg` / `admin123`.

## Fonctionnalités

- Authentification admin/vendeur et journal d'activité
- Dashboard financier et alertes stock
- POS avec panier, validation de vente et décrément du stock
- Stock par lots ou unités sérialisées
- Produits, clients, fournisseurs, achats, retours et dépenses
- Trésorerie, comptabilité, analytics, prévisions et endpoints REST
