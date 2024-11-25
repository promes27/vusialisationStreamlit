import streamlit as st
import pandas as pd
import os
import duckdb
import altair as alt
from streamlit_extras.metric_cards import style_metric_cards


#titre 
st.set_page_config(layout="wide")
st.title("Dashbord")

#load data
@st.cache_data
def load_data(path: str):
    data = pd.read_csv(path)
    return data
#upload file
upload_file = st.sidebar.file_uploader("Télécharger un fichier")
if upload_file is None:
    st.info("les données sont vide")
    st.stop()
df_1 = load_data(upload_file)
with st.expander("Mes données"):
    # df_1=pd.read_csv("Data.csv")
    st.dataframe(df_1)


#filtre des villes
st.sidebar.header("filtre")
# adresse = duckdb.sql("""
#         SELECT 
#             DISTINCT Ville 
#         FROM df 
#         ORDER BY Ville
#     """).df()
ville = st.sidebar.selectbox('Ville', df_1["Ville"].unique())

#date 
# Convertir les colonnes en datetime
df_1["DateOuverture"] = pd.to_datetime(df_1["DateOuverture"])
df_1["DateFermeture"] = pd.to_datetime(df_1["DateFermeture"], errors='coerce')

# Sélection des dates via Streamlit
start_date = pd.to_datetime(st.sidebar.date_input("Date début", value=df_1["DateOuverture"].min()))
end_date = pd.to_datetime(st.sidebar.date_input("Date fin", value=pd.Timestamp.now()))

# Gestion des valeurs nulles pour DateFermetureCompte
# On remplace les valeurs nulles par une date future (e.g., aujourd'hui ou une date maximale)
df_1["DateFermeture"].fillna(pd.to_datetime("2024-10-31"), inplace=True)

# Filtrage basé sur les conditions
# df = df_1[(df_1["DateOuverture"] <= end_date) & (df_1["DateOuverture"] >= start_date)]
df = df_1[(df_1["DateOuverture"] <= end_date) & (df_1["DateFermeture"] >= start_date)]
    
#declaration colonne
col1,col2,col3,col4 = st.columns((4)) 

style_metric_cards(border_color="none",box_shadow="#F71938",background_color="dark")
#requettes SQL avec Duckdb
with col1:
    nombre_client = duckdb.sql(f"""
        SELECT COUNT(DISTINCT ClientID) AS nombre_clients
        FROM df 
        WHERE Ville = '{ville}' 
""").df()
    # df_1

    # Extraire la valeur de la colonne 'nombre_clients'
    nombre_total_client = nombre_client['nombre_clients'].iloc[0]

    # Afficher la métrique
    st.metric(label="Nombre Total de Clients", value=nombre_total_client)

#nombre total de pret
with col2:
    nombre_pret = duckdb.sql(f"""
        SELECT COUNT(DISTINCT PretID) AS nombre_pret
        FROM df
        WHERE Ville = '{ville}' 
    """).df()
    # Extraire la valeur de la colonne 'nombre'
    nombre_total_pret = nombre_pret['nombre_pret'].iloc[0]
    
    # Afficher la métrique
    st.metric(label="Nombre Total de Prêts", value=nombre_total_pret)

with col3:
    nombre_compte = duckdb.sql(f"""
        SELECT COUNT (DISTINCT CompteID) AS nombre_compte
        FROM df
        WHERE Ville = '{ville}' 
    """).df()
    #Extraire la valeur de la colonne 'nombre de compte'
    nombre_total_compte = nombre_compte['nombre_compte'].iloc[0]

    #Afficher la metrique
    st.metric(label="Nombre Total de comptes", value=nombre_total_compte)

with col4:
    nombre_transaction = duckdb.sql(f"""
    SELECT COUNT(DISTINCT TransactionID) AS nombre_transaction
    FROM df
    WHERE Ville = '{ville}' 
    """).df()

    # Extraire la valeur de la colonne 'nombre_transaction'
    nombre_total_transaction = nombre_transaction['nombre_transaction'].iloc[0]

    # Afficher la métrique
    st.metric(label="Nombre Total de transactions", value=nombre_total_transaction)
   


