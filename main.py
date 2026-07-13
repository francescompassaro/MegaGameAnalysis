import streamlit as st
import os

# 1. IMPOSTAZIONI GLOBALI E PERSISTENZA STATO (Eseguiti prima di tutto)
st.set_page_config(page_title="Lega Pauper Capua", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "errore_login" not in st.session_state:
    st.session_state["errore_login"] = False

PASSWORD_ADMIN = os.getenv("ADMIN_PASSWORD", "pauper_default")

def processo_autenticazione():
    """Valida le credenziali e fissa lo stato in memoria prima del ciclo di navigazione"""
    if st.session_state["campo_password_admin"] == PASSWORD_ADMIN:
        st.session_state["logged_in"] = True
        st.session_state["errore_login"] = False
        st.toast("Accesso effettuato!")
    else:
        st.session_state["errore_login"] = True

# --- INTERFACCIA BARRA LATERALE ---
st.sidebar.title("Lega Pauper Capua")

if not st.session_state["logged_in"]:
    st.sidebar.subheader("Accesso Admin")
    with st.sidebar.form(key="form_login"):
        st.text_input("Password", type="password", key="campo_password_admin")
        st.form_submit_button("Accedi", on_click=processo_autenticazione)

    if st.session_state["errore_login"]:
        st.sidebar.error("Password errata!")
        st.session_state["errore_login"] = False
else:
    st.sidebar.success("Modalita Admin Attiva")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.rerun()

st.sidebar.markdown("---")

# --- MOTORE DI NAVIGAZIONE MULTIPAGINA ---
page_dashboard = st.Page("dashboard.py", title="Dashboard Pubblica", default=True)
page_liste = st.Page("liste.py", title="Liste per Tappa")
page_admin = st.Page("inserisci_dati.py", title="Inserisci Nuovi Dati")

pagine_disponibili = [page_dashboard, page_liste]

if st.session_state["logged_in"]:
    pagine_disponibili.append(page_admin)

pg = st.navigation(pagine_disponibili)
pg.run()
