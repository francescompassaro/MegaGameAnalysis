import streamlit as st
import os

# Impostazioni globali della pagina (vanno definite una sola volta qui)
st.set_page_config(page_title="Lega Pauper Capua", layout="wide")

PASSWORD_ADMIN = os.getenv("ADMIN_PASSWORD", "pauper_default")

# Inizializzazione stati di sessione
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "errore_login" not in st.session_state:
    st.session_state["errore_login"] = False

def processo_autenticazione():
    if st.session_state["campo_password_admin"] == PASSWORD_ADMIN:
        st.session_state["logged_in"] = True
        st.session_state["errore_login"] = False
        st.toast("Accesso effettuato!")
    else:
        st.session_state["errore_login"] = True

# --- LOGIN NELLA SIDEBAR ---
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

# --- DEFINIZIONE DELLE PAGINE NATIVE ---
# Specifichiamo il file Python e il titolo che deve apparire nel menu
page_dashboard = st.Page("dashboard.py", title="Dashboard Pubblica", default=True)
page_liste = st.Page("liste.py", title="Liste per Tappa")
page_admin = st.Page("inserisci_dati.py", title="Inserisci Nuovi Dati")

# --- ROUTING DINAMICO ---
# Creiamo la lista delle pagine visibili sul momento
pagine_disponibili = [page_dashboard, page_liste]

# Se l'utente è loggato, iniettiamo la pagina admin nel menu
if st.session_state["logged_in"]:
    pagine_disponibili.append(page_admin)

# Il widget di navigazione nativo genera automaticamente l'elenco cliccabile nella sidebar
pg = st.navigation(pagine_disponibili)

# Esegue la pagina selezionata
pg.run()
