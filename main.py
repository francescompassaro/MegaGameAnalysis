# 3. GESTIONE STATO DI LOGIN E NAVIGAZIONE
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "errore_login" not in st.session_state:
    st.session_state["errore_login"] = False

# Inizializziamo la pagina attiva di default al primo avvio
if "pagina_attiva" not in st.session_state:
    st.session_state["pagina_attiva"] = "Dashboard Pubblica"

# --- BARRA LATERALE ---
st.sidebar.title("🎮 Lega Pauper Capua")

# Accesso Amministratore
if not st.session_state["logged_in"]:
    st.sidebar.subheader("🔒 Accesso Admin")
    
    with st.sidebar.form(key="form_login"):
        password_input = st.text_input("Password", type="password")
        bottone_accedi = st.form_submit_button("Accedi")
        
        if bottone_accedi:
            if password_input == PASSWORD_ADMIN:
                st.session_state["logged_in"] = True
                st.session_state["errore_login"] = False
                st.toast("Accesso effettuato! 🎉")
                st.rerun()
            else:
                st.session_state["errore_login"] = True

    if st.session_state["errore_login"]:
        st.sidebar.error("Password errata!")
        st.session_state["errore_login"] = False
else:
    st.sidebar.success("👨‍💻 Modalità Admin Attiva")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["pagina_attiva"] = "Dashboard Pubblica" # Forza il ritorno alla home
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📍 Sezioni")

# Generiamo la lista di pagine cliccabili verticali
if st.sidebar.button("🏆 Dashboard Pubblica", use_container_width=True, type="secondary" if st.session_state["pagina_attiva"] != "Dashboard Pubblica" else "primary"):
    st.session_state["pagina_attiva"] = "Dashboard Pubblica"
    st.rerun()

if st.sidebar.button("🃏 Liste per Tappa", use_container_width=True, type="secondary" if st.session_state["pagina_attiva"] != "Liste per Tappa" else "primary"):
    st.session_state["pagina_attiva"] = "Liste per Tappa"
    st.rerun()

if st.session_state["logged_in"]:
    if st.sidebar.button("📝 Inserisci Nuovi Dati", use_container_width=True, type="secondary" if st.session_state["pagina_attiva"] != "Inserisci Nuovi Dati" else "primary"):
        st.session_state["pagina_attiva"] = "Inserisci Nuovi Dati"
        st.rerun()

# Assegniamo la pagina attiva alla variabile menu per far girare i vecchi controlli del codice
menu = st.session_state["pagina_attiva"]

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

        # --- SEZIONE PODIO ---
        st.subheader("🥇 Il Podio Attuale")
        col_p1, col_p2, col_p3 = st.columns(3)
        if len(df_classifica_totale) >= 1:
            col_p1.metric(label="1° Posto 🥇", value=df_classifica_totale.iloc[0]["giocatore"], delta=f"{int(df_classifica_totale.iloc[0]['punteggio'])} PT")
        if len(df_classifica_totale) >= 2:
            col_p2.metric(label="2° Posto 🥈", value=df_classifica_totale.iloc[1]["giocatore"], delta=f"{int(df_classifica_totale.iloc[1]['punteggio'])} PT")
        if len(df_classifica_totale) >= 3:
            col_p3.metric(label="3° Posto 🥉", value=df_classifica_totale.iloc[2]["giocatore"], delta=f"{int(df_classifica_totale.iloc[2]['punteggio'])} PT")
            
        st.markdown("---")

        # --- CLASSIFICA GENERALE VS METASHARE GLOBALE ---
        st.header("🌐 Panoramica Generale")
        col_glob1, col_glob2 = st.columns([4, 3])
        with col_glob1:
            st.subheader("📋 Classifica Generale Completa")
            df_classifica_vis = df_classifica_totale[['Pos', 'giocatore', 'punteggio']].rename(columns={'giocatore': 'Giocatore', 'punteggio': 'Punti Totali'})
            df_classifica_filtrata = filter_dataframe(df_classifica_vis, key="generale")
            st.dataframe(df_classifica_filtrata, width="stretch", hide_index=True, height=380)
            
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
        st.header("🎯 Dettaglio Singola Tappa")
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
            st.subheader(f"📊 Classifica Ordinata - Tappa {tappa_scelta}")
            df_tappa_vis = df_tappa[['Pos Tappa', 'giocatore', 'mazzo', 'punteggio']].rename(columns={'giocatore': 'Giocatore', 'mazzo': 'Mazzo', 'punteggio': 'Punti Tappa'})
            df_tappa_filtrata = filter_dataframe(df_tappa_vis, key="tappa")
            st.dataframe(df_tappa_filtrata, width="stretch", hide_index=True, height=350)
            
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
        
        st.subheader("📋 Registro Storico di Tutti i Match Inseriti")
        df_visualizzazione = df_risultati[['tappa', 'negozio', 'giocatore', 'mazzo', 'vittorie', 'sconfitte', 'pareggi', 'punteggio']].copy()
        df_visualizzazione.columns = ['Tappa', 'Negozio', 'Giocatore', 'Mazzo Giocato', 'W', 'L', 'D', 'Punti']
        df_registro_filtrato = filter_dataframe(df_visualizzazione, key="storico")
        st.dataframe(df_registro_filtrato, width="stretch", hide_index=True)

# --- 5. PAGINA: LISTE PER TAPPA ---
elif menu == "Liste per Tappa":
    st.title("🃏 Archivio Liste Mazzi divisi per Tappa")
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
            st.subheader(f"📊 Elenco Mazzi e Link - Tappa {tappa_l_scelta} [{season_l_scelta} ({anno_l_scelto})]")
            
            h_l1, h_l2, h_l3, h_l4 = st.columns([1, 3, 3, 2])
            h_l1.markdown("**Pos**")
            h_l2.markdown("**Giocatore**")
            h_l3.markdown("**Mazzo/Archetipo**")
            h_l4.markdown("**Lista Condivisa**")
            st.markdown("<hr style='margin: 5px 0px; border-color: #333;'>", unsafe_allow_html=True)
            
            for index, row in df_evento_scelto.iterrows():
                r_l1, r_l2, r_l3, r_l4 = st.columns([1, 3, 3, 2])
                r_l1.write(f"**{index + 1}°**")
                r_l2.write(row["giocatore"])
                r_l3.write(row["mazzo"])
                
                if str(row["link_deck"]).strip() != "":
                    r_l4.link_button("Vedi Lista 🌐", row["link_deck"], width="stretch", type="secondary")
                else:
                    r_l4.write("*Nessuna lista caricata*")
                st.markdown("<hr style='margin: 8px 0px; border-color: #f0f2f6;'>", unsafe_allow_html=True)

# --- 6. PAGINA: INSERIMENTO DATI (ADMIN) ---
elif menu == "Inserisci Nuovi Dati":
    # Resto del codice per l'inserimento dei dati...
