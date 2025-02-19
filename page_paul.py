import streamlit as st
from datetime import datetime
from sqlmanager import Sql_manager
from gepetto.geppetto import Geppetto
from st_utils import st_utils  
import pandas as pd 
import re
import time



def extraire_demande_utilisateur(response):
    """
    Cette fonction extrait le contenu entre crochets dans la chaîne 'response'.
    
    :param response: Chaîne de caractères potentiellement contenant du contenu entre crochets.
    :return: Le contenu entre crochets ou None si aucun crochet n'est détecté.
    """
    match = re.search(r'\[(.*?)\]', response)
    if match:
        return match.group(1)  # Retourne le contenu dans les crochets  
    else:
        return None  # Retourne None si aucun crochet n'est détecté

def main_app():
    st.markdown("""
        <style>
        .chat-message {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            max-width: 70%;
            transition: background 0.3s ease;
        }
        .user-message {
            background-color: #D1E8FF; 
            margin-left: auto; 
        }
        .assistant-message {
            background-color: #FFFFFF; 
            margin-right: auto; 
        }
        .message-time {
            font-size: 0.8rem;
            color: #666;
            text-align: right;
        }
        .stApp {
            background: rgba(255, 255, 255, 0.4);
            backdrop-filter: blur(10px);
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title("Navigation")

    
    if st.session_state["id_user_con"]:
        st.sidebar.write(f"Nom : {st.session_state['username_user']}")
        st.sidebar.write(f"Rôle : {st.session_state['role_user']}")
    
    deconnexion = st.sidebar.button("Se déconnecter")
    if deconnexion:
        for key in list(st.session_state.keys()):
            del st.session_state[key]  # Supprime toutes les variables de session
        st.rerun()  # Recharge l'application proprement

    st.title("Bienvenue dans l'Appet'Eat")

    # Interface de chat  
    def add_to_history(user_message, response_message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.history.insert(0, {  
            "time": timestamp,
            "user": user_message,
            "response": response_message  
        })

    def send_message():
        user_input = st.session_state.get("user_input", "").strip()
        if user_input:
            with st.spinner("Polo est en train de répondre..."):
                response = st.session_state.geppetto.talk(user_input)
                demande_utilisateur = extraire_demande_utilisateur(response)
                add_to_history(user_input, response)
                if demande_utilisateur is not None:
                    st.session_state['search_user'] = demande_utilisateur
                    st.session_state['etape'] = 3
                    time.sleep(2)
                    st.rerun()
            st.session_state["message_ready"] = True  # Marquer que le message a été traité
            st.session_state["temp_input"] = ""# Utilisation d'une variable temporaire
            st.rerun()

    reset = st.sidebar.button("Réinitialiser la discussion")
    if reset:
        st.session_state.history = []
        st.success("La discussion a été réinitialisée.")
        st.rerun()

    if st.session_state.history:
        st.markdown("### 🗨️ Discussion")
        for msg in st.session_state.history[::-1]:
            st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>Vous :</strong> {msg['user']}
                    <div class="message-time">{msg['time']}</div>
                </div>
                <div class="chat-message assistant-message">
                    <strong>Polo :</strong> {msg['response']}
                    <div class="message-time">{msg['time']}</div>
                </div>
            """, unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])

    with col1:
        st.text_input("🗣️ Parlez à Polo", 
                    key="user_input", 
                    placeholder="Votre message ici...",
                    value=st.session_state.get("temp_input", ""))

    with col2:
        st.write("\n\n")
        if st.button("Envoyer", key="send_button"):
            send_message()
    
    if st.session_state.get("message_ready", False):
        st.session_state["message_ready"] = False
        st.session_state["temp_input"] = ""
        st.rerun()
