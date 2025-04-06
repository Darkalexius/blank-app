import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json

from data_fetcher import fetch_cryptocurrency_data, get_available_cryptocurrencies, fetch_current_prices
from crypto_analysis import identify_promising_cryptocurrencies, generate_signals
from technical_indicators import calculate_technical_indicators
from utils import format_currency, get_price_change_color, format_date
import database
from database import (
    save_price_history,
    save_technical_indicators,
    save_signal,
    save_user_preference,
    get_user_preference,
    get_recent_signals,
    get_price_history
)
from exchange_connector import (
    get_available_exchanges, initialize_exchange, save_exchange_credentials,
    get_exchange_credentials, get_account_balance, place_market_order, place_limit_order,
    get_order_status, cancel_order, get_open_orders, get_order_history, get_ticker,
    get_available_pairs, save_order_to_db, update_order_status_in_db, get_orders_from_db
)
from ai_advisor import analyze_crypto_data, generate_investment_strategy, get_market_sentiment, ask_ai_advisor
from ia_agent import IAAgent

# Initialiser l'agent IA
ia_agent = IAAgent()

# Configuration de la page
st.set_page_config(
    page_title="Analyse de Cryptomonnaies",
    page_icon="📈",
    layout="wide",
)

# Titre et description
st.title("📊 Plateforme d'Analyse de Cryptomonnaies de Alexis Adinguera")
st.markdown("""
Cette application analyse les tendances des cryptomonnaies et identifie des opportunités
d'investissement en générant des signaux d'achat et de vente basés sur des indicateurs techniques.
""")

# Sidebar pour les options
st.sidebar.header("Options d'Analyse")

# Sélection de la période
time_periods = {
    "24 heures": "1d",
    "7 jours": "7d",
    "30 jours": "30d",
    "90 jours": "90d"
}
selected_period = st.sidebar.selectbox(
    "Période d'analyse",
    list(time_periods.keys()),
    index=1  # Default to 7 days
)

