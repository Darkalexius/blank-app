import pandas as pd
import numpy as np
from technical_indicators import calculate_technical_indicators

def identify_promising_cryptocurrencies(crypto_data_dict, selected_indicators, top_n=5):
    """
    Identifie les cryptomonnaies les plus prometteuses en fonction des indicateurs techniques
    
    Args:
        crypto_data_dict (dict): Dictionnaire des DataFrames de données par cryptomonnaie
        selected_indicators (list): Liste des indicateurs techniques sélectionnés
        top_n (int): Nombre de cryptomonnaies à retourner
        
    Returns:
        list: Liste des tuples (crypto, score) triés par score décroissant
    """
    scores = {}
    
    for crypto, data in crypto_data_dict.items():
        if data.empty:
            continue
        
        # Calculer les indicateurs techniques
        df = calculate_technical_indicators(data)
        
        # Calculer le score pour cette crypto
        score = calculate_crypto_score(df, selected_indicators)
        
        scores[crypto] = score
    
    # Trier les cryptos par score décroissant
    sorted_cryptos = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Retourner les top_n cryptos
    return sorted_cryptos[:top_n]

def calculate_crypto_score(df, selected_indicators):
    """
    Calcule un score pour une cryptomonnaie en fonction des indicateurs techniques
    
    Args:
        df (pandas.DataFrame): DataFrame avec les indicateurs techniques
        selected_indicators (list): Liste des indicateurs techniques sélectionnés
        
    Returns:
        float: Score calculé
    """
    score = 0.0
    
    # Points basés sur la tendance récente des prix
    price_change = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    if price_change > 10:
        score += 2.0
    elif price_change > 5:
        score += 1.0
    elif price_change > 0:
        score += 0.5
        
    # Vérifier les indicateurs sélectionnés
    if "RSI" in selected_indicators and "RSI" in df.columns:
        rsi = df['RSI'].iloc[-1]
        # RSI entre 40 et 60 indique un marché équilibré
        if 40 <= rsi <= 60:
            score += 0.5
        # RSI entre 30 et 40 indique un marché potentiellement sous-évalué
        elif 30 <= rsi < 40:
            score += 1.0
        # RSI < 30 indique un marché survente (opportunité d'achat)
        elif rsi < 30:
            score += 1.5
    
    if "MACD" in selected_indicators and all(col in df.columns for col in ['MACD', 'MACD_signal']):
        # MACD au-dessus de la ligne de signal est positif
        if df['MACD'].iloc[-1] > df['MACD_signal'].iloc[-1]:
            score += 1.0
        # Histogramme MACD en augmentation est positif
        if df['MACD_hist'].iloc[-1] > df['MACD_hist'].iloc[-2]:
            score += 0.5
        # Croisement récent MACD au-dessus de la ligne de signal
        if df['MACD'].iloc[-1] > df['MACD_signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD_signal'].iloc[-2]:
            score += 1.5
    
    if "Bollinger Bands" in selected_indicators and all(col in df.columns for col in ['BB_upper', 'BB_middle', 'BB_lower']):
        # Prix proche de la bande inférieure (potentiellement sous-évalué)
        if df['close'].iloc[-1] < df['BB_lower'].iloc[-1] * 1.05:
            score += 1.0
        # Prix qui rebondit de la bande inférieure
        if df['close'].iloc[-1] > df['close'].iloc[-2] and df['close'].iloc[-2] < df['BB_lower'].iloc[-2]:
            score += 1.5
    
    if "EMA" in selected_indicators and "EMA_20" in df.columns and "EMA_50" in df.columns:
        # EMA court terme au-dessus de EMA moyen terme (tendance haussière)
        if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1]:
            score += 1.0
        # Croisement récent de EMA court terme au-dessus de EMA moyen terme
        if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1] and df['EMA_20'].iloc[-2] <= df['EMA_50'].iloc[-2]:
            score += 1.5
    
    if "SMA" in selected_indicators and "SMA_50" in df.columns and "SMA_200" in df.columns:
        # Prix au-dessus des deux SMA (tendance haussière)
        if df['close'].iloc[-1] > df['SMA_50'].iloc[-1] and df['close'].iloc[-1] > df['SMA_200'].iloc[-1]:
            score += 1.0
        # SMA 50 au-dessus de SMA 200 (tendance haussière à moyen terme)
        if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]:
            score += 1.0
        # Croisement récent (Golden Cross) de SMA 50 au-dessus de SMA 200
        if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1] and df['SMA_50'].iloc[-20] <= df['SMA_200'].iloc[-20]:
            score += 2.0
    
    # Volume en augmentation est généralement positif
    try:
        volume_mean = df['volume'].rolling(window=7).mean().iloc[-1]
        if volume_mean > 0:  # Éviter la division par zéro
            volume_change = (df['volume'].iloc[-1] / volume_mean)
            if volume_change > 1.5:
                score += 1.0
            elif volume_change > 1.2:
                score += 0.5
    except (ZeroDivisionError, ValueError, IndexError):
        # Ignorer les erreurs liées au calcul du volume
        pass
    
    return score

