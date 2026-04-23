 
```

> **Terminal Pédagogique de Finance de Marché**  
> Salle des marchés interactive — Cours de Finance · 

---

## ⚡ Démarrage rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
streamlit run app.py

# 3. Ouvrir dans le navigateur
# → http://localhost:8501
```

| Rôle | Code d'accès | Accès |
|------|-------------|-------|
| Professeur / Admin | `ADMIN2026` | Interface Control Tower complète |
| Étudiant / Trader  | `BRVM2026`  | Interface Trading Floor |

---

## 🏗 Vue d'ensemble

BRVM·T simule une **salle des marchés pédagogique** en temps réel. Le professeur joue le rôle de Market Maker — il contrôle les prix, les paramètres de volatilité et diffuse des alertes. Les étudiants analysent, pricent et exécutent des ordres sur actions et options.

```
┌─────────────────────────────────────────────────────┐
│                  BRVM·T SESSION                      │
│                                                      │
│   PROFESSEUR                    ÉTUDIANTS (N)        │
│   ┌─────────────┐               ┌─────────────┐      │
│   │ Control     │  spot_price   │ Trading     │      │
│   │ Tower       │ ─────────────▶│ Floor       │      │
│   │             │  market_news  │             │      │
│   │ • Slider S  │ ─────────────▶│ • Payoff    │      │
│   │ • BS params │               │ • Orders    │      │
│   │ • Monitoring│◀─────────────│ • Portfolio │      │
│   └─────────────┘   positions  └─────────────┘      │
│                                                      │
│              [ st.session_state ]                    │
└─────────────────────────────────────────────────────┘
```

> ⚠️ **Important :** La synchronisation temps réel fonctionne uniquement en **réseau local** (salle de classe). Sur Streamlit Cloud, chaque utilisateur a une session isolée. Voir [Déploiement](#-déploiement) pour les détails.

---

## ✨ Fonctionnalités

### 🎛 Interface Professeur — Control Tower

| Onglet | Contenu |
|--------|---------|
| **Marché** | Slider prix sous-jacent · Import CSV · Paramètres Black-Scholes (K, σ, T, r) · Gel/dégel marché · Réinitialisation portefeuilles |
| **Monitoring** | P&L temps réel par étudiant · Bar chart comparatif · Carnet d'ordres global |
| **Communications** | Diffusion d'alertes marché typées (📢 Annonce · ⚠️ Alerte · 📈 Hausse · 📉 Baisse) |
| **Codes Admin** | Liste des codes actifs · Création de codes assistants illimitée |

### 📊 Interface Étudiant — Trading Floor

**Colonne Analyse**
- Graphique prix historiques avec zone colorée (Plotly)
- Courbe de Payoff interactive (Long/Short · Call/Put · Strike personnalisable)
- Point dynamique qui se déplace selon le prix fixé par le prof
- Indicateurs : prime BS · P&L actuel · point mort

**Colonne Exécution**
- Ordres sur 3 instruments : Action · Call · Put
- Prévisualisation du coût avant validation
- Tableau portefeuille : entrée · actuel · P&L par ligne
- Greeks de référence rapide (Δ · Γ · Vega · Theta)

---

## 📐 Moteur Black-Scholes

```
d1 = [ ln(S/K) + (r + σ²/2) × T ] / (σ√T)
d2 = d1 − σ√T

Call = S·N(d1) − K·e^(−rT)·N(d2)
Put  = K·e^(−rT)·N(−d2) − S·N(−d1)

Δ_call = N(d1)          Δ_put = N(d1) − 1
Γ      = N'(d1) / (S·σ·√T)
Vega   = S·N'(d1)·√T / 100
Θ      = −(S·N'(d1)·σ) / (2√T) − r·K·e^(−rT)·N(±d2)  /  365
```

Paramètres par défaut modifiables par le professeur :

| Paramètre | Défaut | Plage |
|-----------|--------|-------|
| S (spot) | 5 000 FCFA | 1 000 – 20 000 |
| K (strike) | 5 000 FCFA | 1 000 – 20 000 |
| σ (volatilité) | 20 % | 5 % – 100 % |
| T (maturité) | 0,25 an | 0,01 – 2 ans |
| r (taux) | 5 % | 0 % – 20 % |

---

## 🗂 Structure du projet

```
brvm-terminal/
├── app.py                  # Application complète (mono-fichier)
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier
```

### Architecture interne de `app.py`

```
app.py
├── black_scholes()         # Pricing + Greeks
├── payoff_curve()          # Calcul P&L sur plage de prix
├── chart_price_history()   # Graphique Plotly historique
├── chart_payoff()          # Courbe de Payoff dynamique
├── chart_admin_pnl()       # Bar chart P&L étudiants
├── compute_trader_pnl()    # P&L latent par trader
├── execute_order()         # Moteur d'exécution BUY/SELL
├── init_session_state()    # Initialisation état global
├── render_login()          # Écran d'authentification
├── render_admin()          # Interface professeur
├── render_trader()         # Interface étudiant
└── main()                  # Point d'entrée
```

---

## 📦 Dépendances

```txt
streamlit>=1.32.0
numpy>=1.26.0
pandas>=2.1.0
plotly>=5.18.0
scipy>=1.11.0
```

---

## 🚀 Déploiement

### ✅ Réseau local (recommandé pour les cours)

```bash
# Sur le PC du professeur (connecté au même réseau WiFi/LAN)
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# Les étudiants se connectent via :
# http://<IP-du-prof>:8501
# ex: http://192.168.1.42:8501
```

Pour trouver votre IP locale :
```bash
# Windows
ipconfig | findstr "IPv4"

# Mac / Linux
ip route get 1 | awk '{print $7}'
```

### ⚠️ Streamlit Cloud (démo solo uniquement)

```bash
# 1. Pousser sur GitHub
git init && git add . && git commit -m "init"
git remote add origin https://github.com/votre-user/brvm-terminal.git
git push origin main

# 2. Sur share.streamlit.io
# New app → sélectionner le repo → main → app.py → Deploy
```

> Sur Streamlit Cloud, chaque visiteur a sa propre session isolée. Idéal pour une démo individuelle, pas pour une session de cours collaborative.

---

## 🔮 Roadmap

```
v1 (actuel)  ──▶  Réseau local · Black-Scholes · Actions + Options
                  Monitoring Admin · Alertes · Multi-codes Admin

v2           ──▶  Firebase / Redis pour sync internet multi-users
                  Surface de volatilité 3D (Smile / Skew)
                  Mode examen avec timer

v3           ──▶  Stratégies multi-jambes (Straddle · Spread · Butterfly)
                  Export PDF de fin de session par étudiant
                  Historique des sessions sauvegardé
```

---

## 📄 Licence

Usage pédagogique libre. 

---

<div align="center">

**IUT·Terminal_Market** · Terminal Pédagogique de Finance de Marché

</div>