# Chargement des cryptomonnaies disponibles
try:
    available_cryptos = get_available_cryptocurrencies()
    
    # Sélection des cryptomonnaies à analyser
    default_cryptos = ["BTC", "ETH", "BNB", "XRP", "SOL"]
    selected_cryptos = st.sidebar.multiselect(
        "Sélectionner les cryptomonnaies à analyser",
        available_cryptos,
        default=default_cryptos
    )
    
    # Si aucune crypto n'est sélectionnée, utilisez les valeurs par défaut
    if not selected_cryptos:
        selected_cryptos = default_cryptos
        st.sidebar.warning("Aucune crypto sélectionnée, utilisation des valeurs par défaut.")

    # Sélection des indicateurs techniques
    technical_indicators = st.sidebar.multiselect(
        "Indicateurs techniques",
        ["RSI", "MACD", "Bollinger Bands", "EMA", "SMA"],
        default=["RSI", "MACD"]
    )

    # Bouton pour actualiser les données
    if st.sidebar.button("Actualiser les données"):
        st.rerun()

    # Affichage du dernier rafraîchissement
    st.sidebar.text(f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")

    # Chargement et analyse des données
    with st.spinner("Chargement des données des cryptomonnaies..."):
        # Obtenir la période en jours
        period = time_periods[selected_period]
        
        # Variable pour détecter si on utilise des données de démonstration
        using_demo_data = False
        
        # Récupérer les données pour chaque crypto sélectionnée
        all_crypto_data = {}
        for crypto in selected_cryptos:
            crypto_data = fetch_cryptocurrency_data(crypto, period)
            # Vérifier si le DataFrame est vide
            if not crypto_data.empty:
                all_crypto_data[crypto] = crypto_data
                
                # Vérifier si nous utilisons des données de démonstration (prix arrondis typiques des données générées)
                if abs(crypto_data['close'].iloc[-1] - round(crypto_data['close'].iloc[-1], 0)) < 0.0001:
                    using_demo_data = True
        
        # Identifier les cryptomonnaies prometteuses
        promising_cryptos = identify_promising_cryptocurrencies(all_crypto_data, technical_indicators)
        
        # Générer les signaux
        signals = generate_signals(all_crypto_data, technical_indicators)
        
        # Avertissement pour les données de démonstration
        if using_demo_data:
            st.warning("""
            **Mode démonstration activé** : L'API CoinGecko a atteint sa limite de requêtes. 
            Nous utilisons des données de démonstration générées localement. 
            Ces données ne reflètent pas les prix réels du marché mais vous permettent de continuer 
            à explorer l'application. Veuillez réessayer plus tard pour obtenir des données en temps réel.
            """)
            
            # Ajouter une indication du temps estimé avant que l'API soit à nouveau disponible
            current_time = datetime.now()
            # CoinGecko limite à 10-30 requêtes par minute pour les API gratuites
            next_available = current_time + timedelta(minutes=1)
            st.info(f"L'API devrait être à nouveau disponible vers {next_available.strftime('%H:%M')}.")

    # Tableau de bord principal
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Aperçu du Marché")
        
        # Créer un dataframe pour le tableau de marché
        market_data = []
        for crypto, data in all_crypto_data.items():
            if not data.empty:
                current_price = data['close'].iloc[-1]
                price_24h_ago = data['close'].iloc[-24] if len(data) > 24 else data['close'].iloc[0]
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                
                market_data.append({
                    "Crypto": crypto,
                    "Prix Actuel": format_currency(current_price),
                    "Changement (24h)": f"{change_24h:.2f}%",
                    "Volume (24h)": format_currency(data['volume'].iloc[-1]),
                    "Signal": signals[crypto]['signal'] if crypto in signals else "Neutre"
                })
        
        market_df = pd.DataFrame(market_data)
        
        # Appliquer une couleur conditionnelle
        def color_change(val):
            if "%" in str(val):
                try:
                    value = float(val.replace("%", ""))
                    if value > 0:
                        return 'background-color: rgba(0, 255, 0, 0.2)'
                    elif value < 0:
                        return 'background-color: rgba(255, 0, 0, 0.2)'
                except:
                    pass
            return ''
        
        def color_signal(val):
            if val == "Achat":
                return 'background-color: rgba(0, 255, 0, 0.3); color: darkgreen; font-weight: bold'
            elif val == "Vente":
                return 'background-color: rgba(255, 0, 0, 0.3); color: darkred; font-weight: bold'
            return ''
        
        # Afficher le tableau avec mise en forme
        st.dataframe(
            market_df.style
            .map(color_change, subset=['Changement (24h)'])
            .map(color_signal, subset=['Signal'])
        )

    with col2:
        st.header("Cryptomonnaies Prometteuses")
        
        if promising_cryptos:
            for idx, (crypto, score) in enumerate(promising_cryptos):
                st.markdown(f"**{idx+1}. {crypto}** - Score: {score:.2f}")
                if crypto in signals:
                    signal_color = "green" if signals[crypto]['signal'] == "Achat" else "red" if signals[crypto]['signal'] == "Vente" else "gray"
                    st.markdown(f"<span style='color:{signal_color};font-weight:bold;'>{signals[crypto]['signal']}</span> - {signals[crypto]['reason']}", unsafe_allow_html=True)
        else:
            st.info("Aucune cryptomonnaie particulièrement prometteuse n'a été identifiée pour le moment.")

    # Création des onglets principaux pour l'application
    main_tabs = st.tabs(["Analyse Graphique", "Trading", "Historique des Signaux", "Base de Données", "Conseiller IA", "Agent IA"])
    
    with main_tabs[0]:
        st.header("Analyse Graphique")
    
    selected_crypto_for_chart = st.selectbox(
        "Sélectionner une cryptomonnaie pour l'analyse graphique",
        selected_cryptos,
        key="crypto_chart_selector_main"
    )
    
    if selected_crypto_for_chart in all_crypto_data:
        df = all_crypto_data[selected_crypto_for_chart]
        
        if not df.empty:
            # Calculer les indicateurs techniques pour cette crypto
            df_with_indicators = calculate_technical_indicators(df)
            
            # Créer un onglet pour chaque type de graphique
            chart_tabs = st.tabs(["Prix", "Volume", "Indicateurs Techniques"])
            
            with chart_tabs[0]:
                # Graphique des prix
                fig = go.Figure()
                
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name="Prix"
                ))
                
                # Ajouter les moyennes mobiles si disponibles
                if 'EMA_20' in df_with_indicators.columns:
                    fig.add_trace(go.Scatter(
                        x=df_with_indicators.index,
                        y=df_with_indicators['EMA_20'],
                        mode='lines',
                        name='EMA 20'
                    ))
                
                if 'SMA_50' in df_with_indicators.columns:
                    fig.add_trace(go.Scatter(
                        x=df_with_indicators.index,
                        y=df_with_indicators['SMA_50'],
                        mode='lines',
                        name='SMA 50'
                    ))
                
                # Ajouter les bandes de Bollinger si disponibles
                if 'BB_upper' in df_with_indicators.columns:
                    fig.add_trace(go.Scatter(
                        x=df_with_indicators.index,
                        y=df_with_indicators['BB_upper'],
                        mode='lines',
                        line=dict(width=0.5, color='rgba(100, 100, 100, 0.3)'),
                        name='BB Upper'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_with_indicators.index,
                        y=df_with_indicators['BB_lower'],
                        mode='lines',
                        line=dict(width=0.5, color='rgba(100, 100, 100, 0.3)'),
                        fill='tonexty',
                        fillcolor='rgba(100, 100, 100, 0.1)',
                        name='BB Lower'
                    ))
                
                # Ajouter des marqueurs pour les signaux si disponibles
                if selected_crypto_for_chart in signals:
                    if signals[selected_crypto_for_chart]['signal'] == "Achat":
                        buy_points = df_with_indicators[df_with_indicators['signal'] == 1]
                        fig.add_trace(go.Scatter(
                            x=buy_points.index,
                            y=buy_points['close'],
                            mode='markers',
                            marker=dict(size=10, color='green', symbol='triangle-up'),
                            name='Signal d\'achat'
                        ))
                    elif signals[selected_crypto_for_chart]['signal'] == "Vente":
                        sell_points = df_with_indicators[df_with_indicators['signal'] == -1]
                        fig.add_trace(go.Scatter(
                            x=sell_points.index,
                            y=sell_points['close'],
                            mode='markers',
                            marker=dict(size=10, color='red', symbol='triangle-down'),
                            name='Signal de vente'
                        ))
                
                fig.update_layout(
                    title=f"{selected_crypto_for_chart} - Évolution du Prix",
                    xaxis_title="Date",
                    yaxis_title="Prix (USD)",
                    height=600,
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with chart_tabs[1]:
                # Graphique du volume
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name="Volume"
                ))
                
                fig.update_layout(
                    title=f"{selected_crypto_for_chart} - Volume d'échanges",
                    xaxis_title="Date",
                    yaxis_title="Volume (USD)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with chart_tabs[2]:
                # Graphiques des indicateurs techniques
                indicator_tabs = st.tabs([indicator for indicator in technical_indicators if indicator in ["RSI", "MACD", "Bollinger Bands"]])
                
                for i, indicator in enumerate([ind for ind in technical_indicators if ind in ["RSI", "MACD", "Bollinger Bands"]]):
                    with indicator_tabs[i]:
                        if indicator == "RSI" and "RSI" in df_with_indicators.columns:
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=df_with_indicators.index,
                                y=df_with_indicators['RSI'],
                                mode='lines',
                                name='RSI'
                            ))
                            
                            # Ajouter des lignes horizontales pour les niveaux de survente et surachat
                            fig.add_shape(
                                type="line",
                                x0=df_with_indicators.index[0],
                                y0=70,
                                x1=df_with_indicators.index[-1],
                                y1=70,
                                line=dict(color="red", width=2, dash="dash")
                            )
                            
                            fig.add_shape(
                                type="line",
                                x0=df_with_indicators.index[0],
                                y0=30,
                                x1=df_with_indicators.index[-1],
                                y1=30,
                                line=dict(color="green", width=2, dash="dash")
                            )
                            
                            fig.update_layout(
                                title=f"{selected_crypto_for_chart} - RSI (Relative Strength Index)",
                                xaxis_title="Date",
                                yaxis_title="RSI",
                                height=400,
                                yaxis=dict(range=[0, 100])
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.markdown("""
                            **Interprétation du RSI:**
                            - **RSI > 70:** Le marché est potentiellement en surachat (signal de vente)
                            - **RSI < 30:** Le marché est potentiellement en survente (signal d'achat)
                            """)
                            
                        elif indicator == "MACD" and all(x in df_with_indicators.columns for x in ['MACD', 'MACD_signal', 'MACD_hist']):
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=df_with_indicators.index,
                                    y=df_with_indicators['MACD'],
                                    mode='lines',
                                    name='MACD'
                                )
                            )
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=df_with_indicators.index,
                                    y=df_with_indicators['MACD_signal'],
                                    mode='lines',
                                    name='Signal'
                                )
                            )
                            
                            fig.add_trace(
                                go.Bar(
                                    x=df_with_indicators.index,
                                    y=df_with_indicators['MACD_hist'],
                                    name='Histogramme',
                                    marker_color=df_with_indicators['MACD_hist'].apply(
                                        lambda x: 'green' if x > 0 else 'red'
                                    )
                                ),
                                secondary_y=True
                            )
                            
                            fig.update_layout(
                                title=f"{selected_crypto_for_chart} - MACD (Moving Average Convergence Divergence)",
                                xaxis_title="Date",
                                height=400
                            )
                            
                            fig.update_yaxes(title_text="MACD & Signal", secondary_y=False)
                            fig.update_yaxes(title_text="Histogramme", secondary_y=True)
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.markdown("""
                            **Interprétation du MACD:**
                            - **MACD croise au-dessus du signal:** Signal d'achat potentiel
                            - **MACD croise en-dessous du signal:** Signal de vente potentiel
                            - **Histogramme positif (vert):** Tendance haussière
                            - **Histogramme négatif (rouge):** Tendance baissière
                            """)
                            
                        elif indicator == "Bollinger Bands" and all(x in df_with_indicators.columns for x in ['BB_upper', 'BB_middle', 'BB_lower']):
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=df_with_indicators.index,
                                y=df_with_indicators['close'],
                                mode='lines',
                                name='Prix de clôture'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=df_with_indicators.index,
                                y=df_with_indicators['BB_upper'],
                                mode='lines',
                                line=dict(width=1, color='rgba(100, 100, 100, 0.8)'),
                                name='Bande supérieure'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=df_with_indicators.index,
                                y=df_with_indicators['BB_middle'],
                                mode='lines',
                                line=dict(width=1, color='rgba(100, 100, 100, 0.5)'),
                                name='Moyenne mobile'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=df_with_indicators.index,
                                y=df_with_indicators['BB_lower'],
                                mode='lines',
                                line=dict(width=1, color='rgba(100, 100, 100, 0.8)'),
                                fill='tonexty',
                                fillcolor='rgba(100, 100, 100, 0.1)',
                                name='Bande inférieure'
                            ))
                            
                            fig.update_layout(
                                title=f"{selected_crypto_for_chart} - Bandes de Bollinger",
                                xaxis_title="Date",
                                yaxis_title="Prix (USD)",
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.markdown("""
                            **Interprétation des Bandes de Bollinger:**
                            - **Prix proche de la bande supérieure:** Marché potentiellement surévalué
                            - **Prix proche de la bande inférieure:** Marché potentiellement sous-évalué
                            - **Bandes qui se resserrent:** Préparation à un mouvement de prix significatif
                            - **Bandes qui s'élargissent:** Volatilité accrue
                            """)
        else:
            st.error(f"Aucune donnée disponible pour {selected_crypto_for_chart}")

    # Section Analyse et Conseils
    st.header("Analyse et Conseils")
    
    # Afficher les signaux avec explications détaillées
    for crypto, signal_info in signals.items():
        if crypto in selected_cryptos:
            signal_color = "green" if signal_info['signal'] == "Achat" else "red" if signal_info['signal'] == "Vente" else "gray"
            st.markdown(f"### {crypto}: <span style='color:{signal_color};'>{signal_info['signal']}</span>", unsafe_allow_html=True)
            
            st.markdown(f"**Raison:** {signal_info['reason']}")
            
            if 'details' in signal_info and signal_info['details']:
                with st.expander("Détails de l'analyse"):
                    for key, value in signal_info['details'].items():
                        st.markdown(f"- **{key}:** {value}")
            
            if 'advice' in signal_info:
                st.markdown(f"**Conseil:** {signal_info['advice']}")
            
            st.markdown("---")

    # Bas de page avec informations de non-responsabilité
    st.markdown("---")
    st.caption("""
    **Avertissement:** Cette application est fournie à titre informatif uniquement. Les signaux 
    générés ne constituent pas des conseils d'investissement. Les investissements en cryptomonnaies 
    comportent des risques. Faites vos propres recherches avant d'investir.
    """)

    # Sauvegarde dans la base de données
    # 1. Sauvegarde des prix historiques et indicateurs techniques
    for crypto, df in all_crypto_data.items():
        if not df.empty:
            # Sauvegarder l'historique des prix
            save_price_history(crypto, df)
            
            # Calculer et sauvegarder les indicateurs techniques
            df_with_indicators = calculate_technical_indicators(df)
            save_technical_indicators(crypto, df_with_indicators)
    
    # 2. Sauvegarde des signaux générés
    for crypto, signal_info in signals.items():
        if crypto in selected_cryptos:
            # Détails des indicateurs pour ce signal
            indicators_data = {}
            if 'details' in signal_info and signal_info['details']:
                indicators_data = signal_info['details']
            
            # Prix actuel pour cette crypto
            current_price = None
            if crypto in all_crypto_data and not all_crypto_data[crypto].empty:
                current_price = all_crypto_data[crypto]['close'].iloc[-1]
            
            # Sauvegarder le signal
            save_signal(
                symbol=crypto,
                signal_type=signal_info['signal'].lower(),
                reason=signal_info['reason'],
                indicators_data=indicators_data,
                price_at_signal=current_price
            )
    
    # 3. Sauvegarde des préférences utilisateur
    save_user_preference("selected_period", selected_period)
    save_user_preference("selected_cryptos", ",".join(selected_cryptos))
    save_user_preference("selected_indicators", ",".join(technical_indicators))
    
    # Contenu de l'onglet d'analyse graphique
    with main_tabs[0]:
        st.header("Analyse Graphique")
        
        selected_crypto_for_chart = st.selectbox(
            "Sélectionner une cryptomonnaie pour l'analyse graphique",
            selected_cryptos,
            key="crypto_chart_selector_tab"
        )
        
        if selected_crypto_for_chart in all_crypto_data:
            df = all_crypto_data[selected_crypto_for_chart]
            
            if not df.empty:
                # Calculer les indicateurs techniques pour cette crypto
                df_with_indicators = calculate_technical_indicators(df)
                
                # Créer un onglet pour chaque type de graphique
                chart_tabs = st.tabs(["Prix", "Volume", "Indicateurs Techniques"])
                
                # [Le reste du code pour l'analyse graphique reste inchangé]
    
    # Afficher les données de la base de données dans les onglets appropriés
    with main_tabs[1]:
        st.header("Trading")
        
        # Sélection de l'échange de crypto-monnaies
        exchanges = get_available_exchanges()
        selected_exchange = st.selectbox(
            "Choisir un échange",
            exchanges,
            index=0,
            key="exchange_selector"
        )
        
        # Afficher des informations sur l'échange sélectionné
        st.info(f"Vous avez sélectionné l'échange {selected_exchange}.")
        
        # Configuration de l'API
        api_key_provided = False
        
        with st.expander("Configuration de l'API"):
            saved_api_key, saved_api_secret = get_exchange_credentials(selected_exchange)
            
            if saved_api_key and saved_api_secret:
                st.success("Informations d'API déjà configurées.")
                api_key_provided = True
                if st.button("Modifier les informations d'API"):
                    saved_api_key, saved_api_secret = None, None
            
            if not (saved_api_key and saved_api_secret):
                with st.form("api_keys_form"):
                    api_key = st.text_input("Clé API", type="password")
                    api_secret = st.text_input("Secret API", type="password")
                    test_mode = st.checkbox("Mode Test (Sandbox)", value=True)
                    submit_button = st.form_submit_button("Sauvegarder")
                    
                if submit_button:
                    if api_key and api_secret:
                        save_exchange_credentials(selected_exchange, api_key, api_secret)
                        st.success("Informations d'API sauvegardées avec succès!")
                        api_key_provided = True
                        st.rerun()
                    else:
                        st.error("Veuillez fournir une clé API et un secret API.")
                
                if st.button("Sauvegarder"):
                    if api_key and api_secret:
                        save_exchange_credentials(selected_exchange, api_key, api_secret)
                        st.success("Informations d'API sauvegardées avec succès!")
                        api_key_provided = True
                        st.rerun()
                    else:
                        st.error("Veuillez fournir une clé API et un secret API.")
        
        # Initialisation de l'échange
        exchange = None
        if api_key_provided:
            with st.spinner("Connexion à l'échange..."):
                api_key, api_secret = get_exchange_credentials(selected_exchange)
                exchange = initialize_exchange(selected_exchange, api_key, api_secret, test_mode=True)
                
                if exchange:
                    st.success(f"Connecté avec succès à {selected_exchange}!")
                    
                    # Afficher le solde du compte
                    try:
                        st.subheader("Solde du compte")
                        balances = get_account_balance(exchange)
                        
                        if balances:
                            # Filtrer les soldes non-nuls
                            non_zero_balances = {k: v for k, v in balances.items() if v > 0}
                            
                            # Créer un DataFrame à partir des soldes
                            balance_data = [{"Devise": k, "Solde": v} for k, v in non_zero_balances.items()]
                            balance_df = pd.DataFrame(balance_data)
                            
                            if not balance_df.empty:
                                st.dataframe(balance_df, use_container_width=True)
                            else:
                                st.info("Aucun solde disponible.")
                        else:
                            st.info("Impossible de récupérer les soldes.")
                    except Exception as e:
                        st.error(f"Erreur lors de la récupération des soldes: {str(e)}")
                    
                    # Interface de trading
                    st.subheader("Passer un ordre")
                    
                    # Récupérer les paires disponibles
                    try:
                        available_pairs = get_available_pairs(exchange)
                        
                        if available_pairs:
                            # Sélectionner une paire
                            selected_pair = st.selectbox(
                                "Choisir une paire",
                                available_pairs,
                                index=0 if available_pairs else None,
                                key="pair_selector"
                            )
                            
                            # Obtenir des informations sur la paire sélectionnée
                            if selected_pair:
                                ticker_info = get_ticker(exchange, selected_pair)
                                
                                if ticker_info:
                                    current_price = ticker_info.get('last', 0)
                                    st.metric(
                                        "Prix Actuel",
                                        f"{current_price:.2f} {selected_pair.split('/')[-1]}",
                                        delta=f"{ticker_info.get('percentage', 0):.2f}%" if 'percentage' in ticker_info else None
                                    )
                                
                                # Type d'ordre
                                order_type = st.radio("Type d'ordre", ["Market", "Limit"], horizontal=True)
                                side = st.radio("Côté", ["Achat", "Vente"], horizontal=True)
                                
                                # Quantité
                                amount = st.number_input("Quantité", min_value=0.0, format="%.8f")
                                
                                # Prix limite (uniquement pour les ordres limites)
                                price = None
                                if order_type == "Limit":
                                    # Définir une valeur par défaut pour le prix limite
                                    default_price = float(ticker_info.get('last', 0)) if ticker_info and 'last' in ticker_info else 0.0
                                    price = st.number_input(
                                        "Prix Limite",
                                        min_value=0.0,
                                        value=default_price,
                                        format="%.8f"
                                    )
                                
                                # Confirmation de l'ordre
                                if st.button("Passer l'ordre"):
                                    if amount <= 0:
                                        st.error("Veuillez spécifier une quantité valide.")
                                    else:
                                        with st.spinner("Traitement de l'ordre..."):
                                            try:
                                                side_api = "buy" if side == "Achat" else "sell"
                                                
                                                if order_type == "Market":
                                                    order = place_market_order(exchange, selected_pair, side_api, amount)
                                                else:  # Limit
                                                    if price and price > 0:
                                                        order = place_limit_order(exchange, selected_pair, side_api, amount, price)
                                                    else:
                                                        st.error("Veuillez spécifier un prix limite valide.")
                                                        order = None
                                                
                                                if order:
                                                    st.success(f"Ordre placé avec succès: {order.get('id', 'N/A')}")
                                                    # Sauvegarder l'ordre dans la base de données
                                                    save_order_to_db(selected_exchange, order)
                                                    # Recharger la page pour afficher le nouvel ordre
                                                    st.rerun()
                                                else:
                                                    st.error("Échec de l'ordre. Vérifiez les paramètres et réessayez.")
                                            except Exception as e:
                                                st.error(f"Erreur lors du placement de l'ordre: {str(e)}")
                            
                            # Afficher les ordres en cours
                            st.subheader("Ordres en cours")
                            try:
                                open_orders = get_open_orders(exchange, selected_pair)
                                
                                if open_orders:
                                    # Créer un DataFrame à partir des ordres ouverts
                                    orders_data = []
                                    for order in open_orders:
                                        orders_data.append({
                                            "ID": order.get('id', 'N/A'),
                                            "Paire": order.get('symbol', 'N/A'),
                                            "Type": order.get('type', 'N/A'),
                                            "Côté": order.get('side', 'N/A'),
                                            "Quantité": order.get('amount', 0),
                                            "Prix": order.get('price', 0) if order.get('price') else "Market",
                                            "Statut": order.get('status', 'N/A'),
                                            "Date": format_date(order.get('timestamp', 0)/1000) if order.get('timestamp') else 'N/A'
                                        })
                                    
                                    orders_df = pd.DataFrame(orders_data)
                                    st.dataframe(orders_df, use_container_width=True)
                                    
                                    # Option d'annulation d'ordre
                                    if not orders_df.empty:
                                        selected_order_id = st.selectbox("Sélectionner un ordre à annuler", orders_df["ID"].tolist(), key="cancel_order_selector")
                                        if st.button("Annuler l'ordre"):
                                            with st.spinner("Annulation de l'ordre..."):
                                                try:
                                                    cancel_result = cancel_order(exchange, selected_order_id, selected_pair)
                                                    if cancel_result:
                                                        st.success(f"Ordre {selected_order_id} annulé avec succès!")
                                                        # Mettre à jour le statut de l'ordre dans la base de données
                                                        update_order_status_in_db(selected_exchange, selected_order_id, "canceled")
                                                        # Recharger la page
                                                        st.rerun()
                                                    else:
                                                        st.error("Échec de l'annulation de l'ordre.")
                                                except Exception as e:
                                                    st.error(f"Erreur lors de l'annulation de l'ordre: {str(e)}")
                                else:
                                    st.info("Aucun ordre en cours.")
                            except Exception as e:
                                st.error(f"Erreur lors de la récupération des ordres en cours: {str(e)}")
                            
                            # Historique des ordres
                            st.subheader("Historique des ordres")
                            try:
                                # Récupérer l'historique des ordres depuis la base de données
                                orders_history = get_orders_from_db(exchange_id=selected_exchange, symbol=selected_pair, limit=20)
                                
                                if orders_history:
                                    # Créer un DataFrame à partir de l'historique des ordres
                                    history_data = []
                                    for order in orders_history:
                                        history_data.append({
                                            "ID": order.order_id,
                                            "Paire": order.symbol,
                                            "Type": order.type,
                                            "Côté": order.side,
                                            "Quantité": order.amount,
                                            "Prix": order.price if order.price else "Market",
                                            "Statut": order.status,
                                            "Date": format_date(order.timestamp)
                                        })
                                    
                                    history_df = pd.DataFrame(history_data)
                                    st.dataframe(history_df, use_container_width=True)
                                else:
                                    st.info("Aucun historique d'ordre disponible.")
                            except Exception as e:
                                st.error(f"Erreur lors de la récupération de l'historique des ordres: {str(e)}")
                        else:
                            st.error("Impossible de récupérer les paires disponibles.")
                    except Exception as e:
                        st.error(f"Erreur lors de la récupération des paires disponibles: {str(e)}")
                else:
                    st.error(f"Impossible de se connecter à {selected_exchange}. Vérifiez vos informations d'API.")
        else:
            st.info("Veuillez configurer vos informations d'API pour commencer à trader.")
            
    with main_tabs[2]:
        st.header("Historique des Signaux")
        
        # Récupérer les signaux récents
        recent_signals = get_recent_signals(limit=20)
        
        if recent_signals:
            # Créer un DataFrame pour afficher les signaux
            signals_data = []
            for signal in recent_signals:
                signal_info = {
                    "Cryptomonnaie": signal.symbol,
                    "Date": signal.timestamp.strftime("%d/%m/%Y %H:%M"),
                    "Type": signal.signal_type.capitalize(),
                    "Raison": signal.reason,
                    "Prix": f"${signal.price_at_signal:.2f}" if signal.price_at_signal else "N/A"
                }
                signals_data.append(signal_info)
            
            signals_df = pd.DataFrame(signals_data)
            
            # Fonction pour colorer les types de signaux
            def color_signal_type(val):
                if val == "Achat":
                    return 'background-color: rgba(0, 255, 0, 0.3); color: darkgreen; font-weight: bold'
                elif val == "Vente":
                    return 'background-color: rgba(255, 0, 0, 0.3); color: darkred; font-weight: bold'
                elif val == "Neutre":
                    return 'background-color: rgba(100, 100, 100, 0.2); color: gray'
                return ''
            
            # Afficher le tableau avec mise en forme
            st.dataframe(
                signals_df.style
                .map(color_signal_type, subset=['Type'])
            )
            
            # Sélectionner un signal pour voir plus de détails
            if signals_df.shape[0] > 0:
                selected_signal_idx = st.selectbox(
                    "Sélectionner un signal pour voir les détails",
                    range(len(recent_signals)),
                    format_func=lambda i: f"{recent_signals[i].symbol} - {recent_signals[i].timestamp.strftime('%d/%m/%Y %H:%M')} - {recent_signals[i].signal_type.capitalize()}",
                    key="signal_details_selector"
                )
                
                selected_signal = recent_signals[selected_signal_idx]
                
                st.subheader(f"Détails du signal pour {selected_signal.symbol}")
                st.write(f"**Type:** {selected_signal.signal_type.capitalize()}")
                st.write(f"**Date:** {selected_signal.timestamp.strftime('%d/%m/%Y %H:%M')}")
                st.write(f"**Raison:** {selected_signal.reason}")
                st.write(f"**Prix au moment du signal:** ${selected_signal.price_at_signal:.2f}" if selected_signal.price_at_signal else "**Prix au moment du signal:** N/A")
                
                # Afficher les données d'indicateurs si disponibles
                if selected_signal.indicators_data:
                    st.subheader("Indicateurs techniques")
                    indicators = json.loads(selected_signal.indicators_data) if isinstance(selected_signal.indicators_data, str) else selected_signal.indicators_data
                    for key, value in indicators.items():
                        st.write(f"**{key}:** {value}")
        else:
            st.info("Aucun signal n'a encore été enregistré dans la base de données.")
    
    with main_tabs[3]:
        st.header("Gestion de la Base de Données")
        
        # Options de gestion
        db_tabs = st.tabs(["Préférences Utilisateur", "Statistiques", "Configuration"])
        
        with db_tabs[0]:
            st.subheader("Préférences Utilisateur")
            
            # Afficher les préférences sauvegardées
            period_pref = get_user_preference("selected_period", "7 jours")
            cryptos_pref = get_user_preference("selected_cryptos", "BTC,ETH,BNB")
            indicators_pref = get_user_preference("selected_indicators", "RSI,MACD")
            
            st.write(f"**Période d'analyse préférée:** {period_pref}")
            st.write(f"**Cryptomonnaies favorites:** {cryptos_pref}")
            st.write(f"**Indicateurs préférés:** {indicators_pref}")
            
            # Option pour réinitialiser les préférences
            if st.button("Réinitialiser les préférences"):
                save_user_preference("selected_period", "7 jours")
                save_user_preference("selected_cryptos", "BTC,ETH,BNB,XRP,SOL")
                save_user_preference("selected_indicators", "RSI,MACD")
                st.success("Préférences réinitialisées avec succès!")
                st.rerun()
        
        with db_tabs[1]:
            st.subheader("Statistiques de la Base de Données")
            
            # Récupérer les statistiques sur les signaux
            session = database.Session()
            
            try:
                # Compter les signaux par type
                achat_count = session.query(database.Signal).filter(database.Signal.signal_type == "achat").count()
                vente_count = session.query(database.Signal).filter(database.Signal.signal_type == "vente").count()
                neutre_count = session.query(database.Signal).filter(database.Signal.signal_type == "neutre").count()
                
                # Compter les entrées dans les autres tables
                price_count = session.query(database.PriceHistory).count()
                indicator_count = session.query(database.TechnicalIndicator).count()
                
                # Afficher les statistiques
                col1, col2, col3 = st.columns(3)
                col1.metric("Signaux d'achat", achat_count)
                col2.metric("Signaux de vente", vente_count)
                col3.metric("Signaux neutres", neutre_count)
                
                st.metric("Entrées d'historique de prix", price_count)
                st.metric("Entrées d'indicateurs techniques", indicator_count)
                
                # Graphique des signaux par type
                fig = go.Figure(data=[
                    go.Bar(name='Signaux par type', 
                           x=['Achat', 'Vente', 'Neutre'], 
                           y=[achat_count, vente_count, neutre_count],
                           marker_color=['green', 'red', 'gray'])
                ])
                fig.update_layout(title="Distribution des signaux par type")
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Erreur lors de la récupération des statistiques: {e}")
            
            finally:
                session.close()
        
        with db_tabs[2]:
            st.subheader("Configuration de la Base de Données")
            
            st.info("La base de données SQLite est actuellement utilisée et stockée localement.")
            
            # Option pour nettoyer les anciennes données
            if st.button("Nettoyer les données anciennes (> 90 jours)"):
                session = database.Session()
                try:
                    cutoff_date = datetime.now() - timedelta(days=90)
                    
                    # Supprimer les anciennes données de prix
                    deleted_prices = session.query(database.PriceHistory).filter(database.PriceHistory.timestamp < cutoff_date).delete()
                    
                    # Supprimer les anciens indicateurs
                    deleted_indicators = session.query(database.TechnicalIndicator).filter(database.TechnicalIndicator.timestamp < cutoff_date).delete()
                    
                    # Supprimer les anciens signaux
                    deleted_signals = session.query(database.Signal).filter(database.Signal.timestamp < cutoff_date).delete()
                    
                    session.commit()
                    
                    st.success(f"Nettoyage terminé! Supprimé: {deleted_prices} données de prix, {deleted_indicators} indicateurs techniques, {deleted_signals} signaux.")
                    
                except Exception as e:
                    session.rollback()
                    st.error(f"Erreur lors du nettoyage de la base de données: {e}")
                
                finally:
                    session.close()
    
    with main_tabs[4]:
        st.header("Conseiller IA")

    with main_tabs[5]:
        st.header("Agent IA")
        
        # Interface d'authentification
        with st.expander("Authentification Agent IA", expanded=True):
            password = st.text_input("Mot de passe", type="password")
            auth_button = st.button("S'authentifier")
            
            if auth_button:
                if ia_agent.authenticate(password):
                    st.session_state.agent_authenticated = True
                    st.success("Authentification réussie!")
                else:
                    st.error("Mot de passe incorrect")
        
        # Interface de l'agent si authentifié
        if st.session_state.get('agent_authenticated', False):
            user_query = st.text_area("Votre question", height=100)
            context = st.text_area("Contexte (optionnel)", height=100)
            
            if st.button("Envoyer"):
                if user_query:
                    with st.spinner("Traitement de votre demande..."):
                        response = ia_agent.process_query(user_query, context if context else None)
                        
                        st.markdown("### Réponse:")
                        st.write(response["response"])
                        st.caption(f"Type de requête: {response['type']}")
                        st.caption(f"Généré le {datetime.fromisoformat(response['timestamp']).strftime('%d/%m/%Y à %H:%M')}")
            
            # Afficher l'historique des conversations
            with st.expander("Historique des conversations"):
                for message in ia_agent.get_conversation_history():
                    role_color = "blue" if message["role"] == "assistant" else "green"
                    st.markdown(f"**{message['role'].capitalize()}** :")
                    st.markdown(f"<div style='color: {role_color};'>{message['content']}</div>", unsafe_allow_html=True)
                    st.caption(f"Le {datetime.fromisoformat(message['timestamp']).strftime('%d/%m/%Y à %H:%M')}")
                    st.markdown("---")
        
        st.markdown("""
        Notre conseiller IA utilise l'intelligence artificielle d'OpenAI pour analyser les données de marché
        et vous fournir des recommandations d'investissement personnalisées.
        """)
        
        ai_tabs = st.tabs(["Analyse de Cryptomonnaie", "Sentiment du Marché", "Stratégie d'Investissement", "Questions & Réponses"])
        
        with ai_tabs[0]:
            st.subheader("Analyse de Cryptomonnaie par IA")
            
            # Sélection de la crypto à analyser
            crypto_to_analyze = st.selectbox(
                "Sélectionner une cryptomonnaie à analyser",
                selected_cryptos,
                key="ai_crypto_selector"
            )
            
            if crypto_to_analyze in all_crypto_data:
                # Préparation des données pour l'analyse IA
                df = all_crypto_data[crypto_to_analyze]
                
                if not df.empty:
                    # Calcul des indicateurs techniques
                    df_with_indicators = calculate_technical_indicators(df)
                    
                    # Préparation des données pour l'IA
                    crypto_data = {
                        "symbol": crypto_to_analyze,
                        "current_price": float(df['close'].iloc[-1]),
                        "price_change_percentage_24h": float(((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100) if len(df) > 24 else 0,
                        "price_change_percentage_7d": float(((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100),
                        "market_cap": float(df['close'].iloc[-1] * df['volume'].iloc[-1] / 1000),  # Estimation simplifiée
                        "total_volume": float(df['volume'].iloc[-1])
                    }
                    
                    # Extraction des indicateurs techniques
                    technical_data = {}
                    for indicator in ['RSI', 'MACD', 'MACD_signal', 'BB_upper', 'BB_middle', 'BB_lower']:
                        if indicator in df_with_indicators.columns:
                            technical_data[indicator] = float(df_with_indicators[indicator].iloc[-1])
                    
                    # Ajouter signal existant s'il est disponible
                    if crypto_to_analyze in signals:
                        technical_data["signal_existant"] = signals[crypto_to_analyze]['signal']
                        technical_data["raison_signal"] = signals[crypto_to_analyze]['reason']
                    
                    # Bouton pour lancer l'analyse
                    if st.button("Analyser avec l'IA"):
                        with st.spinner("Analyse en cours par l'IA..."):
                            # Appel à l'API IA
                            analysis = analyze_crypto_data(crypto_data, technical_data)
                            
                            if "erreur" not in analysis:
                                # Affichage des résultats
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    # Afficher la recommandation de manière bien visible
                                    recommandation = analysis.get("recommandation", "indéterminée")
                                    rec_color = "green" if recommandation == "acheter" else "red" if recommandation == "vendre" else "orange"
                                    
                                    st.markdown(f"""
                                    <div style='background-color: rgba({
                                    '0, 128, 0' if recommandation == 'acheter' else 
                                    '255, 0, 0' if recommandation == 'vendre' else 
                                    '255, 165, 0'
                                    }, 0.2); padding: 20px; border-radius: 5px;'>
                                    <h2 style='color: {rec_color}; margin: 0;'>Recommandation: {recommandation.upper()}</h2>
                                    <p>Niveau de risque: {'⭐' * int(analysis.get('niveau_risque', 3))}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.subheader("Résumé")
                                    st.write(analysis.get("resume", ""))
                                    
                                    st.subheader("Analyse du Marché")
                                    st.write(analysis.get("analyse_marche", ""))
                                    
                                    st.subheader("Analyse Technique")
                                    st.write(analysis.get("analyse_technique", ""))
                                
                                with col2:
                                    st.subheader("Perspectives")
                                    
                                    st.markdown("**Court terme (1-7 jours)**")
                                    st.write(analysis.get("perspectives_court_terme", ""))
                                    
                                    st.markdown("**Moyen terme (1-3 mois)**")
                                    st.write(analysis.get("perspectives_moyen_terme", ""))
                                
                                # Ajouter un timestamp pour l'analyse
                                st.caption(f"Analyse générée le {datetime.fromisoformat(analysis.get('timestamp', datetime.now().isoformat())).strftime('%d/%m/%Y à %H:%M')}")
                            else:
                                st.error(f"Échec de l'analyse IA: {analysis.get('erreur', 'Erreur inconnue')}")
                else:
                    st.error(f"Aucune donnée disponible pour {crypto_to_analyze}")
            else:
                st.warning("Veuillez sélectionner une cryptomonnaie à analyser")
        
        with ai_tabs[1]:
            st.subheader("Sentiment Global du Marché")
            
            if st.button("Analyser le sentiment du marché"):
                with st.spinner("Analyse du sentiment du marché en cours..."):
                    # Appel à l'API IA pour le sentiment du marché
                    sentiment = get_market_sentiment()
                    
                    if "erreur" not in sentiment:
                        # Affichage du sentiment global
                        sentiment_global = sentiment.get("sentiment_global", "neutre")
                        sentiment_color = "green" if sentiment_global == "haussier" else "red" if sentiment_global == "baissier" else "gray"
                        
                        st.markdown(f"""
                        <div style='background-color: rgba({
                        '0, 128, 0' if sentiment_global == 'haussier' else 
                        '255, 0, 0' if sentiment_global == 'baissier' else 
                        '100, 100, 100'
                        }, 0.2); padding: 20px; border-radius: 5px;'>
                        <h2 style='color: {sentiment_color}; margin: 0;'>Sentiment du marché: {sentiment_global.upper()}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Facteurs clés
                        st.subheader("Facteurs Influençant le Marché")
                        facteurs = sentiment.get("facteurs_cles", [])
                        for facteur in facteurs:
                            st.markdown(f"- {facteur}")
                        
                        # Cryptomonnaies prometteuses
                        st.subheader("Cryptomonnaies Prometteuses")
                        cryptos = sentiment.get("cryptos_prometteuses", [])
                        for crypto in cryptos:
                            st.markdown(f"- {crypto}")
                        
                        # Risques à surveiller
                        st.subheader("Risques à Surveiller")
                        risques = sentiment.get("risques_a_surveiller", [])
                        for risque in risques:
                            st.markdown(f"- {risque}")
                        
                        # Conseils généraux
                        st.subheader("Conseils Généraux")
                        st.write(sentiment.get("conseils_generaux", ""))
                        
                        # Timestamp
                        st.caption(f"Analyse générée le {datetime.fromisoformat(sentiment.get('timestamp', datetime.now().isoformat())).strftime('%d/%m/%Y à %H:%M')}")
                    else:
                        st.error(f"Échec de l'analyse du sentiment: {sentiment.get('erreur', 'Erreur inconnue')}")
        
        with ai_tabs[2]:
            st.subheader("Stratégie d'Investissement Personnalisée")
            
            # Profil de risque
            risk_profile = st.radio(
                "Votre profil de risque",
                ["Conservateur", "Modéré", "Agressif"],
                index=1,
                horizontal=True,
                key="risk_profile_selector"
            )
            
            # Conversion du profil en anglais pour l'API
            risk_map = {"Conservateur": "conservative", "Modéré": "moderate", "Agressif": "aggressive"}
            
            # Portefeuille actuel (version simplifiée)
            st.subheader("Votre portefeuille actuel")
            
            # Création dynamique de champs pour le portefeuille
            portfolio = {}
            
            for i in range(5):  # Max 5 cryptos dans le portefeuille
                cols = st.columns([2, 2, 1])
                
                with cols[0]:
                    crypto = st.selectbox(
                        f"Crypto #{i+1}",
                        [""] + available_cryptos,
                        key=f"portfolio_crypto_{i}"
                    )
                
                if crypto:  # Seulement si une crypto est sélectionnée
                    with cols[1]:
                        amount = st.number_input(
                            f"Quantité de {crypto}",
                            min_value=0.0,
                            value=0.0,
                            key=f"portfolio_amount_{i}"
                        )
                    
                    with cols[2]:
                        if amount > 0:
                            portfolio[crypto] = amount
                            st.success("✓")
            
            # Bouton pour générer la stratégie
            if st.button("Générer une stratégie d'investissement"):
                if portfolio:
                    with st.spinner("Génération de la stratégie en cours..."):
                        # Appel à l'API IA
                        strategy = generate_investment_strategy(portfolio, risk_map[risk_profile])
                        
                        if "erreur" not in strategy:
                            # Affichage de la stratégie
                            st.subheader("Évaluation du Portefeuille")
                            st.write(strategy.get("evaluation_portefeuille", ""))
                            
                            st.subheader("Allocation Recommandée")
                            st.write(strategy.get("allocation_recommandee", ""))
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("Cryptos à Considérer")
                                cryptos_to_add = strategy.get("cryptos_a_ajouter", [])
                                for crypto in cryptos_to_add:
                                    st.markdown(f"- {crypto}")
                            
                            with col2:
                                st.subheader("Cryptos à Reconsidérer")
                                cryptos_to_sell = strategy.get("cryptos_a_vendre", [])
                                for crypto in cryptos_to_sell:
                                    st.markdown(f"- {crypto}")
                            
                            st.subheader("Stratégie à Court Terme")
                            st.write(strategy.get("strategie_court_terme", ""))
                            
                            st.subheader("Stratégie à Long Terme")
                            st.write(strategy.get("strategie_long_terme", ""))
                            
                            st.subheader("Gestion des Risques")
                            st.write(strategy.get("gestion_risques", ""))
                            
                            # Résumé
                            st.subheader("Résumé de la Stratégie")
                            st.info(strategy.get("resume", ""))
                            
                            # Timestamp
                            st.caption(f"Stratégie générée le {datetime.fromisoformat(strategy.get('timestamp', datetime.now().isoformat())).strftime('%d/%m/%Y à %H:%M')}")
                        else:
                            st.error(f"Échec de la génération de stratégie: {strategy.get('erreur', 'Erreur inconnue')}")
                else:
                    st.warning("Veuillez ajouter au moins une cryptomonnaie à votre portefeuille")
        
        with ai_tabs[3]:
            st.subheader("Questions & Réponses")
            
            st.markdown("""
            Posez une question à notre conseiller IA spécialisé en cryptomonnaies
            et obtenez une réponse personnalisée basée sur les connaissances les plus récentes.
            """)
            
            # Champ de texte pour la question
            user_question = st.text_area(
                "Votre question",
                height=100,
                placeholder="Exemple: Quelle est la différence entre Proof of Work et Proof of Stake?"
            )
            
            # Contexte supplémentaire (optionnel)
            show_context = st.checkbox("Ajouter du contexte supplémentaire")
            
            context = None
            if show_context:
                context_info = st.text_area(
                    "Contexte supplémentaire (optionnel)",
                    height=100,
                    placeholder="Ajoutez ici des informations supplémentaires pour mieux contextualiser votre question."
                )
                
                if context_info:
                    context = {"contexte_utilisateur": context_info}
            
            # Bouton pour poser la question
            if st.button("Poser la question") and user_question:
                with st.spinner("Traitement de votre question..."):
                    # Appel à l'API IA
                    answer = ask_ai_advisor(user_question, context)
                    
                    # Affichage de la réponse
                    st.markdown("### Réponse:")
                    st.markdown(answer)
                    
                    # Timestamp
                    st.caption(f"Réponse générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
            elif user_question == "":
                st.info("Veuillez entrer une question pour obtenir une réponse.")

except Exception as e:
    st.error(f"Une erreur s'est produite: {str(e)}")
    st.info("Veuillez réessayer plus tard ou contacter l'administrateur si le problème persiste.")