################### graphe ###############################
col1,col2 = st.columns((2))


with col1:
    nbr_churn = duckdb.query(f"""
    SELECT StatutCompte, COUNT(DISTINCT CompteID) AS nbr_churn_total
    FROM df
    WHERE Ville = '{ville}'
    GROUP BY StatutCompte
    """).df()

    chart = alt.Chart(nbr_churn).mark_bar().encode(
        x=alt.X("StatutCompte", title="Statut du Compte"),  # Titre de l'axe X
        y=alt.Y("nbr_churn_total", title="Nombre de Churn Total")# Titre de l'axe Y

    ).properties(
        title="Nombre de Churn par Statut de Compte"  # Titre du graphique
    )

    # Affichage dans Streamlit
    st.altair_chart(chart, use_container_width=True)

with col2:
    nbr_fd = duckdb.query(f"""
    SELECT TypeEngagement, COUNT(DISTINCT EngagementID) AS nbr_fd_total
    FROM df
    WHERE Ville = '{ville}'
    GROUP BY TypeEngagement
    """).df()
    chart = alt.Chart(nbr_fd).mark_arc().encode(
        theta=alt.Theta("nbr_fd_total:Q", title="Nombre Total"),  # Valeurs quantitatives
        # color=alt.Color("TypeEngagement:N", legend=alt.Legend(title="Type d'Engagement")),  # Catégories
        # tooltip=["TypeEngagement", "nbr_fd_total"],
        color=alt.Color(
        "TypeEngagement:N",
        scale=alt.Scale(
            domain=["Participation Programme Fidélité", "Utilisation Application Mobile"],  # Noms des catégories
            range=["#1f77b4", "#ff7f0e"]  # Couleurs personnalisées (bleu, orange, vert)
        ),
        legend=alt.Legend(title="Type d'Engagement"))  # Titre de la légende
         # Info-bulles
    ).properties(
        title="Répartition des Types d'Engagement"
    )

    # Affichage dans Streamlit
    st.altair_chart(chart, use_container_width=True)

#declaration de colonne

requete = duckdb.sql(f"""
    SELECT 
            TypeTransaction, 
            TypeCompte,
            SUM(MontantTransaction) AS TotalMontantTransaction
    FROM df
    WHERE Ville = '{ville}'
    GROUP BY TypeTransaction, TypeCompte
""").df()

# Création du graphique
chart = alt.Chart(requete).mark_bar().encode(
    x=alt.X("TypeTransaction:N", title="Type de Transaction"),  # Axe X
    xOffset="TypeCompte:N",                                     # Décalage pour barres groupées
    y=alt.Y("TotalMontantTransaction:Q", title="Montant Total (Ar)"),  # Axe Y
    color=alt.Color("TypeCompte:N", title="Type de Compte"),  # Couleur
    tooltip=["TypeTransaction", "TypeCompte", "TotalMontantTransaction"]  # Info-bulles
).properties(
    title="Montant des Transactions par Type",
    width=800,  # Largeur personnalisée
    height=400  # Hauteur personnalisée
)

st.altair_chart(chart, use_container_width=True)


col1,col2 = st.columns((2))

df_1["DateTransaction"] = pd.to_datetime(df_1["DateTransaction"])

