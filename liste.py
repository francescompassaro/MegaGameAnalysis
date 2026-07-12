import streamlit as st
import pandas as pd
import sqlite3

DB_FILE = "/data/lega_pauper.db"

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
    
    if tabella == "risultati" and "link_deck" in df.columns:
        df["link_deck"] = df["link_deck"].fillna("").astype(str)
        
    return df

st.title("Archivio Liste Mazzi divisi per Tappa")
st.write("Usa i selettori per scegliere l'evento e visualizzare tutti i mazzi che hanno preso parte alla tappa.")

df_risultati = carica_dati("risultati")

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
