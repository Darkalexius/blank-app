import ccxt
from datetime import datetime
import json
from database import Session, save_user_preference, get_user_preference
import google_auth_oauthlib.flow

# Liste des échanges supportés
SUPPORTED_EXCHANGES = [
    "binance", "coinbasepro", "kraken", "kucoin", "ftx", "bitfinex", "huobi", "alpaca"
]

def get_available_exchanges():
    """
    Retourne la liste des échanges disponibles

    Returns:
        list: Liste des échanges supportés
    """
    return SUPPORTED_EXCHANGES

def initialize_exchange(exchange_id, api_key=None, api_secret=None, test_mode=True, additional_params=None):
    """
    Initialise une connexion à un échange

    Args:
        exchange_id (str): ID de l'échange (ex: 'binance')
        api_key (str): Clé API
        api_secret (str): Secret API
        test_mode (bool): Si vrai, utilise le mode test (sandbox)
        additional_params (dict): Paramètres supplémentaires pour l'échange

    Returns:
        ccxt.Exchange or None: Instance de l'échange ou None en cas d'erreur
    """
    try:
        # Vérifier si l'exchange est supporté
        if exchange_id.lower() not in SUPPORTED_EXCHANGES:
            raise ValueError(f"L'échange {exchange_id} n'est pas supporté")

        # Paramètres de base
        params = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        }

        # Ajouter des paramètres supplémentaires si fournis
        if additional_params:
            params.update(additional_params)

        # Créer l'instance d'échange
        exchange_class = getattr(ccxt, exchange_id.lower())
        exchange = exchange_class(params)

        # Configurer pour le mode test si nécessaire
        if test_mode and exchange.has.get('test', False):
            exchange.set_sandbox_mode(True)

        if (api_key and api_secret) or (exchange_id.lower() == "alpaca" and test_mode):
            try:
                # Pour Alpaca en mode paper
                if exchange_id.lower() == "alpaca":
                    if test_mode:
                        if not (api_key and api_secret):
                            raise Exception("Clés API requises même en mode test pour Alpaca")
                        exchange.urls['api'] = {
                            'public': 'https://paper-api.alpaca.markets',
                            'private': 'https://paper-api.alpaca.markets'
                        }
                        # Configuration spécifique pour Alpaca paper trading
                        exchange.options['enableRateLimit'] = True
                        exchange.options['defaultType'] = 'spot'
                        exchange.options['adjustForTimeDifference'] = True
                        exchange.setSandboxMode(True)
                    print(f"Mode {'paper' if test_mode else 'live'} trading activé pour {exchange_id}")
                    
                    # Force l'initialisation du trader pour Alpaca
                    exchange.checkRequiredCredentials()
                    if not hasattr(exchange, 'trader'):
                        exchange.trader = True

                    try:
                        # Initialiser les marchés spécifiquement pour Alpaca
                        exchange.load_markets(True)  # Force reload
                    except Exception as e:
                        print(f"Erreur lors de l'initialisation des marchés Alpaca: {str(e)}")
                        # Continuer avec les fonctionnalités limitées
                        pass
                else:
                    # Pour les autres échanges
                    exchange.load_markets()
                exchange.fetch_balance()
                print(f"Connexion réussie à {exchange_id}" + (" (mode test)" if test_mode else ""))
            except ccxt.AuthenticationError as e:
                print(f"Erreur d'authentification: {str(e)}")
                if test_mode:
                    print("Note: Vous êtes en mode test (sandbox). Certains échanges ne supportent pas le mode test.")
                if not (exchange_id.lower() == "alpaca" and test_mode):
                    raise Exception(f"Clés API invalides pour {exchange_id}: {str(e)}")
            except Exception as e:
                print(f"Erreur lors du test de connexion: {str(e)}")
                if not (exchange_id.lower() == "alpaca" and test_mode):
                    raise

        return exchange

    except Exception as e:
        print(f"Erreur lors de l'initialisation de l'échange {exchange_id}: {e}")
        return None

def initialize_oauth_flow(client_config, scopes=None):
    """
    Initialise le flux OAuth

    Args:
        client_config (dict): Configuration du client OAuth
        scopes (list): Liste des autorisations demandées

    Returns:
        Flow: Instance du flux OAuth
    """
    if scopes is None:
        scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]

    oauth_flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=scopes
    )

    return oauth_flow