#filtre un nouveau date
with st.form("Date_precedante/Date_actuel"):
    subcol1,subcol2 = st.columns(2)
    # with subcol1:
    date1 = col1.date_input(
    "Date precedent",
    (df_1["DateTransaction"].min(), df_1["DateTransaction"].mean()),
    min_value=df_1["DateTransaction"].min(),
    max_value=df_1["DateTransaction"].max(),
    format="DD/MM/YYYY",
    )
    # with subcol2:
        # Every form must have a submit button.
        # df2 = df_1[(df_1["DateTransaction"] )] 
    date2 = col2.date_input(
    "Date Actuel",
    (df_1["DateTransaction"].min(), df_1["DateTransaction"].mean()),
    min_value = df_1["DateTransaction"].min(),
    max_value = df_1["DateTransaction"].max(),
    format="DD/MM/YYYY",
    )

    submitted1 = st.form_submit_button("Go")    
    if submitted1:
        with subcol1:
            df_2 = df_1[(df_1["DateTransaction"] <= pd.to_datetime(date1[1])) & (df_1["DateTransaction"] >= pd.to_datetime(date1[0]))]

            requete = duckdb.sql(f"""
                Select DISTINCT TransactionID,CompteID,MontantTransaction
                FROM df_2
                WHERE Ville = '{ville}'
                ORDER BY MontantTransaction DESC
                LIMIT 10
            """).df()
            requete

            Courbe = duckdb.sql(f"""
                    SELECT 
                        Mois,
                        SUM(MontantTransaction) as somme_trans
                    FROM df_2 
                        WHERE Ville = '{ville}' AND Mois IS NOT NULL
                    GROUP BY Mois
                """).df()
            Courbe
            # chart = alt.Chart(Courbe).mark_line(point=True).encode(
            #     x=alt.X("Mois", sort="ascending"),
            #     y="somme_trans",
            #     tooltip=["Mois", "somme_trans"]
            # ).properties(
            #     title="Somme de transaction par mois"
            # )

            # # Afficher le graphique dans Streamlit
            # st.altair_chart(chart, use_container_width=True)


        
        with subcol2:
            df_3 = df_1[(df_1["DateTransaction"] <= pd.to_datetime(date2[1])) & (df_1["DateTransaction"] >= pd.to_datetime(date2[0]))]

            requete1 = duckdb.sql(f"""
                 Select DISTINCT TransactionID,CompteID,MontantTransaction
                FROM df_3
                WHERE Ville = '{ville}'
                ORDER BY MontantTransaction DESC
                LIMIT 10
            """).df()
            requete1

            Courbe = duckdb.sql(f"""
                    SELECT 
                        Mois,
                        SUM(MontantTransaction) as somme_trans
                        FROM df_3 
                        WHERE Ville = '{ville}' AND Mois IS NOT NULL
                    GROUP BY Mois
                """).df()
            chart = alt.Chart(Courbe).mark_line(point=True).encode(
                x=alt.X("Mois", sort="ascending"),
                y="somme_trans",
                tooltip=["Mois", "somme_trans"]
            ).properties(
                title="Somme de transaction par mois"
            )

            # Afficher le graphique dans Streamlit
            st.altair_chart(chart, use_container_width=True)
pourCSAT = duckdb.sql("""
    SELECT Ville,
    ROUND(SUM(CASE WHEN scoreCSAT >= 7 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS csat_percentage
    FROM df
    GROUP BY Ville
""").df()

chart = alt.Chart(pourCSAT).mark_bar(point=True).encode(
    x="Ville",
    y="csat_percentage",
    tooltip=["Ville", "csat_percentage"]
).properties(
    title="CSAT (%) par ville"
)

# Afficher le graphique dans Streamlit
st.altair_chart(chart, use_container_width=True)


MontTrans = duckdb.sql("""
    SELECT Ville,
    SUM(MontantTransaction) AS Somme_Transaction
    FROM df
    GROUP BY Ville
""").df()
chart = alt.Chart(MontTrans).mark_bar(point=True).encode(
    x="Ville",
    y="Somme_Transaction",
    tooltip =["Ville","Somme_Transaction"]
).properties(
    title = "Somme transaction par ville"
)

# Afficher le graphique dans Streamlit
st.altair_chart(chart, use_container_width=True)

