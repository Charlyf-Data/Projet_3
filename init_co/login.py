import streamlit as st 
from st_utils import st_utils



def login_page():
    """Affiche la page de connexion avec ses onglets."""
    st.title("Connexion")
    tab1, tab2, tab3 = st.tabs(["Se connecter", "Mode Invité", "Inscriptions"])
    
    with tab1:
        st_utils.users_connect()
    with tab2:
        st_utils.mode_invite()
    with tab3:
        st_utils.creer_compte()
