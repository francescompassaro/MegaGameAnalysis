import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

def filter_dataframe(df: pd.DataFrame, key: str = "default") -> pd.DataFrame:
    """
    Aggiunge una UI di filtraggio dinamico sopra la tabella.
    L'utente puo scegliere su quale colonna applicare il filtro.
    """
    modify = st.checkbox("Attiva Filtri Avanzati per Colonna", key=f"mod_{key}")
    if not modify:
        return df

    df = df.copy()
    to_filter_columns = st.multiselect("Scegli le colonne da filtrare:", df.columns, key=f"cols_{key}")
    
    for column in to_filter_columns:
        left, right = st.columns((1, 3))
        if is_object_dtype(df[column]):
            user_text_input = right.text_input(
                f"Cerca nel testo di '{column}':",
                key=f"filter_{column}_{key}",
            )
            if user_text_input:
                df = df[df[column].astype(str).str.contains(user_text_input, case=False)]
        elif is_numeric_dtype(df[column]):
            min_val = int(df[column].min()) if not df[column].empty else 0
            max_val = int(df[column].max()) if not df[column].empty else 0
            if min_val == max_val:
                max_val += 1
            user_num_input = right.slider(
                f"Filtra intervallo per '{column}':",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                key=f"filter_{column}_{key}",
            )
            df = df[(df[column] >= user_num_input[0]) & (df[column] <= user_num_input[1])]
            
    return df

# 1. IMPOSTAZIONI PAGINA
st.set_page_config(page_title="Lega Pauper Capua", layout="wide", page_icon="🏆")

DB_FILE = "/data/lega_pauper.db"
PASSWORD_ADMIN = os.getenv("ADMIN_PASSWORD", "pauper_default")

# 2. INIZIALIZZAZIONE DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tabella Risultati Match
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
    
    # Migrazione dinamica: aggiunge la colonna link_deck se non esiste nel DB precedente
    cursor.execute("PRAGMA table_info(risultati)")
    colonne = [col[1] for col in cursor.fetchall()]
    if "link_deck" not in colonne:
        cursor.execute("ALTER TABLE risultati ADD COLUMN link_deck TEXT DEFAULT ''")
        
    # Tabella Giocatori Anagrafica
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giocatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    # Tabella Mazzi/Archetipi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mazzi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    
    # Inserimento Mazzi di Default se la tabella è vuota al primo avvio
    cursor.execute("SELECT COUNT(*) FROM mazzi")
    if cursor.fetchone()[0] == 0:
        mazzi_default = [
            "Abzan En Kor", "Azorius Familiars", "Bogles", "Boros Gates", "Boros Synthesizer",  
            "Boros Tribe", "Caw-Gate", "Dimir Faeries", "Dimir Terror", "Dimir Control",  
            "Elves", "Flicker Tron", "Golgari Gardens", "Bant Gardens", "Grixis Affinity",  
            "Gruul Monster", "Gruul Ponza", "Infect MonoGreen", "Infect Simic", "Izzet Skred",  
            "Jeskai Ephemerate", "Jund Evolution", "Jund Wildfire", "Kuldotha Burn",  
            "Mardu Synthesis", "Monoblue Faeries", "Monoblue Terror", "Monored Madness",  
            "Monored Rally", "Monowhite Heroic", "Monowhite Weenie", "Orzhov Blade",  
            "Petitioners Mill", "Spy Combo", "Slivers", "Tortured Existence",  
            "UG Turbofog", "Walls Combo", "WB Skyblade", "Naya Gates", "Monster Tron", "Rakdos Madness"
        ]
        cursor.executemany("INSERT INTO mazzi (nome) VALUES (?)", [(m,) for m in mazzi_default])
        
    conn.commit()
    conn.close()

def inserisci_risultato(anno, season, tappa, negozio, giocatore, mazzo, v, s, p, punti, link_deck):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO risultati (anno, season, tappa, negozio, giocatore, mazzo, vittorie, sconfitte, pareggi, punteggio, link_deck)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (anno, season, tappa, negozio, giocatore, mazzo, v, s, p, punti, link_deck))
    conn.commit()
    conn.close()

def carica_dati(tabella):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {tabella}", conn)
    conn.close()
    
    if tabella == "risultati" and "link_deck" in df.columns:
        df["link_deck"] = df["link_deck"].fillna("").astype(str)
        
    return df

