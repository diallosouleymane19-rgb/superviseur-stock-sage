import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

def get_connection():
    """
    Connexion à la base de données Sage 100 SQL Server.
    """
    try:
        server = st.secrets.get("SAGE_SERVER", "localhost")
        database = st.secrets.get("SAGE_DATABASE", "GESCOM")
        username = st.secrets.get("SAGE_USERNAME", "sa")
        password = st.secrets.get("SAGE_PASSWORD", "")

        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        return None

def get_stock_temps_reel():
    """
    Récupère le stock en temps réel depuis Sage 100.
    """
    try:
        conn = get_connection()
        if not conn:
            return get_stock_demo()

        query = """
        SELECT
            A.AR_Ref AS reference,
            A.AR_Design AS designation,
            A.AR_PrixVen AS prix_vente,
            A.AR_PrixAch AS prix_achat,
            ISNULL(S.AS_QteSto, 0) AS quantite_stock,
            ISNULL(S.AS_QteSto * A.AR_PrixAch, 0) AS valeur_stock,
            A.AR_StkMin AS stock_minimum,
            A.AR_StkMax AS stock_maximum,
            F.FA_CodeFam AS famille
        FROM F_ARTICLE A
        LEFT JOIN F_ARTSTOCKEMPL S ON A.AR_Ref = S.AR_Ref
        LEFT JOIN F_FAMILLE F ON A.FA_CodeFam = F.FA_CodeFam
        WHERE A.AR_Sommeil = 0
        ORDER BY A.AR_Design
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return get_stock_demo()

def get_commandes_supermarchés():
    """
    Récupère les bons de commande des supermarchés depuis Sage 100.
    """
    try:
        conn = get_connection()
        if not conn:
            return get_commandes_demo()

        query = """
        SELECT
            E.DO_Piece AS numero_commande,
            E.DO_Date AS date_commande,
            E.CT_Num AS code_client,
            C.CT_Intitule AS nom_supermarche,
            L.AR_Ref AS reference,
            A.AR_Design AS designation,
            L.DL_Qty AS quantite_commandee,
            L.DL_PrixUnitaire AS prix_unitaire,
            L.DL_MontantHT AS montant_ht,
            E.DO_Statut AS statut
        FROM F_DOCENTETE E
        JOIN F_DOCLIGNES L ON E.DO_Piece = L.DO_Piece
        JOIN F_COMPTET C ON E.CT_Num = C.CT_Num
        JOIN F_ARTICLE A ON L.AR_Ref = A.AR_Ref
        WHERE E.DO_Type = 1
        AND E.DO_Date >= DATEADD(day, -30, GETDATE())
        ORDER BY E.DO_Date DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return get_commandes_demo()

