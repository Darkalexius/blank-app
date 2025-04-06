# Ce fichier sert de pont entre l'application et l'API de données
# Il importe et expose les fonctions du module crypto_compare_api.py

from crypto_compare_api import (
    get_available_cryptocurrencies,
    fetch_cryptocurrency_data,
    fetch_current_prices
)

# Ces fonctions sont importées de crypto_compare_api.py et prêtes à être utilisées
# get_available_cryptocurrencies() - Récupère la liste des cryptomonnaies disponibles
# fetch_cryptocurrency_data(symbol, period, interval) - Récupère les données historiques
# fetch_current_prices(symbols) - Récupère les prix actuels
