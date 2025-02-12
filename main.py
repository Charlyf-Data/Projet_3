from page_paul import main_app
from C_belaud import main_Clement
import streamlit as st 
from init_co import login, initialisation


def main():
    initialisation.init_session_state()
    # pas connecté etqpe 1
    if st.session_state["etape"] == 1:
        login.login_page() 
    elif st.session_state["etape"] == 2:
         main_app()
    elif st.session_state["etape"] == 3:
        main_Clement.main1()

        

main()

