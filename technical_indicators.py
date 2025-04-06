import pandas as pd
import numpy as np

def calculate_technical_indicators(df):
    """
    Calcule les indicateurs techniques pour un DataFrame de données de prix
    
    Args:
        df (pandas.DataFrame): DataFrame avec les colonnes OHLCV
        
    Returns:
        pandas.DataFrame: DataFrame original avec les indicateurs techniques ajoutés
    """
    # Copier le DataFrame pour éviter de modifier l'original
    df_copy = df.copy()
    
    # Calculer le RSI (Relative Strength Index)
    df_copy = calculate_rsi(df_copy)
    
    # Calculer le MACD (Moving Average Convergence Divergence)
    df_copy = calculate_macd(df_copy)
    
    # Calculer les bandes de Bollinger
    df_copy = calculate_bollinger_bands(df_copy)
    
    # Calculer les moyennes mobiles
    df_copy = calculate_moving_averages(df_copy)
    
    # Calculer les signaux basés sur les indicateurs
    df_copy = calculate_signals(df_copy)
    
    return df_copy

def calculate_rsi(df, period=14):
    """
    Calcule le RSI (Relative Strength Index)
    
    Args:
        df (pandas.DataFrame): DataFrame avec les prix de clôture
        period (int): Période pour le calcul du RSI
        
    Returns:
        pandas.DataFrame: DataFrame avec le RSI ajouté
    """
    close_delta = df['close'].diff()
    
    # Séparer les gains et les pertes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    # Calculer la moyenne mobile exponentielle des gains et des pertes
    ma_up = up.ewm(com=period-1, adjust=True, min_periods=period).mean()
    ma_down = down.ewm(com=period-1, adjust=True, min_periods=period).mean()
    
    # Calculer le RSI
    rsi = 100 - (100 / (1 + ma_up / ma_down))
    
    # Ajouter le RSI au DataFrame
    df['RSI'] = rsi
    
    return df

def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """
    Calcule le MACD (Moving Average Convergence Divergence)
    
    Args:
        df (pandas.DataFrame): DataFrame avec les prix de clôture
        fast_period (int): Période pour la moyenne mobile rapide
        slow_period (int): Période pour la moyenne mobile lente
        signal_period (int): Période pour la ligne de signal
        
    Returns:
        pandas.DataFrame: DataFrame avec le MACD ajouté
    """
    # Calculer les moyennes mobiles exponentielles
    ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculer le MACD et la ligne de signal
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal_period, adjust=False).mean()
    macd_hist = macd - macd_signal
    
    # Ajouter les indicateurs au DataFrame
    df['MACD'] = macd
    df['MACD_signal'] = macd_signal
    df['MACD_hist'] = macd_hist
    
    return df

def calculate_bollinger_bands(df, period=20, num_std=2):
    """
    Calcule les bandes de Bollinger
    
    Args:
        df (pandas.DataFrame): DataFrame avec les prix de clôture
        period (int): Période pour la moyenne mobile
        num_std (int): Nombre d'écarts types pour les bandes
        
    Returns:
        pandas.DataFrame: DataFrame avec les bandes de Bollinger ajoutées
    """
    # Calculer la moyenne mobile
    df['BB_middle'] = df['close'].rolling(window=period).mean()
    
    # Calculer l'écart type
    rolling_std = df['close'].rolling(window=period).std()
    
    # Calculer les bandes supérieure et inférieure
    df['BB_upper'] = df['BB_middle'] + (rolling_std * num_std)
    df['BB_lower'] = df['BB_middle'] - (rolling_std * num_std)
    
    return df

def calculate_moving_averages(df):
    """
    Calcule différentes moyennes mobiles
    
    Args:
        df (pandas.DataFrame): DataFrame avec les prix de clôture
        
    Returns:
        pandas.DataFrame: DataFrame avec les moyennes mobiles ajoutées
    """
    # Calculer la moyenne mobile simple (SMA)
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()
    
    # Calculer la moyenne mobile exponentielle (EMA)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    return df

def calculate_signals(df):
    """
    Calcule les signaux basés sur les indicateurs techniques
    
    Args:
        df (pandas.DataFrame): DataFrame avec les indicateurs techniques
        
    Returns:
        pandas.DataFrame: DataFrame avec les signaux ajoutés
    """
    # Initialiser la colonne de signal à 0 (neutre)
    df['signal'] = 0
    
    # Signaux basés sur le RSI
    if 'RSI' in df.columns:
        # Signal d'achat si RSI < 30
        df.loc[df['RSI'] < 30, 'signal'] = 1
        # Signal de vente si RSI > 70
        df.loc[df['RSI'] > 70, 'signal'] = -1
    
    # Signaux basés sur le MACD
    if all(col in df.columns for col in ['MACD', 'MACD_signal']):
        # Calculer les croisements du MACD
        df['macd_crossover'] = 0
        # Croisement haussier: MACD croise au-dessus de la ligne de signal
        df.loc[(df['MACD'] > df['MACD_signal']) & (df['MACD'].shift(1) <= df['MACD_signal'].shift(1)), 'macd_crossover'] = 1
        # Croisement baissier: MACD croise en-dessous de la ligne de signal
        df.loc[(df['MACD'] < df['MACD_signal']) & (df['MACD'].shift(1) >= df['MACD_signal'].shift(1)), 'macd_crossover'] = -1
        
        # Ajouter les signaux du MACD au signal principal
        df.loc[df['macd_crossover'] == 1, 'signal'] = 1
        df.loc[df['macd_crossover'] == -1, 'signal'] = -1
    
    # Signaux basés sur les bandes de Bollinger
    if all(col in df.columns for col in ['BB_upper', 'BB_lower']):
        # Signal d'achat potentiel si le prix est proche de la bande inférieure
        df.loc[df['close'] < df['BB_lower'] * 1.01, 'signal'] = 1
        # Signal de vente potentiel si le prix est proche de la bande supérieure
        df.loc[df['close'] > df['BB_upper'] * 0.99, 'signal'] = -1
    
    # Signaux basés sur les moyennes mobiles
    if all(col in df.columns for col in ['SMA_50', 'SMA_200']):
        # Golden Cross (signal d'achat): SMA 50 croise au-dessus de SMA 200
        golden_cross = (df['SMA_50'] > df['SMA_200']) & (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # Death Cross (signal de vente): SMA 50 croise en-dessous de SMA 200
        death_cross = (df['SMA_50'] < df['SMA_200']) & (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1))
        df.loc[death_cross, 'signal'] = -1
    
    return df
