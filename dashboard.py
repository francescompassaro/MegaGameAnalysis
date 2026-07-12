import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

DB_FILE = "/data/lega_pauper.db"

def filter_dataframe(df: pd.DataFrame, key: str = "default") -> pd.DataFrame:
    modify = st.checkbox("Attiva Filtri Avanzati per Colonna", key=f"mod_{key}")
    if not modify:
        return df

    df = df.copy()
    to_filter_columns = st.multiselect("Scegli le colonne da filtrare:", df.columns, key=f"cols_{key}")
    
    for column in to_filter_columns:
        left, right = st.columns((1, 3))
        if df[column].dtype == object or isinstance(df[column].dtype, pd.StringDtype):
            user_text_input = right.text_input(f"Cerca nel testo di '{column}':", key=f"filter_{column}_{key}")
            if user_text_input:
                df = df[df[column].astype(str).str.contains(user_text_input, case=False)]
        elif pd.api.types.is_numeric_dtype(df[column]):
            min_val = int(df[column].min()) if not df[column].empty else 0
            max_val = int(df[column].max()) if not df[column].empty else 0
            if min_val == max_val:
                max_val += 1
            user_num_input = right.slider(f"Filtra intervallo per '{column}':", min_value=min_val, max_value=max_val, value=(min_val, max_val), key=f"filter_{column}_{key}")
            df = df[(df[column] >= user_num_input[0]) & (df[column] <= user_num_input[1])]
            
    return df

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
    
    colonne_testo = ["giocatore", "mazzo", "season", "negozio", "link_deck"]
    for col in colonne_testo:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            
    return df

st.title("Lega Pauper Capua - Road to Lucca")
df_risultati = carica_dati("risultati")

if df_risultati.empty:
    st.info("Nessun dato presente nel database. Accedi come admin nella barra laterale per inserire i risultati della prima tappa!")
else:
    df_classifica_totale = df_risultati.groupby("giocatore")["punteggio"].sum().reset_index()
    df_classifica_totale = df_classifica_totale.sort_values(by="punteggio", ascending=False).reset_index(drop=True)
    df_classifica_totale.index += 1
    df_classifica_totale.index.name = "Pos"
    df_classifica_totale = df_classifica_totale.reset_index()

    st.subheader("Il Podio Attuale")
    col_p1, col_p2, col_p3 = st.columns(3)
    if len(df_classifica_totale) >= 1:
        col_p1.metric(label="1 Posto", value=df_classifica_totale.iloc[0]["giocatore"], delta=f"{int(df_classifica_totale.iloc[0]['punteggio'])} PT")
    if len(df_classifica_totale) >= 2:
        col_p2.metric(label="2 Posto", value=df_classifica_totale.iloc[1]["giocatore"], delta=f"{int(df_classifica_totale.iloc[1]['punteggio'])} PT")
    if len(df_classifica_totale) >= 3:
        col_p3.metric(label="3 Posto", value=df_classifica_totale.iloc[2]["giocatore"], delta=f"{int(df_classifica_totale.iloc[2]['punteggio'])} PT")
        
    st.markdown("---")

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
        fig_pie_glob = px.pie(df_meta_glob, names="mazzo", values="Presenze", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie_glob.update_layout(legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02), height=420, margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig_pie_glob, width="stretch")
        
    st.markdown("---")
    
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
        fig_pie_tappa = px.pie(df_meta_tappa, names="mazzo", values="Presenze", hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_pie_tappa.update_layout(legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02), height=420, margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig_pie_tappa, width="stretch")
        
    st.markdown("---")
    
    st.subheader("Registro Storico di Tutti i Match Inseriti")
    df_visualizzazione = df_risultati[['tappa', 'negozio', 'giocatore', 'mazzo', 'vittorie', 'sconfitte', 'pareggi', 'punteggio']].copy()
    df_visualizzazione.columns = ['Tappa', 'Negozio', 'Giocatore', 'Mazzo Giocato', 'W', 'L', 'D', 'Punti']
    df_registro_filtrato = filter_dataframe(df_visualizzazione, key="storico")
    st.dataframe(df_registro_filtrato, width="stretch", hide_index=True)