def generate_signals(crypto_data_dict, selected_indicators):
    """
    Génère des signaux d'achat/vente pour chaque cryptomonnaie
    
    Args:
        crypto_data_dict (dict): Dictionnaire des DataFrames de données par cryptomonnaie
        selected_indicators (list): Liste des indicateurs techniques sélectionnés
        
    Returns:
        dict: Dictionnaire des signaux par cryptomonnaie
    """
    signals = {}
    
    for crypto, data in crypto_data_dict.items():
        if data.empty:
            continue
        
        # Calculer les indicateurs techniques
        df = calculate_technical_indicators(data)
        
        # Calculer le signal consolidé
        signal, reason, details, advice = analyze_crypto(df, selected_indicators)
        
        signals[crypto] = {
            'signal': signal,
            'reason': reason,
            'details': details,
            'advice': advice
        }
    
    return signals

def analyze_crypto(df, selected_indicators):
    """
    Analyse une cryptomonnaie et génère un signal consolidé
    
    Args:
        df (pandas.DataFrame): DataFrame avec les indicateurs techniques
        selected_indicators (list): Liste des indicateurs techniques sélectionnés
        
    Returns:
        tuple: (signal, reason, details, advice)
    """
    # Compter les signaux d'achat et de vente
    buy_signals = 0
    sell_signals = 0
    neutral_signals = 0
    
    details = {}
    
    # Analyser le RSI
    if "RSI" in selected_indicators and "RSI" in df.columns:
        rsi = df['RSI'].iloc[-1]
        details["RSI"] = f"{rsi:.2f}"
        
        if rsi < 30:
            buy_signals += 1
            details["RSI_signal"] = "Achat (survente)"
        elif rsi > 70:
            sell_signals += 1
            details["RSI_signal"] = "Vente (surachat)"
        else:
            neutral_signals += 1
            details["RSI_signal"] = "Neutre"
    
    # Analyser le MACD
    if "MACD" in selected_indicators and all(col in df.columns for col in ['MACD', 'MACD_signal']):
        macd = df['MACD'].iloc[-1]
        signal_line = df['MACD_signal'].iloc[-1]
        hist = df['MACD_hist'].iloc[-1]
        
        details["MACD"] = f"{macd:.2f}"
        details["MACD_signal"] = f"{signal_line:.2f}"
        details["MACD_hist"] = f"{hist:.2f}"
        
        # Croisement récent
        if df['MACD'].iloc[-1] > df['MACD_signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD_signal'].iloc[-2]:
            buy_signals += 1
            details["MACD_crossover"] = "Achat (croisement haussier)"
        elif df['MACD'].iloc[-1] < df['MACD_signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD_signal'].iloc[-2]:
            sell_signals += 1
            details["MACD_crossover"] = "Vente (croisement baissier)"
        # Position actuelle
        elif macd > signal_line:
            buy_signals += 0.5
            details["MACD_position"] = "Positif (MACD > Signal)"
        elif macd < signal_line:
            sell_signals += 0.5
            details["MACD_position"] = "Négatif (MACD < Signal)"
        else:
            neutral_signals += 1
            details["MACD_position"] = "Neutre"
    
    # Analyser les bandes de Bollinger
    if "Bollinger Bands" in selected_indicators and all(col in df.columns for col in ['BB_upper', 'BB_middle', 'BB_lower']):
        price = df['close'].iloc[-1]
        upper = df['BB_upper'].iloc[-1]
        lower = df['BB_lower'].iloc[-1]
        
        details["Prix_actuel"] = f"{price:.2f}"
        details["BB_upper"] = f"{upper:.2f}"
        details["BB_lower"] = f"{lower:.2f}"
        
        # Prix proche de la bande inférieure
        if price < lower * 1.05:
            buy_signals += 1
            details["Bollinger"] = "Achat (proche de la bande inférieure)"
        # Prix proche de la bande supérieure
        elif price > upper * 0.95:
            sell_signals += 1
            details["Bollinger"] = "Vente (proche de la bande supérieure)"
        # Prix au milieu des bandes
        else:
            neutral_signals += 1
            details["Bollinger"] = "Neutre (entre les bandes)"
    
    # Analyser les moyennes mobiles
    if "SMA" in selected_indicators and "SMA_50" in df.columns and "SMA_200" in df.columns:
        price = df['close'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        
        details["SMA_50"] = f"{sma_50:.2f}"
        details["SMA_200"] = f"{sma_200:.2f}"
        
        # Golden Cross (SMA 50 croise au-dessus de SMA 200)
        if sma_50 > sma_200 and df['SMA_50'].iloc[-20] <= df['SMA_200'].iloc[-20]:
            buy_signals += 2
            details["SMA_crossover"] = "Achat fort (Golden Cross récent)"
        # Death Cross (SMA 50 croise en-dessous de SMA 200)
        elif sma_50 < sma_200 and df['SMA_50'].iloc[-20] >= df['SMA_200'].iloc[-20]:
            sell_signals += 2
            details["SMA_crossover"] = "Vente forte (Death Cross récent)"
        # Position des moyennes mobiles
        elif sma_50 > sma_200:
            buy_signals += 0.5
            details["SMA_position"] = "Positif (SMA 50 > SMA 200)"
        elif sma_50 < sma_200:
            sell_signals += 0.5
            details["SMA_position"] = "Négatif (SMA 50 < SMA 200)"
        else:
            neutral_signals += 0.5
            details["SMA_position"] = "Neutre"
    
    # Analyser l'EMA
    if "EMA" in selected_indicators and "EMA_20" in df.columns and "EMA_50" in df.columns:
        ema_20 = df['EMA_20'].iloc[-1]
        ema_50 = df['EMA_50'].iloc[-1]
        
        details["EMA_20"] = f"{ema_20:.2f}"
        details["EMA_50"] = f"{ema_50:.2f}"
        
        # Croisement récent
        if ema_20 > ema_50 and df['EMA_20'].iloc[-2] <= df['EMA_50'].iloc[-2]:
            buy_signals += 1
            details["EMA_crossover"] = "Achat (croisement haussier)"
        elif ema_20 < ema_50 and df['EMA_20'].iloc[-2] >= df['EMA_50'].iloc[-2]:
            sell_signals += 1
            details["EMA_crossover"] = "Vente (croisement baissier)"
        # Position actuelle
        elif ema_20 > ema_50:
            buy_signals += 0.5
            details["EMA_position"] = "Positif (EMA 20 > EMA 50)"
        elif ema_20 < ema_50:
            sell_signals += 0.5
            details["EMA_position"] = "Négatif (EMA 20 < EMA 50)"
        else:
            neutral_signals += 0.5
            details["EMA_position"] = "Neutre"
    
    # Calculer le signal consolidé et la raison
    if buy_signals > sell_signals + 0.5:
        signal = "Achat"
        if buy_signals >= 2 * sell_signals:
            strength = "fort"
        else:
            strength = "modéré"
        
        reason = f"Signal d'achat {strength} basé sur {buy_signals:.1f} indicateurs positifs contre {sell_signals:.1f} négatifs"
        advice = "Considérez un achat progressif pour réduire le risque. Surveillez les niveaux de résistance au-dessus du prix actuel."
        
    elif sell_signals > buy_signals + 0.5:
        signal = "Vente"
        if sell_signals >= 2 * buy_signals:
            strength = "fort"
        else:
            strength = "modéré"
        
        reason = f"Signal de vente {strength} basé sur {sell_signals:.1f} indicateurs négatifs contre {buy_signals:.1f} positifs"
        advice = "Envisagez de prendre vos bénéfices ou de réduire votre position. Surveillez les niveaux de support en dessous du prix actuel."
        
    else:
        signal = "Neutre"
        reason = f"Signaux mixtes avec {buy_signals:.1f} indicateurs positifs et {sell_signals:.1f} négatifs"
        advice = "Attendez un signal plus clair avant de prendre une décision. Surveillez de près l'évolution des indicateurs techniques."
    
    return signal, reason, details, advice
