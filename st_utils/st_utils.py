import streamlit as st
import base64
from sqlmanager import Sql_manager
from sqlalchemy import text

def add_background(image_path):
    """
    Ajoute une image de fond en utilisant un encodage base64.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Erreur lors du chargement de l'image de fond: {e}")


def mode_invite():
    """Permet la connexion en mode invité."""
    sql = st.session_state["sql_manager"]
    st.subheader("Connexions")
    if st.button("Se connecter en tant qu'invité", key="guest_button"):
        id_guest, username_guest, role_guest = sql.find_id_user("invite_guest","Invite123")
        if  id_guest != -1:  
            st.session_state["id_user_con"] = id_guest
            st.session_state["username_user"] = username_guest
            st.session_state["role_user"] = role_guest
            st.session_state["etape"]= 2
            st.rerun()

        return id_guest, username_guest, role_guest


def users_connect():
    """Affiche la page de connexion."""
    sql = st.session_state["sql_manager"]
    st.subheader("Connexion")
    username = st.text_input("Nom d'utilisateur", key="login_username")
    password = st.text_input("Mot de passe", type="password", key="login_password")
    if st.button("Se connecter", key="login_button"):
        id_user, username, role_user = sql.find_id_user(username, password)
        if id_user != -1: 
            st.session_state["id_user_con"] = id_user
            st.session_state["username_user"] = username
            st.session_state["role_user"] = role_user
            st.session_state["etape"] = 2
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects.")

        return id_user, username, role_user


def creer_compte():
    """Affiche le formulaire d'inscription et connecte l'utilisateur après inscription réussie."""
    st.subheader("📝 Inscription")

    # Champs du formulaire
    name = st.text_input("Nom complet")
    username = st.text_input("Nom d'utilisateur")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    role = st.selectbox("Rôle", ["Utilisateur", "Admin"])  # Exemple de rôles

    # Bouton d'inscription
    if st.button("S'inscrire"):
        sql_manager = st.session_state["sql_manager"]  # Récupération de l'objet de gestion SQL
        success = sql_manager.inscrire_utilisateur(name, username, email, password, role)

        if success:
            st.success("✅ Inscription réussie ! Redirection vers la connexion...")
            st.session_state["id_user_con"] = username  # Simule une connexion immédiate
            st.rerun()  # Recharge la page pour afficher l'espace connecté
        else:
            st.error("❌ Nom d'utilisateur déjà pris ou erreur lors de l'inscription.")


        