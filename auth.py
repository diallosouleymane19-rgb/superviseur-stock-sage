import streamlit as st
import bcrypt

# Utilisateurs avec leurs rôles
UTILISATEURS = {
    "directeur": {
        "password": bcrypt.hashpw("direct2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Directeur",
        "nom": "Directeur Général"
    },
    "stock": {
        "password": bcrypt.hashpw("stock2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gestionnaire Stock",
        "nom": "Gestionnaire de Stock"
    },
    "sm001": {
        "password": bcrypt.hashpw("sm001_2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gérant Supermarché",
        "nom": "Supermarché Bissau Centre"
    },
    "sm002": {
        "password": bcrypt.hashpw("sm002_2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gérant Supermarché",
        "nom": "Supermarché Bairro Militar"
    },
    "sm003": {
        "password": bcrypt.hashpw("sm003_2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gérant Supermarché",
        "nom": "Supermarché Bandim"
    },
    "sm004": {
        "password": bcrypt.hashpw("sm004_2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gérant Supermarché",
        "nom": "Supermarché Bô Lama"
    },
    "sm005": {
        "password": bcrypt.hashpw("sm005_2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gérant Supermarché",
        "nom": "Supermarché Penha"
    },
    "sm006": {
        "password": bcrypt.hashpw("sm006_2026".encode(), bcrypt.gensalt()).decode(),
        "role": "Gérant Supermarché",
        "nom": "Supermarché Antula"
    },
}

def verifier_mot_de_passe(username, password):
    if username in UTILISATEURS:
        return bcrypt.checkpw(
            password.encode(),
            UTILISATEURS[username]["password"].encode()
        )
    return False

def get_role(username):
    return UTILISATEURS.get(username, {}).get("role", "")

def get_nom(username):
    return UTILISATEURS.get(username, {}).get("nom", "")

def login():
    st.title("📦 Superviseur Stock & Approvisionnement")
    st.markdown("### Connexion — Gestion Entrepôt")
    st.markdown("---")

    with st.form("login_form"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")

        if submit:
            if verifier_mot_de_passe(username, password):
                st.session_state["connecte"] = True
                st.session_state["username"] = username
                st.session_state["role"] = get_role(username)
                st.session_state["nom"] = get_nom(username)
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect.")

    st.markdown("---")
    st.markdown("**Identifiants de démonstration :**")
    st.info("""
    👔 Directeur : `directeur` / `direct2026`
    📦 Stock : `stock` / `stock2026`
    🏪 Supermarché 1 : `sm001` / `sm001_2026`
    """)

def logout():
    if st.sidebar.button("🚪 Se déconnecter"):
        st.session_state["connecte"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.session_state["nom"] = ""
        st.rerun()

def is_connecte():
    return st.session_state.get("connecte", False)