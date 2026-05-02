import pandas as pd
import numpy as np

# Délai de livraison Portugal en semaines
DELAI_LIVRAISON_SEMAINES = 4
STOCK_SECURITE_SEMAINES = 1

def calculer_consommation_moyenne(df_mouvements, reference):
    """
    Calcule la consommation moyenne hebdomadaire d'un produit.
    """
    try:
        sorties = df_mouvements[
            (df_mouvements["reference"] == reference) &
            (df_mouvements["type_mouvement"] == "Sortie")
        ]
        if sorties.empty:
            return 0
        total_sorties = sorties["quantite"].sum()
        nb_semaines = 4  # sur 4 semaines
        return round(total_sorties / nb_semaines, 2)
    except:
        return 0

def calculer_point_commande(consommation_hebdo):
    """
    Calcule le point de commande (seuil déclenchement commande).
    Point de commande = Consommation × (Délai livraison + Stock sécurité)
    """
    return round(consommation_hebdo * (DELAI_LIVRAISON_SEMAINES + STOCK_SECURITE_SEMAINES), 0)

def calculer_qec(consommation_annuelle, cout_commande=50, taux_possession=0.2, prix_unitaire=1):
    """
    Calcule la Quantité Économique de Commande (formule de Wilson).
    QEC = sqrt(2 × D × K / (t × p))
    D = demande annuelle
    K = coût de passation de commande
    t = taux de possession
    p = prix unitaire
    """
    try:
        if consommation_annuelle <= 0 or prix_unitaire <= 0:
            return 0
        qec = np.sqrt((2 * consommation_annuelle * cout_commande) / (taux_possession * prix_unitaire))
        return round(qec, 0)
    except:
        return 0

def analyser_alertes_stock(df_stock, df_mouvements):
    """
    Analyse le stock et génère les alertes.
    """
    alertes = []

    for _, row in df_stock.iterrows():
        ref = row["reference"]
        qte_stock = row["quantite_stock"]
        stock_min = row["stock_minimum"]
        prix_achat = row["prix_achat"]

        # Consommation moyenne hebdomadaire
        conso_hebdo = calculer_consommation_moyenne(df_mouvements, ref)

        # Point de commande
        point_commande = calculer_point_commande(conso_hebdo)

        # QEC
        conso_annuelle = conso_hebdo * 52
        qec = calculer_qec(conso_annuelle, prix_unitaire=prix_achat)

        # Statut
        if qte_stock == 0:
            statut = "🔴 RUPTURE"
            priorite = 1
        elif qte_stock <= stock_min:
            statut = "🟠 CRITIQUE"
            priorite = 2
        elif qte_stock <= point_commande:
            statut = "🟡 À COMMANDER"
            priorite = 3
        else:
            statut = "🟢 OK"
            priorite = 4

        alertes.append({
            "reference": ref,
            "designation": row["designation"],
            "quantite_stock": qte_stock,
            "stock_minimum": stock_min,
            "point_commande": point_commande,
            "conso_hebdo": conso_hebdo,
            "qec": qec,
            "valeur_stock": row["valeur_stock"],
            "statut": statut,
            "priorite": priorite
        })

    df_alertes = pd.DataFrame(alertes)
    df_alertes = df_alertes.sort_values("priorite")
    return df_alertes

def generer_commande_portugal(df_alertes):
    """
    Génère la liste des produits à commander au Portugal.
    """
    a_commander = df_alertes[
        df_alertes["priorite"].isin([1, 2, 3])
    ].copy()

    if a_commander.empty:
        return pd.DataFrame()

    a_commander["quantite_a_commander"] = a_commander["qec"].apply(
        lambda x: max(x, 1)
    )

    return a_commander[[
        "reference",
        "designation",
        "quantite_stock",
        "point_commande",
        "quantite_a_commander",
        "statut"
    ]]

def consolider_besoins_supermarchés(df_commandes):
    """
    Consolide les besoins de tous les supermarchés.
    """
    if df_commandes.empty:
        return pd.DataFrame()

    consolidé = df_commandes.groupby(
        ["reference", "designation"]
    ).agg(
        total_commande=("quantite_commandee", "sum"),
        nb_supermarchés=("code_client", "nunique"),
        montant_total=("montant_ht", "sum")
    ).reset_index()

    return consolidé.sort_values("total_commande", ascending=False)