init_db()
df_risultati = carica_dati("risultati")

# 3. GESTIONE STATO DI LOGIN E NAVIGAZIONE
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "errore_login" not in st.session_state:
    st.session_state["errore_login"] = False

if "pagina_attiva" not in st.session_state:
    st.session_state["pagina_attiva"] = "Dashboard Pubblica"

# --- BARRA LATERALE ---
st.sidebar.title("Lega Pauper Capua")

# Accesso Amministratore
if not st.session_state["logged_in"]:
    st.sidebar.subheader("Accesso Admin")
    
    with st.sidebar.form(key="form_login"):
        password_input = st.text_input("Password", type="password")
        bottone_accedi = st.form_submit_button("Accedi")
        
        if bottone_accedi:
            if password_input == PASSWORD_ADMIN:
                st.session_state["logged_in"] = True
                st.session_state["errore_login"] = False
                st.toast("Accesso effettuato!")
                st.rerun()
            else:
                st.session_state["errore_login"] = True

    if st.session_state["errore_login"]:
        st.sidebar.error("Password errata!")
        st.session_state["errore_login"] = False
else:
    st.sidebar.success("Modalita Admin Attiva")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["pagina_attiva"] = "Dashboard Pubblica"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Navigazione")

# Elenco verticale di pagine cliccabili stabili e pulite
if st.sidebar.button("Dashboard Pubblica", use_container_width=True, type="secondary" if st.session_state["pagina_attiva"] != "Dashboard Pubblica" else "primary"):
    st.session_state["pagina_attiva"] = "Dashboard Pubblica"
    st.rerun()

if st.sidebar.button("Liste per Tappa", use_container_width=True, type="secondary" if st.session_state["pagina_attiva"] != "Liste per Tappa" else "primary"):
    st.session_state["pagina_attiva"] = "Liste per Tappa"
    st.rerun()

if st.session_state["logged_in"]:
    if st.sidebar.button("Inserisci Nuovi Dati", use_container_width=True, type="secondary" if st.session_state["pagina_attiva"] != "Inserisci Nuovi Dati" else "primary"):
        st.session_state["pagina_attiva"] = "Inserisci Nuovi Dati"
        st.rerun()

menu = st.session_state["pagina_attiva"]

