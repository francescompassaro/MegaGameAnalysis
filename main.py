import streamlit as st
import os

# 1. IMPOSTAZIONI GLOBALI E PERSISTENZA STATO
st.set_page_config(page_title="Lega Pauper Capua", layout="wide")

# Usiamo "autenticato" che e una variabile pura, slegata dai widget grafici
if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if "errore_login" not in st.session_state:
    st.session_state["errore_login"] = False

PASSWORD_ADMIN = os.getenv("ADMIN_PASSWORD", "pauper_default")

def processo_autenticazione():
    # Controlliamo il valore del widget text_input
    if st.session_state["input_pwd_raw"] == PASSWORD_ADMIN:
        # Fissiamo il flag su una variabile di stato indipendente
        st.session_state["autenticato"] = True
        st.session_state["errore_login"] = False
        st.toast("Accesso effettuato!")
    else:
        st.session_state["errore_login"] = True

# --- INTERFACCIA BARRA LATERALE ---
st.sidebar.title("Lega Pauper Capua")

if not st.session_state["autenticato"]:
    st.sidebar.subheader("Accesso Admin")
    with st.sidebar.form(key="form_login"):
        # Il widget scrive su una chiave temporanea "input_pwd_raw"
        st.text_input("Password", type="password", key="input_pwd_raw")
        st.form_submit_button("Accedi", on_click=processo_autenticazione)

    if st.session_state["errore_login"]:
        st.sidebar.error("Password errata!")
        st.session_state["errore_login"] = False
else:
    st.sidebar.success("Modalita Admin Attiva")
    if st.sidebar.button("Log Out"):
        st.session_state["autenticato"] = False
        st.rerun()

st.sidebar.markdown("---")

# --- MOTORE DI NAVIGAZIONE MULTIPAGINA ---
page_dashboard = st.Page("dashboard.py", title="Dashboard Pubblica", default=True)
page_liste = st.Page("liste.py", title="Liste per Tappa")
page_admin = st.Page("inserisci_dati.py", title="Inserisci Nuovi Dati")

pagine_disponibili = [page_dashboard, page_liste]

# Il menu si aggiorna guardando la variabile di stato pura
if st.session_state["autenticato"]:
    pagine_disponibili.append(page_admin)

pg = st.navigation(pagine_disponibili)
pg.run()
