import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 1. IMPOSTAZIONI PAGINA
st.set_page_config(page_title="Lega Pauper Capua", layout="wide", page_icon="🏆")

DB_FILE = "lega_pauper.db"
PASSWORD_ADMIN = "pauper2026"  # La tua password per inserire i dati

# 2. INIZIALIZZAZIONE DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risultati (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anno INTEGER,
            season TEXT,
            tappa INTEGER,
            negozio TEXT,
            giocatore TEXT,
            mazzo TEXT,
            vittorie INTEGER,
            sconfitte INTEGER,
            pareggi INTEGER,
            punteggio INTEGER
        )
    """)
    conn.commit()
    conn.close()

def inserisci_risultato(tappa, negozio, giocatore, mazzo, v, s, p, punti):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO risultati (tappa, negozio, giocatore, mazzo, vittorie, sconfitte, pareggi, punteggio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tappa, negozio, giocatore, mazzo, v, s, p, punti))
    conn.commit()
    conn.close()

def carica_dati():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM risultati ORDER BY tappa DESC, punteggio DESC", conn)
    conn.close()
    return df

init_db()
df_risultati = carica_dati()

# 3. GESTIONE STATO DI LOGIN
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- BARRA LATERALE ---
st.sidebar.title("🎮 Lega Pauper Capua")

if not st.session_state["logged_in"]:
    st.sidebar.subheader("🔒 Accesso Admin")
    password_input = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Accedi"):
        if password_input == PASSWORD_ADMIN:
            st.session_state["logged_in"] = True
            st.sidebar.success("Accesso effettuato!")
            st.rerun()
        else:
            st.sidebar.error("Password errata!")
else:
    st.sidebar.success("👨‍💻 Modalità Admin Attiva")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.rerun()

opzioni_menu = ["Dashboard Pubblica"]
if st.session_state["logged_in"]:
    opzioni_menu.append("📝 Inserisci Nuovi Dati")

menu = st.sidebar.radio("Navigazione", opzioni_menu)

# --- 4. PAGINA: DASHBOARD PUBBLICA ---
if menu == "Dashboard Pubblica":
    st.title("🏆 Lega Pauper Capua - Road to Lucca")
    
    if df_risultati.empty:
        st.info("Nessun dato presente nel database. Accedi come admin nella barra laterale per inserire i risultati della prima tappa!")
    else:
        # --- ELABORAZIONE DATI CLASSIFICA ---
        df_classifica_totale = df_risultati.groupby("giocatore")["punteggio"].sum().reset_index()
        df_classifica_totale = df_classifica_totale.sort_values(by="punteggio", ascending=False).reset_index(drop=True)
        df_classifica_totale.index += 1
        df_classifica_totale.index.name = "Pos"
        df_classifica_totale = df_classifica_totale.reset_index()

        # --- SEZIONE PODIO (METRICS) ---
        st.subheader("🥇 Il Podio Attuale")
        col_p1, col_p2, col_p3 = st.columns(3)
        
        # Gestione dinamica se ci sono meno di 3 giocatori nel DB
        if len(df_classifica_totale) >= 1:
            col_p1.metric(label="1° Posto 🥇", value=df_classifica_totale.iloc[0]["giocatore"], delta=f"{int(df_classifica_totale.iloc[0]['punteggio'])} PT")
        if len(df_classifica_totale) >= 2:
            col_p2.metric(label="2° Posto 🥈", value=df_classifica_totale.iloc[1]["giocatore"], delta=f"{int(df_classifica_totale.iloc[1]['punteggio'])} PT")
        if len(df_classifica_totale) >= 3:
            col_p3.metric(label="3° Posto 🥉", value=df_classifica_totale.iloc[2]["giocatore"], delta=f"{int(df_classifica_totale.iloc[2]['punteggio'])} PT")
            
        st.markdown("---")

        # --- RIGA 1: CLASSIFICA GENERALE VS METASHARE GLOBALE ---
        st.header("🌐 Panoramica Generale")
        col_glob1, col_glob2 = st.columns([4, 3]) # Bilanciamo gli spazi (più largo a sinistra)
        
        with col_glob1:
            st.subheader("📋 Classifica Generale Completa")
            # Mostriamo la classifica pulita come una tabella Excel nativa, super leggibile
            st.dataframe(
                df_classifica_totale[['Pos', 'giocatore', 'punteggio']].rename(columns={'giocatore': 'Giocatore', 'punteggio': 'Punti Totali'}), 
                use_container_width=True, 
                hide_index=True,
                height=380
            )
            
        with col_glob2:
            st.subheader("🍩 Metashare Globale (Mazzi Giocati)")
            df_meta_glob = df_risultati.groupby("mazzo").size().reset_index(name="Presenze")
            fig_pie_glob = px.pie(
                df_meta_glob, 
                names="mazzo", 
                values="Presenze", 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie_glob.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                height=350,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_pie_glob, use_container_width=True)
            
        st.markdown("---")
        
        # --- SELETTORE TAPPA ---
        tappe_disponibili = sorted(df_risultati["tappa"].unique())
        st.header("🎯 Dettaglio Singola Tappa")
        tappa_scelta = st.selectbox("Seleziona la Tappa da visualizzare:", tappe_disponibili, index=len(tappe_disponibili)-1)
        
        df_tappa = df_risultati[df_risultati["tappa"] == tappa_scelta].sort_values(by="punteggio", ascending=False).reset_index(drop=True)
        df_tappa.index += 1
        df_tappa.index.name = "Pos Tappa"
        df_tappa = df_tappa.reset_index()

        # --- RIGA 2: CLASSIFICA TAPPA VS METASHARE TAPPA ---
        col_tappa1, col_tappa2 = st.columns([4, 3])
        
        with col_tappa1:
            st.subheader(f"📊 Classifica Ordinata - Tappa {tappa_scelta}")
            df_tappa_vis = df_tappa[['Pos Tappa', 'giocatore', 'mazzo', 'punteggio']].rename(
                columns={'giocatore': 'Giocatore', 'mazzo': 'Mazzo', 'punteggio': 'Punti Tappa'}
            )
            st.dataframe(df_tappa_vis, use_container_width=True, hide_index=True, height=350)
            
        with col_tappa2:
            st.subheader(f"🍩 Metashare - Tappa {tappa_scelta}")
            df_meta_tappa = df_tappa.groupby("mazzo").size().reset_index(name="Presenze")
            fig_pie_tappa = px.pie(
                df_meta_tappa, 
                names="mazzo", 
                values="Presenze", 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie_tappa.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                height=350,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_pie_tappa, use_container_width=True)
            
        st.markdown("---")
        
        # --- RIGA 3: TABELLA REGISTRO IN FONDO ---
        st.subheader("📋 Registro Storico di Tutti i Match Inseriti")
        df_visualizzazione = df_risultati[['tappa', 'negozio', 'giocatore', 'mazzo', 'vittorie', 'sconfitte', 'pareggi', 'punteggio']].copy()
        df_visualizzazione.columns = ['Tappa', 'Negozio', 'Giocatore', 'Mazzo Giocato', 'W', 'L', 'D', 'Punti']
        
        st.dataframe(df_visualizzazione, use_container_width=True, hide_index=True)


# --- 5. PAGINA: INSERIMENTO DATI (ADMIN) ---
elif menu == "📝 Inserisci Nuovi Dati":
    st.header("📝 Pannello Inserimento Risultati")
    ELENCO_MAZZI = sorted([  
        "Abzan En Kor",  
        "Azorius Familiars",  
        "Bogles",  
        "Boros Gates",  
        "Boros Synthesizer",  
        "Boros Tribe",  
        "Caw-Gate",  
        "Dimir Faeries",  
        "Dimir Terror",  
        "Dimir Control",  
        "Elves",  
        "Flicker Tron",  
        "Golgari Gardens",
        "Bant Gardens",
        "Grixis Affinity",  
        "Gruul Monster",  
        "Gruul Ponza",  
        "Infect MonoGreen",
        "Infect Simic",  
        "Izzet Skred",  
        "Jeskai Ephemerate",  
        "Jund Evolution",  
        "Jund Wildfire",  
        "Kuldotha Burn",  
        "Mardu Synthesis",  
        "Monoblue Faeries",  
        "Monoblue Terror",  
        "Monored Madness",  
        "Monored Rally",  
        "Monowhite Heroic",  
        "Monowhite Weenie",  
        "Orzhov Blade",  
        "Petitioners Mill",  
        "Spy Combo",  
        "Slivers",  
        "Tortured Existence",  
        "UG Turbofog",  
        "Walls Combo",  
        "WB Skyblade",
        "Naya Gates",
        "Monster Tron",
        "Rakdos Madness"

        ])

    ELENCO_NEGOZI = ["Magicomix"]
    
    with st.form("form_inserimento", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            # Nuovi campi obbligatori per il filtro temporale
            anno = st.selectbox("Anno della Season", [2026, 2027, 2025])
            season = st.selectbox("Nome Season", ["Stagione 1", "Stagione 2", "Stagione 3", "Winter", "Spring", "Summer", "Autumn"])
            tappa = st.number_input("Numero Tappa", min_value=1, max_value=50, value=1, step=1)
            
        with col_f2:
            negozio = st.selectbox("Negozio ospitante", ELENCO_NEGOZI)
            giocatore = st.text_input("Nome e Cognome Giocatore")
            mazzo = st.selectbox("Mazzo/Archetipo", ELENCO_MAZZI)
            
        with col_f3:
            vittorie = st.number_input("Vittorie (W)", min_value=0, max_value=10, value=0, step=1)
            sconfitte = st.number_input("Sconfitte (L)", min_value=0, max_value=10, value=0, step=1)
            pareggi = st.number_input("Pareggi (D)", min_value=0, max_value=10, value=0, step=1)
            
        punti_totali = (vittorie * 3) + (pareggi * 1)
        st.markdown(f"**Calcolo Punteggio:** `{punti_totali} Punti` (3 per W, 1 per D)")
        
        submit_btn = st.form_submit_button("Salva nel Database 💾")
        
        if submit_btn:
            if not giocatore.strip():
                st.error("Il nome del giocatore non può essere vuoto!")
            else:
                # Inseriamo anche anno e season nella query SQL
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO risultati (anno, season, tappa, negozio, giocatore, mazzo, vittorie, sconfitte, pareggi, punteggio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (anno, season, tappa, negozio, giocatore, mazzo, vittorie, sconfitte, pareggi, punti_totali))
                conn.commit()
                conn.close()
                
                st.success(f"Dati inseriti con successo per {giocatore}!")
                st.rerun()