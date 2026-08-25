import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Boxes, Calculator, ChevronDown, LayoutDashboard, LogOut, Menu, Package, Plus, Receipt, RotateCcw, Search, ShoppingCart, Truck, Users, Wallet, X, ArrowLeftRight, FileText, CheckCircle2, BarChart3 } from 'lucide-react'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
type UserRole = 'ADMIN' | 'COMMERCIAL' | 'CAISSIER' | 'MAGASINIER' | 'RESPONSABLE'
type User = { id: string; email: string; role: UserRole; nom: string; prenom: string; magasin_id?: string }
type Product = { id: string; nom: string; marque?: string; reference?: string; type_tracabilite: string; prix_vente: number; prix_achat: number; seuil_min: number; stock: number; statut: string }
type Entity = Record<string, any>

const money = (value: number) => `${Math.round(Number(value || 0)).toLocaleString('fr-FR')} FCFA`
const dateLabel = (value: string) => value ? new Date(value).toLocaleDateString('fr-FR') : '-'

async function request(path: string, options: RequestInit = {}, user?: User) {
  const token = localStorage.getItem('linuxlogos_access')
  try {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(user ? { 'X-User-Id': user.id } : {}),
        ...(options.headers || {})
      }
    })
    const result = await response.json()
    if (!response.ok || result.success === false) throw new Error(result.message || 'Erreur serveur')
    return result.data
  } catch (err: any) {
    if (err instanceof TypeError && err.message.includes('fetch')) {
      throw new Error('OFFLINE_NETWORK_ERROR')
    }
    throw err
  }
}

const allNavigation = [
  ['dashboard', 'Dashboard', LayoutDashboard, ['ADMIN', 'COMMERCIAL', 'CAISSIER', 'MAGASINIER', 'RESPONSABLE']],
  ['pos', 'Ventes (POS)', ShoppingCart, ['ADMIN', 'COMMERCIAL', 'RESPONSABLE']],
  ['import-excel', 'Import Excel', FileText, ['ADMIN', 'COMMERCIAL', 'RESPONSABLE']],
  ['proformas', 'Devis / Proformas', Receipt, ['ADMIN', 'COMMERCIAL', 'RESPONSABLE']],
  ['caisse-session', 'Session Caisse', Wallet, ['ADMIN', 'CAISSIER', 'RESPONSABLE']],
  ['cashier-pending', 'Caisse & Paiements', Wallet, ['ADMIN', 'CAISSIER', 'RESPONSABLE']],
  ['deliveries', 'Livraisons Magasin', Truck, ['ADMIN', 'MAGASINIER', 'RESPONSABLE']],
  ['transfers', 'Transferts Inter-Magasins', ArrowLeftRight, ['ADMIN', 'MAGASINIER', 'RESPONSABLE']],
  ['products', 'Produits & Prix', Package, ['ADMIN', 'COMMERCIAL', 'MAGASINIER', 'RESPONSABLE']],
  ['stock', 'Stock Multi-Magasins', Boxes, ['ADMIN', 'MAGASINIER', 'RESPONSABLE']],
  ['magasins', 'Magasins', Boxes, ['ADMIN', 'RESPONSABLE']],
  ['crm', 'Contrats de Service (CRM)', FileText, ['ADMIN', 'COMMERCIAL', 'RESPONSABLE']],
  ['customers', 'Clients & Fidélité', Users, ['ADMIN', 'COMMERCIAL', 'CAISSIER', 'RESPONSABLE']],
  ['suppliers', 'Fournisseurs', Truck, ['ADMIN', 'MAGASINIER', 'RESPONSABLE']],
  ['purchases', 'Achats', ShoppingCart, ['ADMIN', 'MAGASINIER', 'RESPONSABLE']],
  ['returns', 'Retours & Remboursements', RotateCcw, ['ADMIN', 'CAISSIER', 'MAGASINIER', 'RESPONSABLE']],
  ['accounting', 'Comptabilité', Calculator, ['ADMIN', 'RESPONSABLE']],
  ['treasury', 'Trésorerie', Wallet, ['ADMIN', 'RESPONSABLE']],
  ['expenses', 'Dépenses', Receipt, ['ADMIN', 'RESPONSABLE']],
  ['reports', 'Rapports & Analytics', BarChart3, ['ADMIN', 'COMMERCIAL', 'CAISSIER', 'RESPONSABLE']],
  ['logs', 'Journal d\'Activité', Receipt, ['ADMIN', 'RESPONSABLE']]
] as const

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = useState('admin@linuxlogos.tg')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await request('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) })
      localStorage.setItem('linuxlogos_access', result.access)
      localStorage.setItem('linuxlogos_refresh', result.refresh)
      onLogin(result.user)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function quickLogin(role: UserRole) {
    const mockUsers: Record<UserRole, User> = {
      ADMIN: { id: 'USR-ADMIN', email: 'admin@linuxlogos.tg', role: 'ADMIN', nom: 'Administrateur', prenom: 'Global' },
      COMMERCIAL: { id: 'USR-COM', email: 'commercial@linuxlogos.tg', role: 'COMMERCIAL', nom: 'Vendeur', prenom: 'Commercial' },
      CAISSIER: { id: 'USR-CAI', email: 'caissier@linuxlogos.tg', role: 'CAISSIER', nom: 'Caissier', prenom: 'Caisse' },
      MAGASINIER: { id: 'USR-MAG', email: 'magasinier@linuxlogos.tg', role: 'MAGASINIER', nom: 'Magasinier', prenom: 'Livreur' },
      RESPONSABLE: { id: 'USR-RESP', email: 'responsable@linuxlogos.tg', role: 'RESPONSABLE', nom: 'Responsable', prenom: 'Magasin' },
    }
    onLogin(mockUsers[role])
  }

  return (
    <main className="login-shell">
      <form className="login-card" onSubmit={submit}>
        <div className="brand-mark"><ShoppingCart size={28} /></div>
        <p className="eyebrow">LINUXLOGOS / WMS & POS</p>
        <h1>Connexion WMS</h1>
        <p className="muted">Sélectionnez un rôle ou saisissez vos identifiants.</p>
        <div className="form-grid">
          <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
          <label>Mot de passe<input type="password" value={password} onChange={e => setPassword(e.target.value)} required /></label>
        </div>
        {error && <div className="error">{error}</div>}
        <button className="primary wide" disabled={loading}>{loading ? 'Connexion...' : 'Se connecter'}</button>
        <div style={{ marginTop: '.8rem', display: 'grid', gap: '.4rem' }}>
          <small><b>Changer rapidement de profil de démo :</b></small>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.4rem' }}>
            {(['COMMERCIAL', 'CAISSIER', 'MAGASINIER', 'RESPONSABLE', 'ADMIN'] as UserRole[]).map(r => (
              <button key={r} type="button" className="secondary" style={{ fontSize: '.7rem', padding: '.3rem .5rem' }} onClick={() => quickLogin(r)}>{r}</button>
            ))}
          </div>
        </div>
      </form>
    </main>
  )
}