def get_mouvements_stock(jours=30):
    """
    Récupère les mouvements de stock des derniers jours.
    """
    try:
        conn = get_connection()
        if not conn:
            return get_mouvements_demo()

        query = f"""
        SELECT
            M.AR_Ref AS reference,
            A.AR_Design AS designation,
            M.MS_Date AS date_mouvement,
            M.MS_Qte AS quantite,
            M.MS_Type AS type_mouvement
        FROM F_MVTSTOCK M
        JOIN F_ARTICLE A ON M.AR_Ref = A.AR_Ref
        WHERE M.MS_Date >= DATEADD(day, -{jours}, GETDATE())
        ORDER BY M.MS_Date DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return get_mouvements_demo()

# ---------------------------------------------------------
# DONNÉES DE DÉMONSTRATION (quand Sage n'est pas connecté)
# ---------------------------------------------------------
def get_stock_demo():
    """
    Données de démonstration pour tester sans Sage.
    """
    import numpy as np
    np.random.seed(42)

    produits = [
        ("RIZ001", "Riz Basmati 5kg", "Épicerie"),
        ("HUI001", "Huile de Tournesol 5L", "Épicerie"),
        ("SUC001", "Sucre Blanc 2kg", "Épicerie"),
        ("FAR001", "Farine de Blé 5kg", "Épicerie"),
        ("LAI001", "Lait UHT 1L", "Produits Laitiers"),
        ("BEU001", "Beurre 250g", "Produits Laitiers"),
        ("YAO001", "Yaourt Nature", "Produits Laitiers"),
        ("SAB001", "Savon de Ménage", "Hygiène"),
        ("SHA001", "Shampoing 500ml", "Hygiène"),
        ("PAP001", "Papier Toilette x12", "Hygiène"),
        ("EAU001", "Eau Minérale 1.5L", "Boissons"),
        ("JUS001", "Jus d'Orange 1L", "Boissons"),
        ("CON001", "Concentré de Tomate", "Conserves"),
        ("SAR001", "Sardines en Boîte", "Conserves"),
        ("PTE001", "Pâtes Spaghetti 500g", "Épicerie"),
    ]

    data = []
    for ref, nom, famille in produits:
        qte = np.random.randint(0, 500)
        prix_achat = np.random.uniform(0.5, 15.0)
        prix_vente = prix_achat * 1.3
        stock_min = np.random.randint(20, 100)
        stock_max = stock_min * 5

        data.append({
            "reference": ref,
            "designation": nom,
            "prix_vente": round(prix_vente, 2),
            "prix_achat": round(prix_achat, 2),
            "quantite_stock": qte,
            "valeur_stock": round(qte * prix_achat, 2),
            "stock_minimum": stock_min,
            "stock_maximum": stock_max,
            "famille": famille
        })

    return pd.DataFrame(data)

def get_commandes_demo():
    """
    Données de démonstration des commandes supermarchés.
    """
    import numpy as np
    np.random.seed(42)

    supermarchés = [
        ("SM001", "Supermarché Bissau Centre"),
        ("SM002", "Supermarché Bairro Militar"),
        ("SM003", "Supermarché Bandim"),
        ("SM004", "Supermarché Bô Lama"),
        ("SM005", "Supermarché Penha"),
        ("SM006", "Supermarché Antula"),
    ]

    produits = [
        ("RIZ001", "Riz Basmati 5kg", 8.50),
        ("HUI001", "Huile de Tournesol 5L", 12.00),
        ("SUC001", "Sucre Blanc 2kg", 3.50),
        ("LAI001", "Lait UHT 1L", 1.80),
        ("EAU001", "Eau Minérale 1.5L", 0.80),
    ]

    data = []
    for i in range(30):
        sm_code, sm_nom = supermarchés[np.random.randint(0, 6)]
        ref, nom, prix = produits[np.random.randint(0, 5)]
        qte = np.random.randint(10, 200)
        date = datetime.now() - timedelta(days=np.random.randint(0, 30))

        data.append({
            "numero_commande": f"BC{str(i+1).zfill(5)}",
            "date_commande": date.strftime("%Y-%m-%d"),
            "code_client": sm_code,
            "nom_supermarche": sm_nom,
            "reference": ref,
            "designation": nom,
            "quantite_commandee": qte,
            "prix_unitaire": prix,
            "montant_ht": round(qte * prix, 2),
            "statut": np.random.choice(["En attente", "En cours", "Livré"])
        })

    return pd.DataFrame(data)

def get_mouvements_demo():
    """
    Données de démonstration des mouvements de stock.
    """
    import numpy as np
    np.random.seed(42)

    produits = ["RIZ001", "HUI001", "SUC001", "LAI001", "EAU001"]
    types = ["Entrée", "Sortie"]

    data = []
    for i in range(50):
        date = datetime.now() - timedelta(days=np.random.randint(0, 30))
        data.append({
            "reference": produits[np.random.randint(0, 5)],
            "designation": f"Produit {i}",
            "date_mouvement": date.strftime("%Y-%m-%d"),
            "quantite": np.random.randint(1, 100),
            "type_mouvement": types[np.random.randint(0, 2)]
        })

    return pd.DataFrame(data)