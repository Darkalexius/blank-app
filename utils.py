import locale
from datetime import datetime

# Configurer le format de devise
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'fr_FR')
    except:
        pass  # Utilisation des paramètres par défaut si la locale française n'est pas disponible

def format_currency(value):
    """
    Formate un nombre en devise (USD)
    
    Args:
        value (float): Valeur à formater
        
    Returns:
        str: Valeur formatée en devise
    """
    if value is None:
        return "N/A"
    
    try:
        if value >= 1000:
            return f"${value:,.2f}"
        elif value >= 1:
            return f"${value:.2f}"
        elif value >= 0.01:
            return f"${value:.4f}"
        else:
            return f"${value:.8f}"
    except:
        return str(value)

def format_date(timestamp, format_str="%d/%m/%Y %H:%M"):
    """
    Formate un timestamp en date lisible
    
    Args:
        timestamp: Timestamp à formater
        format_str (str): Format de date désiré
        
    Returns:
        str: Date formatée
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp / 1000)
    else:
        dt = timestamp
    
    return dt.strftime(format_str)

def get_price_change_color(change_percent):
    """
    Détermine la couleur en fonction du pourcentage de changement
    
    Args:
        change_percent (float): Pourcentage de changement
        
    Returns:
        str: Code couleur CSS
    """
    if change_percent > 5:
        return "rgba(0, 255, 0, 0.7)"  # Vert vif
    elif change_percent > 0:
        return "rgba(0, 255, 0, 0.4)"  # Vert clair
    elif change_percent < -5:
        return "rgba(255, 0, 0, 0.7)"  # Rouge vif
    elif change_percent < 0:
        return "rgba(255, 0, 0, 0.4)"  # Rouge clair
    else:
        return "rgba(128, 128, 128, 0.4)"  # Gris

def calculate_interval_from_period(period):
    """
    Calcule l'intervalle de données approprié en fonction de la période sélectionnée
    
    Args:
        period (str): Période ('1d', '7d', '30d', '90d')
        
    Returns:
        str: Intervalle approprié ('1m', '5m', '15m', '1h', '4h', '1d')
    """
    intervals = {
        "1d": "1m",
        "7d": "15m",
        "30d": "1h",
        "90d": "4h"
    }
    
    return intervals.get(period, "1h")
