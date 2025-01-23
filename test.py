import streamlit as st
import pandas as pd
from outils import find, add_background

# Configuration générale de la page
st.set_page_config(layout="wide")

# En-tête de l'application
st.markdown(
    "<h1 style='color:#FFD700; text-align: center;'>WELCOME ON LAZIDI</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<h4 style='color:#FFD700; text-align: center;'>because searching should be easy!</h4>",
    unsafe_allow_html=True
)

# Ajout de l'arrière-plan
add_background('fond5.png')

# Champ de saisie
key = st.text_input("Entrez un texte ici :")

if key.strip():  # Vérification que le champ n'est pas vide
    try:
        # Appel de la fonction find pour rechercher les résultats
        result = find(key)

        if isinstance(result, pd.DataFrame) and not result.empty:
            st.write("**Résultat :**")
            st.dataframe(result)  # Affichage du DataFrame complet (en tableau)

            # Limitation à 10 résultats maximum pour un affichage détaillé
            for i in range(min(len(result), 10)):
                row = result.iloc[i]

                # Ligne de séparation visuelle
                st.markdown("<hr style='border:1px solid #ADD8E6;'>", unsafe_allow_html=True)

                # Titre avec le nom du lieu (colonne `displayName.text`)
                display_name = row.get('displayName.text', f"Lieu {i+1}")  # Valeur par défaut si `displayName.text` est vide
                st.markdown(
                    f"<h2 style='color:#FFD700;'>{display_name}</h2>",
                    unsafe_allow_html=True
                )

                # Lien du site (si disponible)
                website_uri = row.get('websiteUri', None)
                if pd.notna(website_uri):
                    st.markdown(
                        f"<p style='font-size:16px;'>🔗 <a href='{website_uri}' target='_blank'>Visiter le site</a></p>",
                        unsafe_allow_html=True
                    )
                
                # Adresse formatée (si disponible)
                formatted_address = row.get('formattedAddress', None)
                if pd.notna(formatted_address):
                    st.write(f"**Adresse :** {formatted_address}")

        else:
            st.warning("Aucun résultat trouvé. Veuillez vérifier votre entrée.")
    except Exception as e:
        st.error(f"Une erreur s'est produite : {e}")
else:
    st.error("Le champ ne peut pas être vide.")
