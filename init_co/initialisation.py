import streamlit as st
from datetime import datetime
from sqlmanager import Sql_manager
from gepetto.geppetto import Geppetto
from st_utils import st_utils  
import pandas as pd 





def init_session_state():
    if "sql_manager" not in st.session_state:
        st.session_state["sql_manager"] = Sql_manager()
    if "id_user_con" not in st.session_state:
        st.session_state["id_user_con"] = None
    if "geppetto" not in st.session_state:
        st.session_state["geppetto"] = Geppetto()
        st.session_state["geppetto"].preprompt("bienvenue_projet_3")
    if "history" not in st.session_state or (st.session_state["id_user_con"] is None):
        st.session_state["history"] = []  #permet de fermer l'application sans se déconnecter et de vider l'historique."
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""
    if "temp_input" not in st.session_state:
        st.session_state["temp_input"] = "" #permet de vider le cache et de ne pas créer un bug quand polo cherche la réponse.
    if "message_ready" not in st.session_state:
        st.session_state["message_ready"] = False  
    if "etape" not in st.session_state:
        st.session_state["etape"] = 1
    for key in ['restaurants', 'df', 'favorites', 'search_history', 'reviews', 'selected_route']:
        if key not in st.session_state:
            st.session_state[key] = [] if key != 'df' else pd.DataFrame()
    if "user_reviews" not in st.session_state:
        st.session_state.user_reviews = {}
        
        