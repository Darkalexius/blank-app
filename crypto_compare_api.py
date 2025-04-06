import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

class CryptoCompareAPI:
    """
    Classe pour interagir avec l'API CryptoCompare
    """
    
    def __init__(self, api_key=None):
        """
        Initialise la connexion à l'API CryptoCompare
        
        Args:
            api_key (str): Clé API CryptoCompare (optionnelle)
        """
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers["authorization"] = f"Apikey {api_key}"
    
    def get_available_cryptos(self, limit=50):
        """
        Récupère la liste des cryptomonnaies disponibles
        
        Args:
            limit (int): Nombre de cryptomonnaies à récupérer
            
        Returns:
            list: Liste des symboles de cryptomonnaies
        """
        try:
            # Obtenir la liste des cryptomonnaies
            url = f"{self.base_url}/top/mktcapfull?limit={limit}&tsym=USD"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("Response") == "Error":
                raise Exception(data.get("Message", "Erreur inconnue de l'API"))
            
            cryptos = []
            
            # Extraire les symboles et les IDs
            for coin in data.get("Data", []):
                coin_info = coin.get("CoinInfo", {})
                symbol = coin_info.get("Name")
                
                if symbol:
                    cryptos.append(symbol)
            
            return cryptos
            
        except Exception as e:
            print(f"Erreur lors de la récupération des cryptomonnaies disponibles: {e}")
            # Retourner une liste de cryptos par défaut en cas d'erreur
            return ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "AVAX", "ALPACA"]
    
    def get_historical_data(self, symbol, vs_currency="USD", limit=2000, interval="hour"):
        """
        Récupère les données historiques d'une cryptomonnaie
        
        Args:
            symbol (str): Symbole de la cryptomonnaie (ex: BTC)
            vs_currency (str): Devise de comparaison (ex: USD)
            limit (int): Nombre de points de données à récupérer
            interval (str): Intervalle entre les points ('minute', 'hour', 'day')
            
        Returns:
            pandas.DataFrame: DataFrame contenant les données OHLCV
        """
        try:
            # Mapper l'intervalle à l'endpoint correct
            endpoint = "histohour"
            if interval == "minute":
                endpoint = "histominute"
            elif interval == "day":
                endpoint = "histoday"
            
            # Construire l'URL
            url = f"{self.base_url}/{endpoint}?fsym={symbol}&tsym={vs_currency}&limit={limit}"
            
            # Faire la requête
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("Response") == "Error":
                raise Exception(data.get("Message", "Erreur inconnue de l'API"))
            
            # Extraire les données
            historical_data = data.get("Data", [])
            
            if not historical_data:
                return pd.DataFrame()
            
            # Créer le DataFrame
            df = pd.DataFrame(historical_data)
            
            # Convertir les timestamps en datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Renommer les colonnes pour correspondre à notre format
            df = df.rename(columns={
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volumefrom': 'volume'
            })
            
            # Définir l'index
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Erreur lors de la récupération des données pour {symbol}: {e}")
            
            # Si l'erreur est liée à une limite d'API dépassée
            if "rate limit" in str(e).lower() or "429" in str(e):
                print(f"Limite d'API dépassée. Génération de données de démonstration pour {symbol}.")
                return self._generate_demo_data(symbol, interval)
            
            # Retourner un DataFrame vide en cas d'erreur
            return pd.DataFrame()
    
    def get_current_prices(self, symbols, vs_currency="USD"):
        """
        Récupère les prix actuels pour une liste de cryptomonnaies
        
        Args:
            symbols (list): Liste des symboles de cryptomonnaies
            vs_currency (str): Devise de comparaison (ex: USD)
            
        Returns:
            dict: Dictionnaire des prix actuels {symbole: prix}
        """
        try:
            # Convertir la liste en string délimitée par des virgules
            fsyms = ",".join(symbols)
            
            # Construire l'URL
            url = f"{self.base_url}/pricemulti?fsyms={fsyms}&tsyms={vs_currency}"
            
            # Faire la requête
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict) and data.get("Response") == "Error":
                raise Exception(data.get("Message", "Erreur inconnue de l'API"))
            
            # Construire le dictionnaire de prix
            prices = {}
            for symbol, price_data in data.items():
                prices[symbol] = price_data.get(vs_currency, 0)
            
            return prices
            
        except Exception as e:
            print(f"Erreur lors de la récupération des prix actuels: {e}")
            
            # Si l'erreur est liée à une limite d'API dépassée
            if "rate limit" in str(e).lower() or "429" in str(e):
                print(f"Limite d'API dépassée. Génération de prix de démonstration.")
                return self._generate_demo_prices(symbols)
            
            return {}
    
    def _generate_demo_data(self, symbol, interval="hour"):
        """
        Génère des données de démonstration pour une cryptomonnaie
        
        Args:
            symbol (str): Symbole de la cryptomonnaie
            interval (str): Intervalle entre les points ('minute', 'hour', 'day')
            
        Returns:
            pandas.DataFrame: DataFrame contenant les données OHLCV
        """
        # Définir le nombre de points de données selon l'intervalle
        if interval == "minute":
            n_points = 500  # ~8 heures
        elif interval == "day":
            n_points = 90   # 3 mois
        else:  # hour
            n_points = 168  # 7 jours
        
        # Créer une série temporelle
        end_time = pd.Timestamp.now()
        
        if interval == "minute":
            timestamps = [end_time - pd.Timedelta(minutes=i) for i in range(n_points)]
        elif interval == "day":
            timestamps = [end_time - pd.Timedelta(days=i) for i in range(n_points)]
        else:  # hour
            timestamps = [end_time - pd.Timedelta(hours=i) for i in range(n_points)]
            
        timestamps.reverse()  # Mettre dans l'ordre chronologique
        
        # Définir différents prix de base selon la crypto
        base_prices = {
            "BTC": 50000,
            "ETH": 3000,
            "BNB": 500,
            "SOL": 100,
            "XRP": 0.5,
            "ADA": 0.4,
            "DOGE": 0.1,
            "DOT": 10,
            "MATIC": 1.5,
            "AVAX": 30,
            "ALPACA": 0.6
        }
        
        # Prix de base pour la crypto (par défaut 100 si non trouvée)
        base_price = base_prices.get(symbol, 100)
        
        # Générer des prix aléatoires avec tendance
        trend = np.random.choice([-1, 1])  # Tendance aléatoire (haussière ou baissière)
        volatility = 0.03  # Volatilité de 3%
        
        prices = []
        volumes = []
        current_price = base_price
        
        for i in range(n_points):
            # Ajouter de la volatilité aléatoire avec une légère tendance
            change = np.random.normal(0.001 * trend, volatility)
            current_price *= (1 + change)
            
            # Données OHLCV
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            # Volume - dépend de la crypto
            volume = base_price * 1000 * (1 + np.random.normal(0, 0.2))
            
            prices.append((open_price, high_price, low_price, current_price))
            volumes.append(volume)
        
        # Créer le DataFrame
        df = pd.DataFrame(
            {
                'open': [p[0] for p in prices],
                'high': [p[1] for p in prices],
                'low': [p[2] for p in prices],
                'close': [p[3] for p in prices],
                'volume': volumes
            },
            index=timestamps
        )
        
        return df
    
    def _generate_demo_prices(self, symbols):
        """
        Génère des prix de démonstration pour une liste de cryptomonnaies
        
        Args:
            symbols (list): Liste des symboles de cryptomonnaies
            
        Returns:
            dict: Dictionnaire des prix générés {symbole: prix}
        """
        # Prix de base approximatifs pour les principales cryptomonnaies
        base_prices = {
            "BTC": 50000,
            "ETH": 3000,
            "BNB": 500,
            "SOL": 100,
            "XRP": 0.5,
            "ADA": 0.4,
            "DOGE": 0.1,
            "DOT": 10,
            "MATIC": 1.5,
            "AVAX": 30,
            "SHIB": 0.00001,
            "LTC": 150,
            "LINK": 15,
            "UNI": 8,
            "ATOM": 12,
            "ETC": 40,
            "XLM": 0.3,
            "BCH": 300,
            "ALGO": 0.5,
            "NEAR": 5
        }
        
        # Générer des prix avec une petite variation aléatoire
        demo_prices = {}
        for symbol in symbols:
            # Récupérer le prix de base ou utiliser 100 comme valeur par défaut
            base_price = base_prices.get(symbol, 100)
            # Ajouter une variation aléatoire de -5% à +5%
            variation = np.random.uniform(-0.05, 0.05)
            demo_prices[symbol] = base_price * (1 + variation)
        
        return demo_prices

