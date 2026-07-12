import streamlit as st
import pandas as pd
import sqlite3

# Blocco di sicurezza e controllo autorizzazioni
if not st.session_state.get("logged_in", False):
    st.warning("Accesso negato. Autenticati nella barra laterale.")
    st.stop()

DB_FILE = "/data/lega_pauper.db"

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
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {tabella}")
    righe = cursor.fetchall()
    colonne = [col[0] for col in cursor.description]
    conn.close()
    
    if not righe:
        return pd.DataFrame(columns=colonne)
    
    dati_mappati = {col: [] for col in colonne}
    for riga in righe:
        for i, valore in enumerate(riga):
            dati_mappati[colonne[i]].append(valore)
            
    df = pd.DataFrame(dati_mappati)
    
    colonne_testo = ["giocatore", "mazzo", "season", "negozio", "link_deck", "nome"]
    for col in colonne_testo:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            
    return df

st.title("Pannello Amministratore")

df_risultati = carica_dati("risultati")
df_giocatori_db = carica_dati("giocatori")
df_mazzi_db = carica_dati("mazzi")

lista_giocatori = sorted(df_giocatori_db["nome"].tolist()) if not df_giocatori_db.empty else []
lista_mazzi = sorted(df_mazzi_db["nome"].tolist()) if not df_mazzi_db.empty else []

tab_risultati, tab_gestione_player, tab_gestione_deck = st.tabs([
    "Inserisci Punti Tappa", "Gestione Giocatori", "Gestione Mazzi/Archetipi"
])

with tab_risultati:
    st.header("Match Risultati")
    ELENCO_NEGOZI = ["Magicomix"]
    
    if not lista_giocatori or not lista_mazzi:
        st.warning("Per favore, inserisci almeno un giocatore e un mazzo nei Tab a fianco prima di registrare un match!")
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
                st.success(f"Match di {row['giocatore']} eliminato!")
                st.rerun()

with tab_gestione_player:
    st.header("Gestione Giocatori")
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
                st.rerun()
            except Exception as e:
                st.error(f"Errore: {e}")