function App() {
  const [user, setUser] = useState<User | null>(() => JSON.parse(localStorage.getItem('linuxlogos_user') || 'null'))
  const [route, setRoute] = useState('dashboard')
  const [drawer, setDrawer] = useState(false)

  function login(value: User) {
    localStorage.setItem('linuxlogos_user', JSON.stringify(value))
    setUser(value)
  }

  function logout() {
    localStorage.removeItem('linuxlogos_user')
    localStorage.removeItem('linuxlogos_access')
    localStorage.removeItem('linuxlogos_refresh')
    setUser(null)
  }

  if (!user) return <Login onLogin={login} />

  const allowedNav = allNavigation.filter(([_, __, ___, roles]) => (roles as readonly string[]).includes(user.role))
  const currentNavItem = allowedNav.find(([key]) => key === route) || allowedNav[0]
  const CurrentIcon = currentNavItem ? currentNavItem[2] : LayoutDashboard

  return (
    <div className="app-shell">
      <aside className={`sidebar ${drawer ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark small"><ShoppingCart size={20} /></div>
          <div><b>LinuxLogos WMS</b><span>2 Magasins & POS</span></div>
          <button className="icon-button mobile-only" onClick={() => setDrawer(false)}><X size={18} /></button>
        </div>
        <nav>
          {allowedNav.map(([key, label, Icon]) => (
            <button key={key} className={route === key ? 'nav-item active' : 'nav-item'} onClick={() => { setRoute(key); setDrawer(false) }}>
              <Icon size={18} />{label}
            </button>
          ))}
        </nav>
        <div className="user-footer">
          <div className="avatar">{(user.prenom || user.nom)[0]}</div>
          <div>
            <b>{user.prenom} {user.nom}</b>
            <span>Rôle : {user.role}</span>
          </div>
          <button className="icon-button" onClick={logout} title="Déconnexion"><LogOut size={17} /></button>
        </div>
      </aside>

      {drawer && <div className="scrim" onClick={() => setDrawer(false)} />}

      <main className="main">
        <header>
          <button className="icon-button mobile-only" onClick={() => setDrawer(true)}><Menu size={22} /></button>
          <div className="search"><Search size={17} /><input placeholder="Rechercher..." /></div>
          <div className="header-user">
            <Badge>{user.role}</Badge>
            <span>{user.prenom || user.nom}</span>
            <div className="avatar">{(user.prenom || user.nom)[0]}</div>
          </div>
        </header>

        <section className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow"><CurrentIcon size={14} /> ESPACE {user.role}</p>
              <h1>{currentNavItem ? currentNavItem[1] : 'Dashboard'}</h1>
            </div>
            <div className="status-dot">Système multi-magasins opérationnel</div>
          </div>
          <Page route={currentNavItem ? currentNavItem[0] : 'dashboard'} user={user} />
        </section>
      </main>
    </div>
  )
}

function Page({ route, user }: { route: string; user: User }) {
  if (route === 'dashboard') return <Dashboard user={user} />
  if (route === 'pos') return <POS user={user} />
  if (route === 'import-excel') return <ImportExcel user={user} />
  if (route === 'proformas') return <Proformas user={user} />
  if (route === 'caisse-session') return <CaisseSessionPage user={user} />
  if (route === 'cashier-pending') return <CashierPending user={user} />
  if (route === 'deliveries') return <Deliveries user={user} />
  if (route === 'transfers') return <Transfers user={user} />
  if (route === 'products') return <Products user={user} />
  if (route === 'stock') return <Stock user={user} />
  if (route === 'magasins') return <CrudPage title="Magasins" endpoint="magasins" fields={['nom', 'adresse', 'telephone']} user={user} />
  if (route === 'crm') return <ServiceContracts user={user} />
  if (route === 'customers') return <CustomersPage user={user} />
  if (route === 'suppliers') return <CrudPage title="Fournisseurs" endpoint="suppliers" fields={['nom', 'entreprise', 'telephone', 'pays']} user={user} />
  if (route === 'purchases') return <Purchases user={user} />
  if (route === 'returns') return <ReturnsPage user={user} />
  if (route === 'expenses') return <CrudPage title="Dépenses" endpoint="expenses" fields={['categorie', 'montant', 'date', 'description']} user={user} />
  if (route === 'treasury') return <Treasury user={user} />
  if (route === 'accounting') return <Accounting user={user} />
  if (route === 'reports') return <Reports user={user} />
  return <SimplePanel title="Journal d'activité" text="L'historique d'audit s'affiche ici." />
}

function Dashboard({ user }: { user: User }) {
  const [data, setData] = useState<any>(null)
  useEffect(() => { request('/dashboard/', {}, user).then(setData).catch(() => setData({})) }, [user])
  const f = data?.financial || {}
  return (
    <>
      <div className="welcome">
        <div>
          <p className="muted">{new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}</p>
          <h2>Bonjour {user.prenom || user.nom} ({user.role})</h2>
        </div>
        <button className="primary" onClick={() => window.location.reload()}>Actualiser</button>
      </div>
      <div className="metric-grid">
        <Metric label="CA total" value={money(f.ca)} note={`${f.nbVentes || 0} ventes`} accent />
        <Metric label="Aujourd'hui" value={money(data?.todayCA)} note={`${data?.todaySalesCount || 0} ventes`} />
        <Metric label="Résultat" value={money(f.resultat)} note="Après dépenses" />
        <Metric label="Trésorerie" value={money(f.tresorerie)} note="Solde disponible" />
      </div>
      <div className="two-columns">
        <Panel title="Activité récente">
          <div className="list">
            {(data?.recentSales || []).map((sale: Entity) => (
              <div className="list-row" key={sale.id}>
                <div><b>{sale.reference}</b><span>{dateLabel(sale.date)} - {sale.statut}</span></div>
                <strong>{money(sale.total_ttc)}</strong>
              </div>
            ))}
            {!data?.recentSales?.length && <Empty text="Aucune vente enregistrée" />}
          </div>
        </Panel>
        <Panel title="Alertes stock multi-magasins">
          <div className="list">
            {(data?.alerts || []).map((item: Product) => (
              <div className="list-row" key={item.id}>
                <div><b>{item.nom}</b><span>Seuil min : {item.seuil_min}</span></div>
                <Badge danger={item.statut === 'RUPTURE'}>{item.statut}</Badge>
              </div>
            ))}
            {!data?.alerts?.length && <Empty text="Stock sous contrôle" />}
          </div>
        </Panel>
      </div>
    </>
  )
}

function Metric({ label, value, note, accent }: { label: string; value: string; note: string; accent?: boolean }) {
  return <div className={`metric ${accent ? 'accent' : ''}`}><span>{label}</span><strong>{value}</strong><small>{note}</small></div>
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="panel"><div className="panel-heading"><h3>{title}</h3></div>{children}</section>
}

function Empty({ text }: { text: string }) { return <div className="empty">{text}</div> }
function Badge({ children, danger }: { children: React.ReactNode; danger?: boolean }) {
  return <span className={`badge ${danger ? 'danger' : ''}`}>{children}</span>
}

function POS({ user }: { user: User }) {
  const [products, setProducts] = useState<Product[]>([])
  const [customers, setCustomers] = useState<Entity[]>([])
  const [cart, setCart] = useState<Entity[]>([])
  const [query, setQuery] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [couponCode, setCouponCode] = useState('')
  const [appliedCoupon, setAppliedCoupon] = useState<Entity | null>(null)
  const [message, setMessage] = useState('')
  const [offlineCount, setOfflineCount] = useState<number>(() => JSON.parse(localStorage.getItem('linuxlogos_offline_sales') || '[]').length)

  const syncOfflineSales = async () => {
    const queue: any[] = JSON.parse(localStorage.getItem('linuxlogos_offline_sales') || '[]')
    if (!queue.length) return
    const remaining: any[] = []
    let synced = 0
    for (const item of queue) {
      try {
        await request('/sales/', { method: 'POST', body: JSON.stringify(item) }, user)
        synced++
      } catch (err) {
        remaining.push(item)
      }
    }
    localStorage.setItem('linuxlogos_offline_sales', JSON.stringify(remaining))
    setOfflineCount(remaining.length)
    if (synced > 0) {
      setMessage(`Synchronisation réussie : ${synced} vente(s) hors-ligne envoyée(s) au serveur.`)
      request('/products/').then(setProducts).catch(() => {})
    }
  }

  useEffect(() => {
    Promise.all([request('/products/'), request('/customers/', {}, user)]).then(([p, c]) => {
      setProducts(p)
      setCustomers(c)
      if (c.length) setCustomerId(c[0].id)
    }).catch(() => {})

    syncOfflineSales()
    window.addEventListener('online', syncOfflineSales)
    return () => window.removeEventListener('online', syncOfflineSales)
  }, [user])

  const shown = products.filter(p => p.stock > 0 && (p.nom.toLowerCase().includes(query.toLowerCase()) || (p.reference && p.reference.toLowerCase().includes(query.toLowerCase()))))
  const subtotal = cart.reduce((sum, item) => sum + item.prix_vente * item.qty, 0)

  let couponDiscount = 0
  if (appliedCoupon) {
    if (appliedCoupon.type_remise === 'POURCENTAGE') couponDiscount = subtotal * (appliedCoupon.valeur / 100)
    else couponDiscount = Math.min(subtotal, appliedCoupon.valeur)
  }
  const total = Math.max(0, subtotal - couponDiscount)

  function add(product: Product) {
    setCart(current => {
      const found = current.find(x => x.id === product.id)
      return found ? current.map(x => x.id === product.id ? { ...x, qty: Math.min(product.stock, x.qty + 1) } : x) : [...current, { ...product, qty: 1 }]
    })
  }

  async function applyCoupon() {
    if (!couponCode.trim()) return
    try {
      const res = await request('/coupons/validate/', { method: 'POST', body: JSON.stringify({ code: couponCode }) })
      setAppliedCoupon(res)
      setMessage(`Coupon ${res.code} appliqué (${res.valeur} ${res.type_remise === 'POURCENTAGE' ? '%' : 'FCFA'})`)
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  async function validateOrder(isProforma: boolean) {
    if (!cart.length) return setMessage('Panier vide.')
    const customer = customers.find(c => c.id === customerId)
    if (!customer) return setMessage('Sélectionnez un client.')

    const payload = {
      client_id: customer.id,
      proforma: isProforma,
      coupon_code: appliedCoupon ? appliedCoupon.code : undefined,
      lignes: cart.map(x => ({ produit_id: x.id, prix_unitaire: x.prix_vente, quantite: x.qty, remise: 0 }))
    }

    if (!navigator.onLine) {
      const queue: any[] = JSON.parse(localStorage.getItem('linuxlogos_offline_sales') || '[]')
      queue.push(payload)
      localStorage.setItem('linuxlogos_offline_sales', JSON.stringify(queue))
      setOfflineCount(queue.length)
      setMessage(`Mode hors-ligne : Vente enregistrée en local (${queue.length} en attente de synchro).`)
      setCart([])
      setAppliedCoupon(null)
      setCouponCode('')
      return
    }

    try {
      const result = await request('/sales/', { method: 'POST', body: JSON.stringify(payload) }, user)
      if (isProforma) {
        setMessage(`Proforma ${result.reference} créée (${money(result.total)}). Conservée dans vos devis.`)
      } else {
        setMessage(`Commande ${result.reference} validée par le commercial (${money(result.total)}). Transmise au Caissier pour paiement.`)
      }
      setCart([])
      setAppliedCoupon(null)
      setCouponCode('')
      setProducts(await request('/products/'))
    } catch (e: any) {
      if (e.message === 'OFFLINE_NETWORK_ERROR') {
        const queue: any[] = JSON.parse(localStorage.getItem('linuxlogos_offline_sales') || '[]')
        queue.push(payload)
        localStorage.setItem('linuxlogos_offline_sales', JSON.stringify(queue))
        setOfflineCount(queue.length)
        setMessage(`Connexion interrompue : Vente mise en attente de synchronisation (${queue.length} hors-ligne).`)
        setCart([])
        setAppliedCoupon(null)
        setCouponCode('')
      } else {
        setMessage(e.message)
      }
    }
  }

  return (
    <div className="pos-workspace">
      <div className="pos-grid">
        <Panel title="Saisie rapide & Recherche Produit">
          <div className="search large"><Search size={17} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Scanner ou rechercher (Code-barres, Nom, Référence)..." /></div>
          <div className="product-grid">
            {shown.map(product => (
              <button className="product-tile" key={product.id} onClick={() => add(product)}>
                <span className="product-tag">Réf: {product.reference || 'N/A'}</span>
                <b>{product.nom}</b>
                <small>Stock dispo: {product.stock}</small>
                <strong>{money(product.prix_vente)}</strong>
              </button>
            ))}
            {!shown.length && <Empty text="Aucun article correspondant en stock" />}
          </div>
        </Panel>

        <Panel title={`Panier Commercial · ${cart.reduce((s, x) => s + x.qty, 0)} article(s)`}>
          <div className="cart">
            {cart.map(item => (
              <div className="cart-row" key={item.id}>
                <div><b>{item.nom}</b><span>{money(item.prix_vente)} x {item.qty}</span></div>
                <div className="stepper">
                  <button onClick={() => setCart(c => c.map(x => x.id === item.id ? { ...x, qty: x.qty - 1 } : x).filter(x => x.qty > 0))}>-</button>
                  <b>{item.qty}</b>
                  <button onClick={() => add(item as Product)}>+</button>
                </div>
              </div>
            ))}
            {!cart.length && <Empty text="Aucun article sélectionné" />}

            <div className="form-grid" style={{ marginTop: '1rem' }}>
              <label>Client & Fidélité
                <select value={customerId} onChange={e => setCustomerId(e.target.value)}>
                  {customers.map(c => (
                    <option key={c.id} value={c.id}>{c.nom} {c.prenom} (Points: {c.points_fidelite || 0})</option>
                  ))}
                </select>
              </label>

              <label>Coupon Réduction
                <div style={{ display: 'flex', gap: '.4rem' }}>
                  <input placeholder="Code coupon (ex: PROMO10)" value={couponCode} onChange={e => setCouponCode(e.target.value)} />
                  <button className="secondary" type="button" onClick={applyCoupon}>Appliquer</button>
                </div>
              </label>
            </div>

            <div className="cart-total">
              <span>Total TTC</span>
              <strong>{money(total)}</strong>
            </div>

            {offlineCount > 0 && (
              <div className="notice" style={{ background: '#fef3c7', color: '#92400e', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{offlineCount} vente(s) enregistrée(s) hors-ligne</span>
                <button className="secondary" style={{ fontSize: '.75rem', padding: '.2rem .5rem' }} onClick={syncOfflineSales}>Synchroniser</button>
              </div>
            )}

            <div style={{ display: 'grid', gap: '.5rem' }}>
              <button className="primary wide" onClick={() => validateOrder(false)}>Valider la vente (Transmettre au Caissier)</button>
              <button className="secondary wide" style={{ border: '1px solid var(--border)' }} onClick={() => validateOrder(true)}>Générer Proforma / Devis Privé</button>
            </div>

            {message && <div className="notice">{message}</div>}
          </div>
        </Panel>
      </div>
    </div>
  )
}

function ImportExcel({ user }: { user: User }) {
  const [content, setContent] = useState('reference,quantite,prix\nPRD-TEST,2,250')
  const [isProforma, setIsProforma] = useState(false)
  const [message, setMessage] = useState('')

  async function submitImport() {
    try {
      const res = await request('/sales/import-excel/', {
        method: 'POST',
        body: JSON.stringify({ content, proforma: isProforma })
      }, user)
      setMessage(`Import réussi : Commande ${res.reference} (${res.statut}) de ${money(res.total)} créée.`)
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <Panel title="Importation en bloc de commandes (Excel / CSV)">
      <div style={{ padding: '1rem', display: 'grid', gap: '1rem' }}>
        <p className="muted">Collez ci-dessous le contenu du fichier Excel/CSV transmis par le client (Colonnes : reference/nom, quantite, prix) :</p>
        <textarea rows={8} style={{ width: '100%', padding: '.8rem', fontFamily: 'monospace', borderRadius: '8px', border: '1px solid var(--border)' }} value={content} onChange={e => setContent(e.target.value)} />
        <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
          <input type="checkbox" checked={isProforma} onChange={e => setIsProforma(e.target.checked)} style={{ width: 'auto' }} />
          Importer sous forme de Devis / Proforma (non transmis directement au caissier)
        </label>
        <button className="primary" onClick={submitImport}>Lancer l'importation de la commande</button>
        {message && <div className="notice">{message}</div>}
      </div>
    </Panel>
  )
}

function Proformas({ user }: { user: User }) {
  const [proformas, setProformas] = useState<Entity[]>([])
  const [message, setMessage] = useState('')

  async function load() {
    const list = await request('/sales/', {}, user)
    setProformas(list.filter((x: Entity) => x.statut === 'PROFORMA'))
  }

  useEffect(() => { load() }, [user])

  async function convert(p: Entity) {
    try {
      await request(`/proformas/${p.id}/convert/`, { method: 'POST' }, user)
      setMessage(`Proforma ${p.reference} convertie avec succès en vente validée pour le Caissier.`)
      load()
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <Panel title="Devis & Factures Pro Forma Privés">
      <div className="list">
        {proformas.map(p => (
          <div className="list-row" key={p.id}>
            <div><b>{p.reference}</b><span>Créé le {dateLabel(p.date)} - {money(p.total_ttc)}</span></div>
            <button className="primary" onClick={() => convert(p)}>Convertir en vente validée</button>
          </div>
        ))}
        {!proformas.length && <Empty text="Aucune proforma / devis en attente" />}
        {message && <div className="notice">{message}</div>}
      </div>
    </Panel>
  )
}

function CaisseSessionPage({ user }: { user: User }) {
  const [session, setSession] = useState<Entity | null>(null)
  const [floatAmount, setFloatAmount] = useState('50000')
  const [finalCash, setFinalCash] = useState('50000')
  const [notes, setNotes] = useState('')
  const [message, setMessage] = useState('')

  async function load() {
    const active = await request('/caisse/session/', {}, user)
    setSession(active)
  }

  useEffect(() => { load() }, [user])

  async function openSession() {
    try {
      const s = await request('/caisse/session/', { method: 'POST', body: JSON.stringify({ action: 'OPEN', fond_de_caisse_initial: floatAmount }) }, user)
      setSession(s)
      setMessage('Session de caisse ouverte avec succès.')
    } catch (err) { setMessage((err as Error).message) }
  }

  async function closeSession() {
    try {
      const s = await request('/caisse/session/', { method: 'POST', body: JSON.stringify({ action: 'CLOSE', montant_final_especes: finalCash, notes }) }, user)
      setSession(null)
      setMessage(`Session de caisse fermée. Écart de caisse : ${money(s.ecart)}`)
    } catch (err) { setMessage((err as Error).message) }
  }

  return (
    <Panel title="Gestion du Tiroir Caisse & Sessions Quotidiennes">
      <div style={{ padding: '1rem', display: 'grid', gap: '1rem' }}>
        {session ? (
          <div className="form-grid">
            <div className="notice"><b>Session Caisse Ouverte</b> - Fond initial : {money(session.fond_de_caisse_initial)} (Ouverte le {new Date(session.date_ouverture).toLocaleString('fr-FR')})</div>
            <label>Montant final compté en espèces dans le tiroir caisse
              <input type="number" value={finalCash} onChange={e => setFinalCash(e.target.value)} />
            </label>
            <label>Notes / Justification des écarts
              <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="Facultatif..." />
            </label>
            <button className="primary" onClick={closeSession}>Clôturer la session de caisse</button>
          </div>
        ) : (
          <div className="form-grid">
            <p className="muted">Aucune session de caisse ouverte. Veuillez initialiser le fond de caisse avant encaissement :</p>
            <label>Fond de caisse initial (FCFA)
              <input type="number" value={floatAmount} onChange={e => setFloatAmount(e.target.value)} />
            </label>
            <button className="primary" onClick={openSession}>Ouvrir la session de caisse</button>
          </div>
        )}
        {message && <div className="notice">{message}</div>}
      </div>
    </Panel>
  )
}

function CashierPending({ user }: { user: User }) {
  const [pending, setPending] = useState<Entity[]>([])
  const [selectedSale, setSelectedSale] = useState<Entity | null>(null)
  const [paymentMode, setPaymentMode] = useState('ESPECES')
  const [receivedAmount, setReceivedAmount] = useState('')
  const [message, setMessage] = useState('')

  async function load() {
    const list = await request('/cashier/pending/', {}, user)
    setPending(list)
  }

  useEffect(() => { load() }, [user])

  function openPaymentModal(sale: Entity) {
    setSelectedSale(sale)
    setReceivedAmount(String(sale.total_ttc))
  }

  async function processPayment() {
    if (!selectedSale) return
    try {
      const res = await request(`/payments/${selectedSale.id}/`, {
        method: 'POST',
        body: JSON.stringify({ paiements: [{ montant: receivedAmount, mode: paymentMode }] })
      }, user)

      setMessage(`Paiement enregistré pour ${selectedSale.reference}. Monnaie à rendre : ${money(res.monnaie_rendue)}`)
      printProvisionalReceipt(selectedSale, Number(receivedAmount), res.monnaie_rendue, paymentMode)
      setSelectedSale(null)
      load()
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  function printProvisionalReceipt(sale: Entity, recu: number, monnaie: number, mode: string) {
    const popup = window.open('', '_blank', 'width=720,height=720')
    if (!popup) return
    popup.document.write(`
      <html><head><title>Facture Provisoire - ${sale.reference}</title>
      <style>body{font-family:Arial,sans-serif;padding:32px;color:#111}h1{margin-bottom:4px}.status{margin-top:24px;padding:16px;background:#fff3cd;border:1px solid #ffeeba;font-size:18px;font-weight:bold;text-align:center}</style>
      </head><body>
      <h1>LinuxLogos POS</h1>
      <p><b>FACTURE PROVISOIRE</b></p>
      <p>Référence : ${sale.reference}</p>
      <p>Date : ${new Date().toLocaleDateString('fr-FR')}</p>
      <p>Total TTC : ${money(sale.total_ttc)}</p>
      <p>Montant reçu : ${money(recu)}</p>
      <p>Monnaie rendue : ${money(monnaie)}</p>
      <p>Mode de paiement : ${mode}</p>
      <div class="status">Statut : PAYÉ – NON LIVRÉ</div>
      <p style="margin-top:32px;font-size:12px;color:#666">À présenter au magasinier pour retrait du matériel.</p>
      <script>window.print()</script>
      </body></html>
    `)
    popup.document.close()
  }

  return (
    <>
      <Panel title="Commandes Validées en Attente d'Encaissement">
        <div className="list">
          {pending.map(sale => (
            <div className="list-row" key={sale.id}>
              <div><b>{sale.reference}</b><span>Du {dateLabel(sale.date)} - Total : {money(sale.total_ttc)}</span></div>
              <button className="primary" onClick={() => openPaymentModal(sale)}>Encaisser</button>
            </div>
          ))}
          {!pending.length && <Empty text="Aucune vente en attente d'encaissement" />}
        </div>
      </Panel>

      {selectedSale && (
        <Modal title={`Encaissement ${selectedSale.reference}`} onClose={() => setSelectedSale(null)}>
          <div className="form-grid">
            <div><b>Total à payer :</b> {money(selectedSale.total_ttc)}</div>
            <label>Mode de paiement
              <select value={paymentMode} onChange={e => setPaymentMode(e.target.value)}>
                <option value="ESPECES">Espèces</option>
                <option value="CARTE">Carte bancaire</option>
                <option value="MOBILE">Mobile money</option>
                <option value="SANS_CONTACT">Sans contact</option>
              </select>
            </label>
            <label>Montant donné par le client (FCFA)
              <input type="number" value={receivedAmount} onChange={e => setReceivedAmount(e.target.value)} />
            </label>
            {Number(receivedAmount) >= selectedSale.total_ttc && (
              <div className="notice" style={{ background: '#e0f2fe', color: '#0369a1' }}>
                Monnaie à rendre : <b>{money(Number(receivedAmount) - selectedSale.total_ttc)}</b>
              </div>
            )}
            <button className="primary wide" onClick={processPayment}>Valider le paiement & Imprimer ticket "Payé - non livré"</button>
          </div>
        </Modal>
      )}

      {message && <div className="notice" style={{ marginTop: '1rem' }}>{message}</div>}
    </>
  )
}

function Deliveries({ user }: { user: User }) {
  const [deliveries, setDeliveries] = useState<Entity[]>([])
  const [message, setMessage] = useState('')

  async function load() {
    const list = await request('/deliveries/', {}, user)
    setDeliveries(list)
  }

  useEffect(() => { load() }, [user])

  async function confirmDelivery(sale: Entity) {
    try {
      await request(`/deliveries/${sale.id}/confirm/`, { method: 'POST' }, user)
      setMessage(`Livraison de ${sale.reference} confirmée. Stock déduit du magasin. Facture finale imprimée.`)
      printFinalInvoice(sale)
      load()
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  function printFinalInvoice(sale: Entity) {
    const popup = window.open('', '_blank', 'width=720,height=720')
    if (!popup) return
    popup.document.write(`
      <html><head><title>Facture Finale - ${sale.reference}</title>
      <style>body{font-family:Arial,sans-serif;padding:32px;color:#111}h1{margin-bottom:4px}.status{margin-top:24px;padding:16px;background:#d4edda;border:1px solid #c3e6cb;font-size:18px;font-weight:bold;text-align:center}</style>
      </head><body>
      <h1>LinuxLogos WMS</h1>
      <p><b>FACTURE FINALE / BON DE LIVRAISON DEFINITIF</b></p>
      <p>Référence : ${sale.reference}</p>
      <p>Date de livraison : ${new Date().toLocaleDateString('fr-FR')}</p>
      <p>Montant Total TTC : ${money(sale.total_ttc)}</p>
      <div class="status">Statut : LIVRÉ ET CLÔTURÉ</div>
      <script>window.print()</script>
      </body></html>
    `)
    popup.document.close()
  }

  return (
    <Panel title="File des Commandes Payées en Attente de Livraison Magasinier">
      <div className="list">
        {deliveries.map(sale => (
          <div className="list-row" key={sale.id}>
            <div>
              <b>{sale.reference}</b>
              <span>Payé le {dateLabel(sale.date)} - {money(sale.total_ttc)}</span>
            </div>
            <button className="primary" onClick={() => confirmDelivery(sale)}>
              <CheckCircle2 size={16} /> Confirmer la livraison & Imprimer facture finale
            </button>
          </div>
        ))}
        {!deliveries.length && <Empty text="Aucune livraison en attente pour ce magasin" />}
        {message && <div className="notice">{message}</div>}
      </div>
    </Panel>
  )
}

function Transfers({ user }: { user: User }) {
  const [transfers, setTransfers] = useState<Entity[]>([])
  const [stores, setStores] = useState<Entity[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ magasin_source_id: '', magasin_dest_id: '', produit_id: '', quantite: '1' })

  async function load() {
    const [tr, st, pr] = await Promise.all([request('/transfers/', {}, user), request('/magasins/', {}, user), request('/products/')])
    setTransfers(tr)
    setStores(st)
    setProducts(pr)
    if (st.length >= 2) setForm(f => ({ ...f, magasin_source_id: st[0].id, magasin_dest_id: st[1].id }))
    if (pr.length) setForm(f => ({ ...f, produit_id: pr[0].id }))
  }

  useEffect(() => { load() }, [user])

  async function submitTransfer(e: FormEvent) {
    e.preventDefault()
    await request('/transfers/', { method: 'POST', body: JSON.stringify(form) }, user)
    setOpen(false)
    load()
  }

  return (
    <>
      <Toolbar label={`${transfers.length} transfert(s) inter-magasins`} onClick={() => setOpen(true)} />
      <Panel title="Historique des Transferts de Stock inter-dépôts">
        <Table
          headers={['Référence', 'Produit', 'Qté', 'Source', 'Destination', 'Date']}
          rows={transfers.map(t => [
            <b>{t.reference}</b>,
            t.produit_id,
            t.quantite,
            t.magasin_source_id,
            t.magasin_dest_id,
            dateLabel(t.created_at)
          ])}
        />
      </Panel>

      {open && (
        <Modal title="Nouveau Transfert de Stock Inter-Magasins" onClose={() => setOpen(false)}>
          <form onSubmit={submitTransfer} className="form-grid">
            <label>Magasin Source
              <select value={form.magasin_source_id} onChange={e => setForm({ ...form, magasin_source_id: e.target.value })}>
                {stores.map(s => <option key={s.id} value={s.id}>{s.nom}</option>)}
              </select>
            </label>
            <label>Magasin Destination
              <select value={form.magasin_dest_id} onChange={e => setForm({ ...form, magasin_dest_id: e.target.value })}>
                {stores.map(s => <option key={s.id} value={s.id}>{s.nom}</option>)}
              </select>
            </label>
            <label>Produit à transférer
              <select value={form.produit_id} onChange={e => setForm({ ...form, produit_id: e.target.value })}>
                {products.map(p => <option key={p.id} value={p.id}>{p.nom} (Stock total: {p.stock})</option>)}
              </select>
            </label>
            <label>Quantité
              <input type="number" min="1" value={form.quantite} onChange={e => setForm({ ...form, quantite: e.target.value })} />
            </label>
            <button className="primary wide">Valider le transfert</button>
          </form>
        </Modal>
      )}
    </>
  )
}

function ServiceContracts({ user }: { user: User }) {
  const [contracts, setContracts] = useState<Entity[]>([])
  const [customers, setCustomers] = useState<Entity[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ client_id: '', titre: '', type_service: 'DEPLOIEMENT', montant: '100000', description: '' })

  async function load() {
    const [c, cust] = await Promise.all([request('/service-contracts/', {}, user), request('/customers/', {}, user)])
    setContracts(c)
    setCustomers(cust)
    if (cust.length) setForm(f => ({ ...f, client_id: cust[0].id }))
  }

  useEffect(() => { load() }, [user])

  async function saveContract(e: FormEvent) {
    e.preventDefault()
    await request('/service-contracts/', { method: 'POST', body: JSON.stringify(form) }, user)
    setOpen(false)
    load()
  }

  return (
    <>
      <Toolbar label={`${contracts.length} contrat(s) de services IT (CRM)`} onClick={() => setOpen(true)} />
      <Panel title="Module CRM & Contrats de Services Informatiques">
        <Table
          headers={['Référence', 'Titre', 'Type', 'Montant', 'Statut']}
          rows={contracts.map(c => [
            <b>{c.reference}</b>,
            c.titre,
            <Badge>{c.type_service}</Badge>,
            money(c.montant),
            c.statut
          ])}
        />
      </Panel>

      {open && (
        <Modal title="Nouveau Contrat de Service IT" onClose={() => setOpen(false)}>
          <form onSubmit={saveContract} className="form-grid">
            <label>Client
              <select value={form.client_id} onChange={e => setForm({ ...form, client_id: e.target.value })}>
                {customers.map(c => <option key={c.id} value={c.id}>{c.nom} {c.prenom}</option>)}
              </select>
            </label>
            <label>Titre du contrat / Projet
              <input value={form.titre} onChange={e => setForm({ ...form, titre: e.target.value })} required />
            </label>
            <label>Type de service
              <select value={form.type_service} onChange={e => setForm({ ...form, type_service: e.target.value })}>
                <option value="DEPLOIEMENT">Déploiement Logiciel</option>
                <option value="RESEAU">Installation Réseau</option>
                <option value="SECURITE">Sécurité & Audit</option>
                <option value="MAINTENANCE">Maintenance IT</option>
              </select>
            </label>
            <label>Montant du contrat (FCFA)
              <input type="number" value={form.montant} onChange={e => setForm({ ...form, montant: e.target.value })} />
            </label>
            <label>Description / Détails
              <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            </label>
            <button className="primary wide">Créer le contrat</button>
          </form>
        </Modal>
      )}
    </>
  )
}

function CustomersPage({ user }: { user: User }) {
  return <CrudPage title="Clients & Points de Fidélité" endpoint="customers" fields={['nom', 'prenom', 'telephone', 'email']} user={user} />
}

function ReturnsPage({ user }: { user: User }) {
  return <CrudPage title="Retours produits & Avoirs" endpoint="returns" fields={['vente_id', 'produit_id', 'quantite', 'motif', 'gravite']} user={user} />
}

function Products({ user }: { user: User }) {
  const [items, setItems] = useState<Product[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ nom: '', prix_achat: '', prix_vente: '', seuil_min: '5', type_tracabilite: 'LOT' })

  async function load() { setItems(await request('/products/')) }
  useEffect(() => { load() }, [])

  async function save(e: FormEvent) {
    e.preventDefault()
    await request('/products/', { method: 'POST', body: JSON.stringify(form) }, user)
    setOpen(false)
    load()
  }

  return (
    <>
      <Toolbar label={`${items.length} produit(s)`} onClick={() => setOpen(true)} />
      <Panel title="Catalogue Produits Multi-Magasins">
        <Table
          headers={['Produit', 'Traçabilité', 'Prix Vente', 'Stock Central', 'Statut']}
          rows={items.map(p => [
            <b>{p.nom}</b>,
            <Badge>{p.type_tracabilite}</Badge>,
            money(p.prix_vente),
            <strong className={p.stock <= p.seuil_min ? 'danger-text' : ''}>{p.stock}</strong>,
            p.statut
          ])}
        />
      </Panel>
      {open && (
        <Modal title="Nouveau produit" onClose={() => setOpen(false)}>
          <form onSubmit={save} className="form-grid">
            {[
              ['nom', 'Nom du produit'],
              ['prix_achat', 'Prix d\'achat'],
              ['prix_vente', 'Prix de vente'],
              ['seuil_min', 'Seuil minimum d\'alerte']
            ].map(([key, label]) => (
              <label key={key}>{label}
                <input value={(form as any)[key]} type={key === 'nom' ? 'text' : 'number'} onChange={e => setForm({ ...form, [key]: e.target.value })} required />
              </label>
            ))}
            <label>Mode Traçabilité
              <select value={form.type_tracabilite} onChange={e => setForm({ ...form, type_tracabilite: e.target.value })}>
                <option>LOT</option>
                <option>SERIE</option>
              </select>
            </label>
            <button className="primary wide">Créer</button>
          </form>
        </Modal>
      )}
    </>
  )
}

function Stock({}: { user: User }) {
  const [products, setProducts] = useState<Product[]>([])
  useEffect(() => { request('/products/').then(setProducts) }, [])

  return (
    <>
      <div className="metric-grid">
        <Metric label="Produits" value={String(products.length)} note="Catalogue actif" />
        <Metric label="Alertes" value={String(products.filter(p => p.stock <= p.seuil_min).length)} note="À surveiller" />
        <Metric label="Ruptures" value={String(products.filter(p => p.stock === 0).length)} note="Stock nul" />
        <Metric label="Magasins" value="2" note="Magasin 1 & 2" />
      </div>
      <Panel title="État Réel des Stocks Centralisés">
        <Table
          headers={['Produit', 'Type', 'Stock Restant', 'Seuil Alerte', 'État']}
          rows={products.map(p => [
            <b>{p.nom}</b>,
            p.type_tracabilite,
            p.stock,
            p.seuil_min,
            <Badge danger={p.stock === 0}>{p.stock === 0 ? 'RUPTURE' : p.stock <= p.seuil_min ? 'FAIBLE' : 'OK'}</Badge>
          ])}
        />
      </Panel>
    </>
  )
}

function CrudPage({ title, endpoint, fields, user }: { title: string; endpoint: string; fields: string[]; user: User }) {
  const [items, setItems] = useState<Entity[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<Entity>({})

  async function load() { setItems(await request(`/${endpoint}/`, {}, user)) }
  useEffect(() => { load() }, [endpoint])

  async function save(e: FormEvent) {
    e.preventDefault()
    await request(`/${endpoint}/`, { method: 'POST', body: JSON.stringify(form) }, user)
    setOpen(false)
    setForm({})
    load()
  }

  return (
    <>
      <Toolbar label={`${items.length} enregistrement(s)`} onClick={() => setOpen(true)} />
      <Panel title={title}>
        <div className="entity-grid">
          {items.map(item => (
            <div className="entity" key={item.id}>
              <div className="avatar">{(item.nom || item.produit_nom || item.categorie || '?')[0]}</div>
              <div>
                <b>{item.nom || item.produit_nom || item.categorie || item.reference}</b>
                <span>{item.telephone || item.date || item.motif || `${item.montant || ''} FCFA`}</span>
              </div>
              <ChevronDown size={16} />
            </div>
          ))}
          {!items.length && <Empty text={`Aucun enregistrement`} />}
        </div>
      </Panel>
      {open && (
        <Modal title={`Ajouter ${title.slice(0, -1).toLowerCase()}`} onClose={() => setOpen(false)}>
          <form onSubmit={save} className="form-grid">
            {fields.map(field => (
              <label key={field}>{field.replace('_', ' ')}
                <input type={field === 'montant' || field === 'quantite' ? 'number' : 'text'} value={form[field] || ''} onChange={e => setForm({ ...form, [field]: e.target.value })} required={['nom', 'montant', 'categorie'].includes(field)} />
              </label>
            ))}
            <button className="primary wide">Enregistrer</button>
          </form>
        </Modal>
      )}
    </>
  )
}

function Purchases({ user }: { user: User }) {
  const [items, setItems] = useState<Entity[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [suppliers, setSuppliers] = useState<Entity[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ fournisseur_id: '', produit_id: '', quantite: '1', prix_unitaire: '' })

  useEffect(() => {
    Promise.all([request('/purchases/', {}, user), request('/products/'), request('/suppliers/', {}, user)]).then(([p, pr, s]) => {
      setItems(p)
      setProducts(pr)
      setSuppliers(s)
    })
  }, [user])

  async function save(e: FormEvent) {
    e.preventDefault()
    await request('/purchases/', {
      method: 'POST',
      body: JSON.stringify({
        fournisseur_id: form.fournisseur_id || suppliers[0]?.id,
        lignes: [{ produit_id: form.produit_id || products[0]?.id, quantite: form.quantite, prix_unitaire: form.prix_unitaire || products[0]?.prix_achat }]
      })
    }, user)
    setOpen(false)
    setItems(await request('/purchases/', {}, user))
  }

  return (
    <>
      <Toolbar label={`${items.length} achat(s)`} onClick={() => setOpen(true)} />
      <Panel title="Historique des Achats & Approvisionnements">
        <Table
          headers={['Référence', 'Fournisseur', 'Date', 'Coût total']}
          rows={items.map(p => [<b>{p.reference}</b>, p.fournisseur_id, dateLabel(p.date), <strong>{money(p.cout_total)}</strong>])}
        />
      </Panel>
      {open && (
        <Modal title="Nouvel Achat / Réapprovisionnement" onClose={() => setOpen(false)}>
          <form onSubmit={save} className="form-grid">
            <label>Fournisseur
              <select value={form.fournisseur_id} onChange={e => setForm({ ...form, fournisseur_id: e.target.value })}>
                {suppliers.map(s => <option key={s.id} value={s.id}>{s.nom}</option>)}
              </select>
            </label>
            <label>Produit
              <select value={form.produit_id} onChange={e => setForm({ ...form, produit_id: e.target.value })}>
                {products.map(p => <option key={p.id} value={p.id}>{p.nom}</option>)}
              </select>
            </label>
            <label>Quantité
              <input type="number" min="1" value={form.quantite} onChange={e => setForm({ ...form, quantite: e.target.value })} />
            </label>
            <label>Prix unitaire
              <input type="number" value={form.prix_unitaire} onChange={e => setForm({ ...form, prix_unitaire: e.target.value })} />
            </label>
            <button className="primary wide">Enregistrer</button>
          </form>
        </Modal>
      )}
    </>
  )
}

function Treasury({ user }: { user: User }) {
  const [data, setData] = useState<any>({})
  useEffect(() => { request('/treasury/', {}, user).then(setData) }, [user])
  return (
    <>
      <div className="treasury-hero">
        <span>Solde Actuel Disponible</span>
        <strong>{money(data.balance)}</strong>
      </div>
      <Panel title="Mouvements de Caisse & Trésorerie">
        <Table
          headers={['Type', 'Référence', 'Date', 'Entrée', 'Sortie']}
          rows={(data.movements || []).map((m: Entity) => [
            <Badge>{m.type}</Badge>,
            m.reference,
            dateLabel(m.date),
            m.montant_entree ? money(m.montant_entree) : '-',
            m.montant_sortie ? money(m.montant_sortie) : '-'
          ])}
        />
      </Panel>
    </>
  )
}

function Reports({ user }: { user: User }) {
  const [magasins, setMagasins] = useState<Entity[]>([])
  const [data, setData] = useState<any>(null)
  const [magasinId, setMagasinId] = useState('')
  const [commercialId, setCommercialId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  async function loadReports() {
    const params = new URLSearchParams()
    if (magasinId) params.append('magasin_id', magasinId)
    if (commercialId) params.append('commercial_id', commercialId)
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)

    const query = params.toString() ? `?${params.toString()}` : ''
    const res = await request(`/analytics/${query}`, {}, user)
    setData(res)
  }

  useEffect(() => {
    request('/magasins/', {}, user).then(setMagasins).catch(() => {})
    loadReports()
  }, [user])

  function filterReports(e: FormEvent) {
    e.preventDefault()
    loadReports()
  }

  return (
    <>
      <Panel title="Filtres des Rapports de Ventes">
        <form onSubmit={filterReports} className="form-grid" style={{ padding: '1rem' }}>
          <label>Magasin
            <select value={magasinId} onChange={e => setMagasinId(e.target.value)}>
              <option value="">Tous les magasins</option>
              {magasins.map(m => <option key={m.id} value={m.id}>{m.nom}</option>)}
            </select>
          </label>
          <label>Commercial / Vendeur (ID)
            <input value={commercialId} onChange={e => setCommercialId(e.target.value)} placeholder="Tous les commerciaux..." />
          </label>
          <label>Date Début
            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
          </label>
          <label>Date Fin
            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
          </label>
          <button className="primary" style={{ gridColumn: '1 / -1' }}>Générer le rapport</button>
        </form>
      </Panel>

      <div className="metric-grid" style={{ marginTop: '1rem' }}>
        <Metric label="Chiffre d'Affaires" value={money(data?.ca)} note="Total ventes filtrées" accent />
        <Metric label="Nombre de Ventes" value={String(data?.nbVentes || 0)} note="Transactions" />
      </div>

      <div className="two-columns" style={{ marginTop: '1rem' }}>
        <Panel title="Ventes par Jour">
          <Table
            headers={['Date', 'Nombre de ventes', 'Chiffre d\'Affaires']}
            rows={(data?.salesByDay || []).map((row: any) => [
              dateLabel(row.date),
              row.nb_ventes,
              money(row.ca)
            ])}
          />
        </Panel>

        <Panel title="Détail des Articles Vendus">
          <Table
            headers={['Article / Produit', 'Quantité Vendue', 'Montant Total TTC']}
            rows={(data?.articlesVendus || []).map((row: any) => [
              <b>{row.nom}</b>,
              row.quantite,
              money(row.total)
            ])}
          />
        </Panel>
      </div>
    </>
  )
}

function Accounting({ user }: { user: User }) {
  const [data, setData] = useState<any>()
  useEffect(() => { request('/accounting/', {}, user).then(setData) }, [user])
  return (
    <>
      <div className="metric-grid accounting">
        {[
          ['CA Total', data?.financial?.ca],
          ['COGS', data?.financial?.cogs],
          ['Achats', data?.financial?.achats],
          ['Dépenses', data?.financial?.depenses],
          ['Marge brute', data?.financial?.margeBrute],
          ['Résultat', data?.financial?.resultat],
          ['Valeur Stock', data?.financial?.valeurStock]
        ].map(([label, value]) => (
          <Metric key={String(label)} label={String(label)} value={money(Number(value))} note="Aperçu financier" />
        ))}
      </div>
      <Panel title="Rentabilité détaillée des Ventes">
        <Table
          headers={['Vente', 'Source', 'Qté', 'CA net', 'Coût réel', 'Marge', 'Taux']}
          rows={(data?.sales || []).map((sale: Entity) => [
            sale.vente_id,
            sale.source_id || sale.lot_id || sale.unite_id || '-',
            sale.quantite,
            money(sale.montant_vente_net),
            money(sale.cout_total),
            money(sale.marge_brute),
            `${Number(sale.taux_marge || 0).toFixed(1)} %`
          ])}
        />
      </Panel>
    </>
  )
}

function SimplePanel({ title, text }: { title: string; text: string }) {
  return <Panel title={title}><div className="empty large">{text}</div></Panel>
}

function Toolbar({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <div className="toolbar">
      <span>{label}</span>
      <button className="primary" onClick={onClick}><Plus size={16} /> Ajouter</button>
    </div>
  )
}

function Table({ headers, rows }: { headers: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{headers.map(h => <th key={h}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <Empty text="Aucune donnée enregistrée" />}
    </div>
  )
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-heading">
          <h2>{title}</h2>
          <button className="icon-button" onClick={onClose}><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default App