def save_exchange_credentials(exchange_id, api_key, api_secret, user_id="default"):
    """
    Sauvegarde les identifiants de l'échange dans la base de données

    Args:
        exchange_id (str): ID de l'échange
        api_key (str): Clé API
        api_secret (str): Secret API
        user_id (str): Identifiant de l'utilisateur
    """
    try:
        # Crypter les clés (dans une application réelle, utilisez une méthode de chiffrement)
        # Pour cette démo, nous stockons simplement les clés directement, mais dans un environnement
        # de production, il faudrait les chiffrer
        save_user_preference(f"exchange_{exchange_id}_api_key", api_key, user_id)
        save_user_preference(f"exchange_{exchange_id}_api_secret", api_secret, user_id)
        save_user_preference("selected_exchange", exchange_id, user_id)

        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des identifiants: {e}")
        return False

def get_exchange_credentials(exchange_id, user_id="default"):
    """
    Récupère les identifiants de l'échange depuis la base de données

    Args:
        exchange_id (str): ID de l'échange
        user_id (str): Identifiant de l'utilisateur

    Returns:
        tuple: (api_key, api_secret) ou (None, None) si pas trouvé
    """
    try:
        api_key = get_user_preference(f"exchange_{exchange_id}_api_key", None, user_id)
        api_secret = get_user_preference(f"exchange_{exchange_id}_api_secret", None, user_id)

        return api_key, api_secret
    except Exception as e:
        print(f"Erreur lors de la récupération des identifiants: {e}")
        return None, None

def get_account_balance(exchange):
    """
    Récupère le solde du compte

    Args:
        exchange (ccxt.Exchange): Instance de l'échange

    Returns:
        dict: Soldes du compte
    """
    try:
        balance = exchange.fetch_balance()

        # Filtrer pour ne garder que les soldes non-nuls
        filtered_balance = {}
        for currency, amount in balance['total'].items():
            if amount > 0:
                filtered_balance[currency] = {
                    'free': balance['free'].get(currency, 0),
                    'used': balance['used'].get(currency, 0),
                    'total': amount
                }

        return filtered_balance
    except Exception as e:
        print(f"Erreur lors de la récupération du solde: {e}")
        return {}

def place_market_order(exchange, symbol, side, amount):
    """
    Place un ordre au marché

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        symbol (str): Symbole de la paire (ex: 'BTC/USD')
        side (str): Type d'ordre ('buy' ou 'sell')
        amount (float): Quantité à acheter/vendre

    Returns:
        dict: Détails de l'ordre ou None en cas d'erreur
    """
    try:
        # Vérifier que le marché est disponible
        exchange.load_markets()
        if symbol not in exchange.markets:
            formatted_markets = [m for m in exchange.markets.keys()]
            raise ValueError(f"Marché {symbol} non disponible. Marchés disponibles: {formatted_markets[:10]}...")

        # Placer l'ordre
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=amount
        )

        # Sauvegarder l'ordre dans la base de données
        save_order_to_db(exchange.id, order)

        return order
    except Exception as e:
        print(f"Erreur lors du placement de l'ordre: {e}")
        return None

def place_limit_order(exchange, symbol, side, amount, price):
    """
    Place un ordre limité

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        symbol (str): Symbole de la paire (ex: 'BTC/USD')
        side (str): Type d'ordre ('buy' ou 'sell')
        amount (float): Quantité à acheter/vendre
        price (float): Prix limite

    Returns:
        dict: Détails de l'ordre ou None en cas d'erreur
    """
    try:
        # Vérifier que le marché est disponible
        exchange.load_markets()
        if symbol not in exchange.markets:
            formatted_markets = [m for m in exchange.markets.keys()]
            raise ValueError(f"Marché {symbol} non disponible. Marchés disponibles: {formatted_markets[:10]}...")

        # Placer l'ordre
        order = exchange.create_order(
            symbol=symbol,
            type='limit',
            side=side,
            amount=amount,
            price=price
        )

        # Sauvegarder l'ordre dans la base de données
        save_order_to_db(exchange.id, order)

        return order
    except Exception as e:
        print(f"Erreur lors du placement de l'ordre: {e}")
        return None

def get_order_status(exchange, order_id, symbol=None):
    """
    Récupère le statut d'un ordre

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        order_id (str): ID de l'ordre
        symbol (str): Symbole de la paire (requis pour certains échanges)

    Returns:
        dict: Détails de l'ordre ou None en cas d'erreur
    """
    try:
        order = exchange.fetch_order(order_id, symbol)
        return order
    except Exception as e:
        print(f"Erreur lors de la récupération du statut de l'ordre: {e}")
        return None