# --- 4. PAGINA: DASHBOARD PUBBLICA ---
if menu == "Dashboard Pubblica":
    st.title("Lega Pauper Capua - Road to Lucca")
    
    if df_risultati.empty:
        st.info("Nessun dato presente nel database. Accedi come admin nella barra laterale per inserire i risultati della prima tappa!")
    else:
        # --- ELABORAZIONE DATI CLASSIFICA ---
        df_classifica_totale = df_risultati.groupby("giocatore")["punteggio"].sum().reset_index()
        df_classifica_totale = df_classifica_totale.sort_values(by="punteggio", ascending=False).reset_index(drop=True)
        df_classifica_totale.index += 1
        df_classifica_totale.index.name = "Pos"
        df_classifica_totale = df_classifica_totale.reset_index()

        # --- SEZIONE PODIO ---
        st.subheader("Il Podio Attuale")
        col_p1, col_p2, col_p3 = st.columns(3)
        if len(df_classifica_totale) >= 1:
            col_p1.metric(label="1 Posto", value=df_classifica_totale.iloc[0]["giocatore"], delta=f"{int(df_classifica_totale.iloc[0]['punteggio'])} PT")
        if len(df_classifica_totale) >= 2:
            col_p2.metric(label="2 Posto", value=df_classifica_totale.iloc[1]["giocatore"], delta=f"{int(df_classifica_totale.iloc[1]['punteggio'])} PT")
        if len(df_classifica_totale) >= 3:
            col_p3.metric(label="3 Posto", value=df_classifica_totale.iloc[2]["giocatore"], delta=f"{int(df_classifica_totale.iloc[2]['punteggio'])} PT")
            
        st.markdown("---")

        # --- CLASSIFICA GENERALE VS METASHARE GLOBALE ---
        st.header("Panoramica Generale")
        col_glob1, col_glob2 = st.columns([4, 3])
        with col_glob1:
            st.subheader("Classifica Generale Completa")
            df_classifica_vis = df_classifica_totale[['Pos', 'giocatore', 'punteggio']].rename(columns={'giocatore': 'Giocatore', 'punteggio': 'Punti Totali'})
            df_classifica_filtrata = filter_dataframe(df_classifica_vis, key="generale")
            st.dataframe(df_classifica_filtrata, width="stretch", hide_index=True, height=380)
            
        with col_glob2:
            st.subheader("Metashare Globale (Mazzi Giocati)")
            df_meta_glob = df_risultati.groupby("mazzo").size().reset_index(name="Presenze")
            fig_pie_glob = px.pie(
                df_meta_glob, 
                names="mazzo", 
                values="Presenze", 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie_glob.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="top", 
                    y=1.0, 
                    xanchor="left", 
                    x=1.02
                ),
                height=420,
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_pie_glob, width="stretch")
            
        st.markdown("---")
        
        # --- SELETTORE A CASCATA TAPPA ---
        st.header("Dettaglio Singola Tappa")
        col_sel1, col_sel2, col_sel3 = st.columns(3)
        with col_sel1:
            anni_disponibili = sorted(df_risultati["anno"].unique(), reverse=True)
            anno_scelto = st.selectbox("Seleziona Anno:", anni_disponibili, index=0)
            df_filtrato_anno = df_risultati[df_risultati["anno"] == anno_scelto]
        with col_sel2:
            season_disponibili = sorted(df_filtrato_anno["season"].unique())
            season_scelta = st.selectbox("Seleziona Season:", season_disponibili, index=0)
            df_filtrato_season = df_filtrato_anno[df_filtrato_anno["season"] == season_scelta]
        with col_sel3:
            tappe_disponibili = sorted(df_filtrato_season["tappa"].unique())
            tappa_scelta = st.selectbox("Seleziona Tappa:", tappe_disponibili, index=len(tappe_disponibili)-1 if tappe_disponibili else 0)
        
        df_tappa = df_risultati[(df_risultati["anno"] == anno_scelto) & (df_risultati["season"] == season_scelta) & (df_risultati["tappa"] == tappa_scelta)].sort_values(by="punteggio", ascending=False).reset_index(drop=True)
        df_tappa.index += 1
        df_tappa.index.name = "Pos Tappa"
        df_tappa = df_tappa.reset_index()

        col_tappa1, col_tappa2 = st.columns([4, 3])
        with col_tappa1:
            st.subheader(f"Classifica Ordinata - Tappa {tappa_scelta}")
            df_tappa_vis = df_tappa[['Pos Tappa', 'giocatore', 'mazzo', 'punteggio']].rename(columns={'giocatore': 'Giocatore', 'mazzo': 'Mazzo', 'punteggio': 'Punti Tappa'})
            df_tappa_filtrata = filter_dataframe(df_tappa_vis, key="tappa")
            st.dataframe(df_tappa_filtrata, width="stretch", hide_index=True, height=350)
            
        with col_tappa2:
            st.subheader(f"Metashare - Tappa {tappa_scelta}")
            df_meta_tappa = df_tappa.groupby("mazzo").size().reset_index(name="Presenze")
            fig_pie_tappa = px.pie(
                df_meta_tappa, 
                names="mazzo", 
                values="Presenze", 
                hole=0.4, 
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie_tappa.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="top", 
                    y=1.0, 
                    xanchor="left", 
                    x=1.02
                ),
                height=420,
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_pie_tappa, width="stretch")
            
        st.markdown("---")
        
        st.subheader("Registro Storico di Tutti i Match Inseriti")
        df_visualizzazione = df_risultati[['tappa', 'negozio', 'giocatore', 'mazzo', 'vittorie', 'sconfitte', 'pareggi', 'punteggio']].copy()
        df_visualizzazione.columns = ['Tappa', 'Negozio', 'Giocatore', 'Mazzo Giocato', 'W', 'L', 'D', 'Punti']
        df_registro_filtrato = filter_dataframe(df_visualizzazione, key="storico")
        st.dataframe(df_registro_filtrato, width="stretch", hide_index=True)

