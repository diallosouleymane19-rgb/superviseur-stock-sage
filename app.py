import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from utils.sage_connector import (
    get_stock_temps_reel,
    get_commandes_demo,
    get_mouvements_demo
)
from utils.export_commande import export_commande_excel 
analyser_alertes_stock,
    generer_commande_portugal,
    consolider_besoins_supermarchés
)
from auth import login, logout, is_connecte, get_role

# ---------------------------------------------------------
# AUTHENTIFICATION
# ---------------------------------------------------------
if not is_connecte():
    login()
    st.stop()

role = st.session_state["role"]
nom = st.session_state["nom"]

# ---------------------------------------------------------
# STYLE GLOBAL
# ---------------------------------------------------------
st.markdown("""
<style>
body { font-family: 'Segoe UI', sans-serif; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ddd; padding: 8px; }
th { background-color: #1f77b4; color: white; font-weight: bold; }
tr:nth-child(even) { background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU LATÉRAL
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/warehouse.png", width=80)
st.sidebar.title("Superviseur Stock")
st.sidebar.markdown(f"👤 **{nom}**")
st.sidebar.markdown(f"🎭 **{role}**")
st.sidebar.markdown("---")
logout()

# Menu selon le rôle
if role == "Directeur":
    pages = [
        "🏠 Tableau de Bord",
        "📦 Stock Temps Réel",
        "🚨 Alertes Stock",
        "🛒 Commandes Supermarchés",
        "✈️ Commande Portugal",
        "📊 Rapports & Analytics",
    ]
elif role == "Gestionnaire Stock":
    pages = [
        "🏠 Tableau de Bord",
        "📦 Stock Temps Réel",
        "🚨 Alertes Stock",
        "🛒 Commandes Supermarchés",
        "✈️ Commande Portugal",
    ]
else:  # Gérant Supermarché
    pages = [
        "🏠 Tableau de Bord",
        "🛒 Mes Commandes",
        "📦 Stock Disponible",
    ]

page = st.sidebar.radio("Navigation", pages)

# Indicateur connexion Sage
st.sidebar.markdown("---")
st.sidebar.markdown("**🔌 Connexion Sage :**")
st.sidebar.warning("⚠️ Mode démonstration\n(Sage non connecté)")

# ---------------------------------------------------------
# CHARGEMENT DES DONNÉES
# ---------------------------------------------------------
@st.cache_data(ttl=300)  # Cache 5 minutes
def charger_donnees():
    df_stock = get_stock_temps_reel()
    df_commandes = get_commandes_demo()
    df_mouvements = get_mouvements_demo()
    return df_stock, df_commandes, df_mouvements

df_stock, df_commandes, df_mouvements = charger_donnees()
df_alertes = analyser_alertes_stock(df_stock, df_mouvements)

# ---------------------------------------------------------
# PAGE : TABLEAU DE BORD
# ---------------------------------------------------------
if page == "🏠 Tableau de Bord":
    st.title("🏠 Tableau de Bord — Stock & Approvisionnement")
    st.markdown("---")

    # KPIs
    total_references = len(df_stock)
    valeur_totale = df_stock["valeur_stock"].sum()
    ruptures = len(df_alertes[df_alertes["priorite"] == 1])
    critiques = len(df_alertes[df_alertes["priorite"] == 2])
    a_commander = len(df_alertes[df_alertes["priorite"] == 3])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📦 Références", total_references)
    col2.metric("💰 Valeur Stock", f"{valeur_totale:,.0f} XOF")
    col3.metric("🔴 Ruptures", ruptures, delta=f"-{ruptures}" if ruptures > 0 else "0")
    col4.metric("🟠 Critiques", critiques)
    col5.metric("🟡 À Commander", a_commander)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Répartition du stock par famille")
        df_famille = df_stock.groupby("famille")["valeur_stock"].sum().reset_index()
        fig1 = px.pie(df_famille, values="valeur_stock", names="famille",
                      color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("🚨 Statut des stocks")
        df_statut = df_alertes.groupby("statut").size().reset_index(name="count")
        fig2 = px.bar(df_statut, x="statut", y="count",
                      color="statut",
                      color_discrete_map={
                          "🔴 RUPTURE": "red",
                          "🟠 CRITIQUE": "orange",
                          "🟡 À COMMANDER": "yellow",
                          "🟢 OK": "green"
                      })
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("🚨 Alertes prioritaires")
    alertes_urgentes = df_alertes[df_alertes["priorite"] <= 2]
    if alertes_urgentes.empty:
        st.success("✅ Aucune alerte critique !")
    else:
        st.dataframe(alertes_urgentes[[
            "statut", "reference", "designation",
            "quantite_stock", "stock_minimum", "point_commande"
        ]], use_container_width=True)

# ---------------------------------------------------------
# PAGE : STOCK TEMPS RÉEL
# ---------------------------------------------------------
elif page == "📦 Stock Temps Réel":
    st.title("📦 Stock en Temps Réel")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total références", len(df_stock))
    col2.metric("Valeur totale", f"{df_stock['valeur_stock'].sum():,.0f} XOF")
    col3.metric("Quantité totale", f"{df_stock['quantite_stock'].sum():,.0f}")

    st.markdown("---")

    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        famille_filter = st.multiselect(
            "Filtrer par famille",
            options=df_stock["famille"].unique(),
            default=[]
        )
    with col2:
        search = st.text_input("Rechercher un produit")

    df_filtered = df_stock.copy()
    if famille_filter:
        df_filtered = df_filtered[df_filtered["famille"].isin(famille_filter)]
    if search:
        df_filtered = df_filtered[
            df_filtered["designation"].str.contains(search, case=False) |
            df_filtered["reference"].str.contains(search, case=False)
        ]

    st.dataframe(df_filtered[[
        "reference", "designation", "famille",
        "quantite_stock", "valeur_stock",
        "stock_minimum", "prix_achat", "prix_vente"
    ]], use_container_width=True)

# ---------------------------------------------------------
# PAGE : ALERTES STOCK
# ---------------------------------------------------------
elif page == "🚨 Alertes Stock":
    st.title("🚨 Alertes de Stock")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Ruptures", len(df_alertes[df_alertes["priorite"] == 1]))
    col2.metric("🟠 Critiques", len(df_alertes[df_alertes["priorite"] == 2]))
    col3.metric("🟡 À Commander", len(df_alertes[df_alertes["priorite"] == 3]))
    col4.metric("🟢 OK", len(df_alertes[df_alertes["priorite"] == 4]))

    st.markdown("---")

    filtre = st.selectbox("Filtrer par statut", [
        "Tous",
        "🔴 RUPTURE",
        "🟠 CRITIQUE",
        "🟡 À COMMANDER",
        "🟢 OK"
    ])

    df_affiche = df_alertes.copy()
    if filtre != "Tous":
        df_affiche = df_affiche[df_affiche["statut"] == filtre]

    st.dataframe(df_affiche[[
        "statut", "reference", "designation",
        "quantite_stock", "stock_minimum",
        "point_commande", "conso_hebdo", "qec"
    ]], use_container_width=True)

# ---------------------------------------------------------
# PAGE : COMMANDES SUPERMARCHÉS
# ---------------------------------------------------------
elif page == "🛒 Commandes Supermarchés":
    st.title("🛒 Commandes des Supermarchés")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total commandes", len(df_commandes))
    col2.metric("Montant total", f"{df_commandes['montant_ht'].sum():,.0f} XOF")
    col3.metric("Supermarchés actifs", df_commandes["code_client"].nunique())

    st.markdown("---")

    onglet1, onglet2 = st.tabs(["📋 Détail commandes", "📊 Consolidation"])

    with onglet1:
        supermarche_filter = st.multiselect(
            "Filtrer par supermarché",
            options=df_commandes["nom_supermarche"].unique(),
            default=[]
        )
        df_cmd_filtered = df_commandes.copy()
        if supermarche_filter:
            df_cmd_filtered = df_cmd_filtered[
                df_cmd_filtered["nom_supermarche"].isin(supermarche_filter)
            ]
        st.dataframe(df_cmd_filtered, use_container_width=True)

    with onglet2:
        st.subheader("📊 Besoins consolidés tous supermarchés")
        df_consolidé = consolider_besoins_supermarchés(df_commandes)
        st.dataframe(df_consolidé, use_container_width=True)

        fig = px.bar(df_consolidé.head(10),
                     x="designation", y="total_commande",
                     title="Top 10 produits les plus commandés",
                     color="montant_total",
                     color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# PAGE : COMMANDE PORTUGAL
# ---------------------------------------------------------
elif page == "✈️ Commande Portugal":
    st.title("✈️ Commande Fournisseur Portugal")
    st.markdown("---")

    st.info(f"""
    **Délai de livraison :** 3 à 4 semaines
    **Point de commande :** Stock couvrant 5 semaines de consommation
    **Stock de sécurité :** 1 semaine supplémentaire
    """)

    df_commande_portugal = generer_commande_portugal(df_alertes)

    if df_commande_portugal.empty:
        st.success("✅ Aucune commande urgente à passer au Portugal !")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Références à commander", len(df_commande_portugal))

        st.subheader("📋 Liste des produits à commander")
        st.dataframe(df_commande_portugal, use_container_width=True)

        buffer = export_commande_excel(
            df_commande_portugal,
            nom_societe="Entrepôt Central — Guinée-Bissau",
            pays_fournisseur="Portugal"
        )
        st.download_button(
            label="📥 Télécharger la commande en Excel",
            data=buffer,
            file_name=f"Commande_Portugal_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
       
        )

# ---------------------------------------------------------
# PAGE : MES COMMANDES (Gérant Supermarché)
# ---------------------------------------------------------
elif page == "🛒 Mes Commandes":
    st.title(f"🛒 Mes Commandes — {nom}")
    st.markdown("---")

    # Filtrer les commandes du supermarché connecté
    code_sm = st.session_state["username"].upper()
    mes_commandes = df_commandes[df_commandes["code_client"] == code_sm]

    if mes_commandes.empty:
        st.info("Aucune commande trouvée pour votre supermarché.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Mes commandes", len(mes_commandes))
        col2.metric("Montant total", f"{mes_commandes['montant_ht'].sum():,.0f} XOF")
        st.dataframe(mes_commandes, use_container_width=True)

# ---------------------------------------------------------
# PAGE : STOCK DISPONIBLE (Gérant Supermarché)
# ---------------------------------------------------------
elif page == "📦 Stock Disponible":
    st.title("📦 Stock Disponible à l'Entrepôt")
    st.markdown("---")

    st.dataframe(df_stock[[
        "reference", "designation", "famille",
        "quantite_stock", "prix_vente"
    ]], use_container_width=True)

# ---------------------------------------------------------
# PAGE : RAPPORTS & ANALYTICS (Directeur)
# ---------------------------------------------------------
elif page == "📊 Rapports & Analytics":
    st.title("📊 Rapports & Analytics")
    st.markdown("---")

    onglet1, onglet2, onglet3 = st.tabs([
        "📈 Évolution Stock",
        "🏪 Performance Supermarchés",
        "💰 Valeur Stock"
    ])

    with onglet1:
        st.subheader("📈 Top 10 produits par valeur de stock")
        df_top = df_stock.nlargest(10, "valeur_stock")
        fig = px.bar(df_top, x="designation", y="valeur_stock",
                     color="famille",
                     title="Top 10 produits par valeur de stock")
        st.plotly_chart(fig, use_container_width=True)

    with onglet2:
        st.subheader("🏪 Commandes par supermarché")
        df_sm = df_commandes.groupby("nom_supermarche").agg(
            total_commandes=("numero_commande", "count"),
            montant_total=("montant_ht", "sum")
        ).reset_index()
        fig = px.bar(df_sm, x="nom_supermarche", y="montant_total",
                     color="total_commandes",
                     title="Montant des commandes par supermarché")
        st.plotly_chart(fig, use_container_width=True)

    with onglet3:
        st.subheader("💰 Valeur du stock par famille")
        df_val = df_stock.groupby("famille")["valeur_stock"].sum().reset_index()
        fig = px.pie(df_val, values="valeur_stock", names="famille",
                     title="Répartition de la valeur du stock")
        st.plotly_chart(fig, use_container_width=True)
    