def cancel_order(exchange, order_id, symbol=None):
    """
    Annule un ordre

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        order_id (str): ID de l'ordre
        symbol (str): Symbole de la paire (requis pour certains échanges)

    Returns:
        dict: Confirmation de l'annulation ou None en cas d'erreur
    """
    try:
        result = exchange.cancel_order(order_id, symbol)
        return result
    except Exception as e:
        print(f"Erreur lors de l'annulation de l'ordre: {e}")
        return None

def get_open_orders(exchange, symbol=None):
    """
    Récupère la liste des ordres ouverts

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        symbol (str): Symbole de la paire (optionnel)

    Returns:
        list: Liste des ordres ouverts
    """
    try:
        orders = exchange.fetch_open_orders(symbol)
        return orders
    except Exception as e:
        print(f"Erreur lors de la récupération des ordres ouverts: {e}")
        return []

def get_order_history(exchange, symbol=None, limit=50):
    """
    Récupère l'historique des ordres

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        symbol (str): Symbole de la paire (optionnel)
        limit (int): Nombre maximum d'ordres à récupérer

    Returns:
        list: Liste des ordres historiques
    """
    try:
        orders = exchange.fetch_closed_orders(symbol, limit=limit)
        return orders
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique des ordres: {e}")
        return []

def get_ticker(exchange, symbol):
    """
    Récupère les informations de marché pour un symbole

    Args:
        exchange (ccxt.Exchange): Instance de l'échange
        symbol (str): Symbole de la paire (ex: 'BTC/USD')

    Returns:
        dict: Informations de marché
    """
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker
    except Exception as e:
        print(f"Erreur lors de la récupération des informations de marché: {e}")
        return None

def get_available_pairs(exchange):
    """
    Récupère la liste des paires disponibles sur l'échange

    Args:
        exchange (ccxt.Exchange): Instance de l'échange

    Returns:
        list: Liste des paires disponibles
    """
    try:
        exchange.load_markets()
        return list(exchange.markets.keys())
    except Exception as e:
        print(f"Erreur lors de la récupération des paires disponibles: {e}")
        return []

# Fonctions pour interagir avec la base de données
def save_order_to_db(exchange_id, order_details):
    """
    Sauvegarde un ordre dans la base de données

    Args:
        exchange_id (str): ID de l'échange
        order_details (dict): Détails de l'ordre
    """
    from database import Order

    session = Session()

    try:
        # Créer un objet Order
        order = Order(
            exchange_id=exchange_id,
            order_id=str(order_details['id']),
            symbol=order_details['symbol'],
            type=order_details['type'],
            side=order_details['side'],
            amount=order_details['amount'],
            price=order_details.get('price'),
            status=order_details['status'],
            timestamp=datetime.fromtimestamp(order_details['timestamp'] / 1000) if 'timestamp' in order_details else datetime.now(),
            order_details=json.dumps(order_details)
        )

        session.add(order)
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde de l'ordre: {e}")

    finally:
        session.close()

def update_order_status_in_db(exchange_id, order_id, new_status, updated_details=None):
    """
    Met à jour le statut d'un ordre dans la base de données

    Args:
        exchange_id (str): ID de l'échange
        order_id (str): ID de l'ordre
        new_status (str): Nouveau statut de l'ordre
        updated_details (dict): Détails mis à jour de l'ordre
    """
    from database import Order

    session = Session()

    try:
        # Récupérer l'ordre
        order = session.query(Order).filter(
            Order.exchange_id == exchange_id,
            Order.order_id == str(order_id)
        ).first()

        if order:
            order.status = new_status
            if updated_details:
                order.order_details = json.dumps(updated_details)

            session.commit()

    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la mise à jour du statut de l'ordre: {e}")

    finally:
        session.close()

def get_orders_from_db(exchange_id=None, symbol=None, status=None, limit=50):
    """
    Récupère les ordres depuis la base de données

    Args:
        exchange_id (str): ID de l'échange (optionnel)
        symbol (str): Symbole de la paire (optionnel)
        status (str): Statut de l'ordre (optionnel)
        limit (int): Nombre maximum d'ordres à récupérer

    Returns:
        list: Liste des ordres
    """
    from database import Order

    session = Session()

    try:
        query = session.query(Order)

        if exchange_id:
            query = query.filter(Order.exchange_id == exchange_id)

        if symbol:
            query = query.filter(Order.symbol == symbol)

        if status:
            query = query.filter(Order.status == status)

        query = query.order_by(Order.timestamp.desc()).limit(limit)

        return query.all()

    except Exception as e:
        print(f"Erreur lors de la récupération des ordres: {e}")
        return []

    finally:
        session.close()