st.write("Tous les clients n'ont pas satifaits par ville")
col1,col2,col3 = st.columns(3)
with col1:
    requeteCSAT1 = duckdb.sql(f"""
        SELECT DISTINCT CompteID,Nom,Prenom,ScoreCSAT
        FROM df
        WHERE ScoreCSAT <= 3 AND Ville = '{ville}'
        ORDER BY ScoreCSAT ASC
        LIMIT 20
    """).df()

    requeteCSAT1

with col2:
    requeteCSAT2 = duckdb.sql(f"""
        SELECT DISTINCT CompteID,Nom,Prenom,ScoreCSAT
        FROM df
        WHERE ScoreCSAT>=3 AND ScoreCSAT<=4  AND Ville = '{ville}'
        ORDER BY ScoreCSAT ASC
        LIMIT 20
    """).df()

    requeteCSAT2

with col3:
    requeteCSAT3 = duckdb.sql(f"""
        SELECT DISTINCT CompteID,Nom,Prenom,ScoreCSAT
        FROM df
        WHERE ScoreCSAT>=5 AND ScoreCSAT<=6 AND Ville = '{ville}'
        ORDER BY ScoreCSAT ASC
        LIMIT 20
    """).df()

    requeteCSAT3

########colonne######
col1,col2 = st.columns(2)

with col1:
    st.write("Top 5 clients plus de transactions")
    Toprequete = duckdb.sql(f"""
        SELECT DISTINCT Nom,Prenom,MontantTransaction
        FROM df
        WHERE Ville ='{ville}'
        ORDER BY MontantTransaction DESC
        LIMIT 5
    """).df()
    Toprequete


with col2:
    st.write("Top 5 clients Moins de transactions")
    Toprequete = duckdb.sql(f"""
        SELECT DISTINCT Nom,Prenom,MontantTransaction
        FROM df
        WHERE Ville ='{ville}'
        ORDER BY MontantTransaction ASC
        LIMIT 5
    """).df()
    Toprequete


col1,col2 = st.columns(2)
with col1:
    MontPret = duckdb.sql("""
        SELECT Ville,
        SUM(MontantPret) AS Somme_Pret
        FROM df
        GROUP BY Ville
    """).df()
    chart = alt.Chart(MontPret).mark_bar(point=True).encode(
        x="Ville",
        y="Somme_Pret",
        tooltip =["Ville","Somme_Pret"]
    ).properties(
        title = "Somme Pret par ville"
    )

    # Afficher le graphique dans Streamlit
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.write("Age moyen clients qui fait le prets")
    Agemoyen = duckdb.sql(f"""
        SELECT ROUND(AVG(AgeClient)) AS AgeMoyen
        FROM df
        WHERE Ville ='{ville}'
    """).df()

    AgeMoyen = Agemoyen['AgeMoyen'].iloc[0]

        #Afficher la metrique
    st.metric(label="Age Moyen", value=AgeMoyen)

#######################################################################################################################################


#colonne 
# Filtrage basé sur les conditions

# requete1 = duckdb.sql(f"""
#     SELECT 
#         COUNT(DISTINCT TransactionID) AS nbr_compte, 
#         StatutCompte, 
#         Annee
#     FROM df
#     WHERE 
#         Ville = '{ville}'
#         AND DateOuverture <= '{end_date}'
#         AND (DateFermeture IS NULL OR DateFermeture >= '{start_date}')
#     GROUP BY 
#         Annee, 
#         StatutCompte
# """)




# #filtre en date
# df_1["DateTransaction"] = pd.to_datetime(df_1["DateTransaction"])

# #selectionner date et ville
# start_date = pd.to_datetime(st.sidebar.date_input("Date début",value=df_1["DateTransaction"].min()))
# end_date = pd.to_datetime(st.sidebar.date_input("Date fin",value=df_1["DateTransaction"].max()))
# #comparer un date
# df_1 = df_1[df_1["DateTransaction"] <= end_date]
# df_1 = df_1[df_1["DateTransaction"] >= start_date]

# st.sidebar.header("selectionner les villes")

# ville = st.sidebar.multiselect(
#     "selectionner les villes",
#     options=df_1["Ville"].unique(),
# )