# --- 5. PAGINA: LISTE PER TAPPA ---
elif menu == "Liste per Tappa":
    st.title("Archivio Liste Mazzi divisi per Tappa")
    st.write("Usa i selettori per scegliere l'evento e visualizzare tutti i mazzi che hanno preso parte alla tappa.")
    
    if df_risultati.empty:
        st.info("Nessun dato presente nel database. Inserisci prima qualche risultato.")
    else:
        st.markdown("---")
        col_p_sel1, col_p_sel2, col_p_sel3 = st.columns(3)
        with col_p_sel1:
            anni_liste = sorted(df_risultati["anno"].unique(), reverse=True)
            anno_l_scelto = st.selectbox("Anno dell'evento:", anni_liste, index=0, key="anno_liste_page")
            df_l_anno = df_risultati[df_risultati["anno"] == anno_l_scelto]
        with col_p_sel2:
            season_liste = sorted(df_l_anno["season"].unique())
            season_l_scelta = st.selectbox("Season dell'evento:", season_liste, index=0, key="season_liste_page")
            df_l_season = df_l_anno[df_l_anno["season"] == season_l_scelta]
        with col_p_sel3:
            tappe_liste = sorted(df_l_season["tappa"].unique())
            tappa_l_scelta = st.selectbox("Numero Tappa:", tappe_liste, index=len(tappe_liste)-1 if tappe_liste else 0, key="tappa_liste_page")
            
        df_evento_scelto = df_risultati[
            (df_risultati["anno"] == anno_l_scelto) & 
            (df_risultati["season"] == season_l_scelta) & 
            (df_risultati["tappa"] == tappa_l_scelta)
        ].sort_values(by="punteggio", ascending=False).reset_index(drop=True)
        
        if df_evento_scelto.empty:
            st.warning("Nessun dato inserito per questa combinazione.")
        else:
            st.subheader(f"Elenco Mazzi e Link - Tappa {tappa_l_scelta} [{season_l_scelta} ({anno_l_scelto})]")
            
            h_l1, h_l2, h_l3, h_l4 = st.columns([1, 3, 3, 2])
            h_l1.markdown("**Pos**")
            h_l2.markdown("**Giocatore**")
            h_l3.markdown("**Mazzo/Archetipo**")
            h_l4.markdown("**Lista Condivisa**")
            st.markdown("<hr style='margin: 5px 0px; border-color: #333;'>", unsafe_allow_html=True)
            
            for index, row in df_evento_scelto.iterrows():
                r_l1, r_l2, r_l3, r_l4 = st.columns([1, 3, 3, 2])
                r_l1.write(f"**{index + 1}**")
                r_l2.write(row["giocatore"])
                r_l3.write(row["mazzo"])
                
                if str(row["link_deck"]).strip() != "":
                    r_l4.link_button("Vedi Lista", row["link_deck"], width="stretch", type="secondary")
                else:
                    r_l4.write("*Nessuna lista caricata*")
                st.markdown("<hr style='margin: 8px 0px; border-color: #f0f2f6;'>", unsafe_allow_html=True)