# Instancier l'API
crypto_compare = CryptoCompareAPI()

# Fonctions d'interface pour maintenir la compatibilité avec le reste de l'application

def get_available_cryptocurrencies():
    """
    Récupère la liste des principales cryptomonnaies disponibles
    """
    return crypto_compare.get_available_cryptos(limit=50)

def fetch_cryptocurrency_data(symbol, period="7d", interval="1h"):
    """
    Récupère les données historiques d'une cryptomonnaie spécifique
    
    Args:
        symbol (str): Symbole de la cryptomonnaie (ex: BTC)
        period (str): Période de temps ('1d', '7d', '30d', '90d')
        interval (str): Intervalle de temps ('1m', '5m', '15m', '1h', '4h', '1d')
        
    Returns:
        pandas.DataFrame: DataFrame contenant les données OHLCV
    """
    # Convertir la période en nombre de points
    periods = {
        "1d": 24,      # 24 heures
        "7d": 168,     # 7 jours * 24 heures
        "30d": 720,    # 30 jours * 24 heures
        "90d": 2160    # 90 jours * 24 heures
    }
    limit = periods.get(period, 168)
    
    # Convertir l'intervalle
    interval_map = {
        "1m": "minute",
        "5m": "minute",
        "15m": "minute",
        "1h": "hour",
        "4h": "hour",
        "1d": "day"
    }
    api_interval = interval_map.get(interval, "hour")
    
    # Si l'intervalle est plus grand que la minute mais qu'on a demandé des minutes
    if interval in ["5m", "15m"] and api_interval == "minute":
        # Augmenter le nombre de points pour pouvoir ensuite rééchantillonner
        limit = limit * 60 // int(interval[:-1])
    
    # Récupérer les données
    df = crypto_compare.get_historical_data(symbol, limit=limit, interval=api_interval)
    
    # Rééchantillonner si nécessaire
    if interval in ["5m", "15m"] and not df.empty:
        df = df.resample(interval).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
    elif interval == "4h" and not df.empty:
        df = df.resample("4h").agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
    
    return df

def fetch_current_prices(symbols):
    """
    Récupère les prix actuels pour une liste de cryptomonnaies
    
    Args:
        symbols (list): Liste des symboles de cryptomonnaies
        
    Returns:
        dict: Dictionnaire des prix actuels {symbole: prix}
    """
    return crypto_compare.get_current_prices(symbols)