# --- 6. PAGINA: INSERIMENTO DATI (ADMIN) ---
elif menu == "Inserisci Nuovi Dati":
    st.title("Pannello Amministratore")
    
    df_risultati = carica_dati("risultati")
    df_giocatori_db = carica_dati("giocatori")
    df_mazzi_db = carica_dati("mazzi")
    
    lista_giocatori = sorted(df_giocatori_db["nome"].tolist())
    lista_mazzi = sorted(df_mazzi_db["nome"].tolist())
    
    tab_risultati, tab_gestione_player, tab_gestione_deck = st.tabs([
        "Inserisci Punti Tappa", "Gestione Giocatori", "Gestione Mazzi/Archetipi"
    ])
    
    with tab_risultati:
        st.header("Match Risultati")
        ELENCO_NEGOZI = ["Magicomix"]
        
        if not lista_giocatori or not lista_mazzi:
            st.warning("Per favor, inserisci almeno un giocatore e un mazzo nei Tab a fianco prima di registrare un match!")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                anno = st.selectbox("Anno della Season", [2026, 2027, 2025])
                season = st.selectbox("Nome Season", ["Stagione 1", "Stagione 2", "Stagione 3", "Winter", "Spring", "Summer", "Autumn"])
                tappa = st.number_input("Numero Tappa", min_value=1, max_value=50, value=1, step=1)
            with col_f2:
                negozio = st.selectbox("Negozio ospitante", ELENCO_NEGOZI)
                giocatore = st.selectbox("Seleziona Giocatore", lista_giocatori)
                mazzo = st.selectbox("Seleziona Archetipo", lista_mazzi)
            with col_f3:
                vittorie = st.number_input("Vittorie (W)", min_value=0, max_value=10, value=0, step=1)
                sconfitte = st.number_input("Sconfitte (L)", min_value=0, max_value=10, value=0, step=1)
                pareggi = st.number_input("Pareggi (D)", min_value=0, max_value=10, value=0, step=1)
                
            link_deck_input = st.text_input("Link della lista mazzo (MTGDecks / Moxfield / ecc.) - Opzionale", placeholder="https://mtgdecks.net/Pauper/...")
            
            punti_totali = (vittorie * 3) + (pareggi * 1)
            st.markdown(f"**Calcolo Punteggio:** `{punti_totali} Punti` (3 per W, 1 per D)")
            
            if st.button("Salva nel Database", key="save_match_btn"):
                inserisci_risultato(anno, season, tappa, negozio, giocatore, mazzo, vittorie, sconfitte, pareggi, punti_totali, link_deck_input.strip())
                st.success(f"Dati inseriti con successo per {giocatore}!")
                st.rerun()
                
        st.markdown("---")
        st.subheader("Tabella di Eliminazione Rapida Match (Ultimi 2 record inseriti)")
        if df_risultati.empty:
            st.info("Nessun match presente nel registro storicizzato.")
        else:
            df_ultimi_record = df_risultati.sort_values(by="id", ascending=False).head(2)
            h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([1, 2, 3, 3, 1, 1])
            h_col1.markdown("**Tappa**")
            h_col2.markdown("**Season**")
            h_col3.markdown("**Giocatore**")
            h_col4.markdown("**Mazzo**")
            h_col5.markdown("**Punti**")
            h_col6.markdown("**Azione**")
            
            for index, row in df_ultimi_record.iterrows():
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([1, 2, 3, 3, 1, 1])
                r_col1.write(f"Tappa {row['tappa']}")
                r_col2.write(f"{row['season']} ({row['anno']})")
                r_col3.write(row['giocatore'])
                r_col4.write(row['mazzo'])
                r_col5.write(str(row['punteggio']))
                if r_col6.button("Elimina", key=f"del_match_{row['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM risultati WHERE id = ?", (int(row['id']),))
                    conn.commit()
                    conn.close()
                    st.success(f"Match di {row['giocatore']} d'ufficio eliminato!")
                    st.rerun()

    # --- TAB 2: GESTIONE GIOCATORI ---
    with tab_gestione_player:
        st.header("Anagrafica Giocatori")
        col_p_ins, col_p_mod = st.columns(2)
        with col_p_ins:
            st.subheader("Aggiungi Nuovo Giocatore")
            nuovo_giocatore = st.text_input("Nome e Cognome", key="new_player").strip()
            if st.button("Salva Giocatore"):
                if nuovo_giocatore:
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO giocatori (nome) VALUES (?)", (nuovo_giocatore,))
                        conn.commit()
                        conn.close()
                        st.success(f"{nuovo_giocatore} aggiunto!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Questo giocatore esiste gia!")
                else:
                    st.error("Il nome del giocatore non puo essere vuoto.")
        with col_p_mod:
            st.subheader("Modifica Giocatore Esistente")
            if lista_giocatori:
                player_da_modificare = st.selectbox("Seleziona Giocatore da modificare:", lista_giocatori, key="sel_player_mod")
                nuovo_nome_player = st.text_input("Nuovo Nome e Cognome:", value=player_da_modificare)
                if st.button("Aggiorna Giocatore"):
                    if nuovo_nome_player.strip():
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE giocatori SET nome = ? WHERE nome = ?", (nuovo_nome_player.strip(), player_da_modificare))
                        cursor.execute("UPDATE risultati SET giocatore = ? WHERE giocatore = ?", (nuovo_nome_player.strip(), player_da_modificare))
                        conn.commit()
                        conn.close()
                        st.success("Aggiornato con successo!")
                        st.rerun()
            else:
                st.info("Nessun giocatore registrato.")
                
        st.markdown("---")
        st.subheader("Lista Giocatori Registrati ed Eliminazione")
        if not df_giocatori_db.empty:
            for index, row in df_giocatori_db.sort_values(by="nome").iterrows():
                p_col1, p_col2 = st.columns([5, 1])
                p_col1.write(f"Giocatore: {row['nome']}")
                if p_col2.button("Rimuovi", key=f"del_player_{row['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM giocatori WHERE id = ?", (int(row['id']),))
                    conn.commit()
                    conn.close()
                    st.success(f"Giocatore '{row['nome']}' rimosso!")
                    st.rerun()

    # --- TAB 3: GESTIONE DECK ---
    with tab_gestione_deck:
        st.header("Anagrafica Mazzi/Archetipi")
        col_d_ins, col_d_mod = st.columns(2)
        with col_d_ins:
            st.subheader("Aggiungi Nuovo Archetipo")
            nuovo_mazzo = st.text_input("Nome Archetipo (es. Eldrazi Tron)", key="new_deck").strip()
            if st.button("Salva Mazzo"):
                if nuovo_mazzo:
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO mazzi (nome) VALUES (?)", (nuovo_mazzo,))
                        conn.commit()
                        conn.close()
                        st.success(f"Archetipo '{nuovo_mazzo}' salvato!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Questo mazzo esiste gia!")
                else:
                    st.error("Il nome del mazzo non puo essere vuoto.")
        with col_d_mod:
            st.subheader("Modifica Archetipo Esistente")
            if lista_mazzi:
                mazzo_da_modificare = st.selectbox("Seleziona Archetipo da modificare:", lista_mazzi, key="sel_deck_mod")
                nuovo_nome_mazzo = st.text_input("Nuovo Nome Archetipo:", value=mazzo_da_modificare)
                if st.button("Aggiorna Archetipo"):
                    if nuovo_nome_mazzo.strip():
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE mazzi SET nome = ? WHERE nome = ?", (nuovo_nome_mazzo.strip(), mazzo_da_modificare))
                        cursor.execute("UPDATE risultati SET mazzo = ? WHERE mazzo = ?", (nuovo_nome_mazzo.strip(), mazzo_da_modificare))
                        conn.commit()
                        conn.close()
                        st.success("Archetipo aggiornato!")
                        st.rerun()
            else:
                st.info("Nessun mazzo configurato.")
                
        st.markdown("---")
        st.subheader("Lista Archetipi Registrati ed Eliminazione")
        if not df_mazzi_db.empty:
            mazzi_ordinati = df_mazzi_db.sort_values(by="nome")
            chunks = [mazzi_ordinati[i:i + 3] for i in range(0, len(mazzi_ordinati), 3)]
            for chunk in chunks:
                cols_deck = st.columns(3)
                for i, (idx, row) in enumerate(chunk.iterrows()):
                    with cols_deck[i]:
                        sub_col1, sub_col2 = st.columns([4, 1])
                        sub_col1.write(f"Mazzo: {row['nome']}")
                        if sub_col2.button("Rimosso", key=f"del_deck_{row['id']}"):
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM mazzi WHERE id = ?", (int(row['id']),))
                            conn.commit()
                            conn.close()
                            st.success(f"Mazzo '{row['nome']}' rimosso!")
                            st.rerun()

    # --- GESTIONE FILES (BACKUP & RIPRISTINO) ---
    st.markdown("---")
    col_back1, col_back2 = st.columns(2)
    with col_back1:
        st.subheader("Backup del Database")
        st.write("Scarica una copia di sicurezza di lega_pauper.db.")
        try:
            with open(DB_FILE, "rb") as file:
                db_bytes = file.read()
            st.download_button(label="Scarica Database (.db)", data=db_bytes, file_name="lega_pauper_backup.db", mime="application/x-sqlite3")
        except FileNotFoundError:
            st.error("Il file del database non esiste ancora.")
    with col_back2:
        st.subheader("Ripristina Database")
        st.write("Carica un file di backup per sovrascrivere i dati correnti.")
        uploaded_db = st.file_uploader("Scegli un file .db", type=["db"])
        if uploaded_db is not None:
            if st.button("Conferma e Sovrascrivi", type="primary"):
                try:
                    with open(DB_FILE, "wb") as f:
                        f.write(uploaded_db.read())
                    st.success("Database ripristinato con successo!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")
