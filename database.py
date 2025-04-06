import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Créer le moteur de base de données SQLite
DATABASE_URL = "sqlite:///crypto_analysis.db"
engine = create_engine(DATABASE_URL)

# Créer une classe de base pour nos modèles
Base = declarative_base()

# Définir les modèles de base de données
class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<PriceHistory(symbol='{self.symbol}', timestamp='{self.timestamp}', close={self.close})>"

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    indicator_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<TechnicalIndicator(symbol='{self.symbol}', indicator='{self.indicator_name}', value={self.value})>"

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    signal_type = Column(String, nullable=False)  # 'achat', 'vente', 'neutre'
    reason = Column(String, nullable=True)
    indicators_data = Column(JSON, nullable=True)  # Stockage des données d'indicateurs associées
    executed = Column(Boolean, default=False)
    price_at_signal = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<Signal(symbol='{self.symbol}', type='{self.signal_type}', timestamp='{self.timestamp}')>"

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True, default="default")
    preference_name = Column(String, nullable=False)
    preference_value = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<UserPreference(user='{self.user_id}', name='{self.preference_name}', value='{self.preference_value}')>"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(String, nullable=False, index=True)
    order_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)  # 'market', 'limit', etc.
    side = Column(String, nullable=False)  # 'buy', 'sell'
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # Peut être NULL pour les ordres market
    status = Column(String, nullable=False, index=True)  # 'open', 'closed', 'canceled'
    timestamp = Column(DateTime, nullable=False)
    order_details = Column(JSON, nullable=True)  # Détails complets de l'ordre
    
    def __repr__(self):
        return f"<Order(exchange='{self.exchange_id}', id='{self.order_id}', symbol='{self.symbol}', status='{self.status}')>"

# Créer les tables dans la base de données
def init_db():
    Base.metadata.create_all(engine)

# Créer une session pour interagir avec la base de données
Session = sessionmaker(bind=engine)

# Fonctions pour interagir avec la base de données
def save_price_history(symbol, df):
    """
    Sauvegarde l'historique des prix d'une cryptomonnaie dans la base de données
    
    Args:
        symbol (str): Symbole de la cryptomonnaie
        df (pandas.DataFrame): DataFrame contenant les données OHLCV
    """
    session = Session()
    
    try:
        # Supprimer les anciennes données pour ce symbole (optionnel)
        # session.query(PriceHistory).filter(PriceHistory.symbol == symbol).delete()
        
        # Préparer les nouveaux enregistrements
        records = []
        for index, row in df.iterrows():
            price_record = PriceHistory(
                symbol=symbol,
                timestamp=index,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            records.append(price_record)
        
        # Ajouter les enregistrements
        session.bulk_save_objects(records)
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde des prix pour {symbol}: {e}")
    
    finally:
        session.close()

def save_technical_indicators(symbol, df):
    """
    Sauvegarde les indicateurs techniques d'une cryptomonnaie dans la base de données
    
    Args:
        symbol (str): Symbole de la cryptomonnaie
        df (pandas.DataFrame): DataFrame contenant les indicateurs techniques
    """
    session = Session()
    
    try:
        # Liste des colonnes d'indicateurs techniques à sauvegarder
        indicator_columns = [
            'RSI', 'MACD', 'MACD_signal', 'MACD_hist',
            'BB_upper', 'BB_middle', 'BB_lower',
            'EMA_5', 'EMA_20', 'SMA_50', 'SMA_200'
        ]
        
        # Préparer les enregistrements
        records = []
        for index, row in df.iterrows():
            for indicator in indicator_columns:
                if indicator in df.columns and not pd.isna(row.get(indicator)):
                    indicator_record = TechnicalIndicator(
                        symbol=symbol,
                        timestamp=index,
                        indicator_name=indicator,
                        value=float(row[indicator])
                    )
                    records.append(indicator_record)
        
        # Ajouter les enregistrements
        if records:
            session.bulk_save_objects(records)
            session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde des indicateurs pour {symbol}: {e}")
    
    finally:
        session.close()

def save_signal(symbol, signal_type, reason, indicators_data=None, price_at_signal=None):
    """
    Sauvegarde un signal d'achat/vente dans la base de données
    
    Args:
        symbol (str): Symbole de la cryptomonnaie
        signal_type (str): Type de signal ('achat', 'vente', 'neutre')
        reason (str): Raison du signal
        indicators_data (dict): Données d'indicateurs associées
        price_at_signal (float): Prix au moment du signal
    """
    session = Session()
    
    try:
        signal = Signal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=signal_type,
            reason=reason,
            indicators_data=indicators_data,
            price_at_signal=price_at_signal
        )
        
        session.add(signal)
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde du signal pour {symbol}: {e}")
    
    finally:
        session.close()

def save_user_preference(preference_name, preference_value, user_id="default"):
    """
    Sauvegarde une préférence utilisateur dans la base de données
    
    Args:
        preference_name (str): Nom de la préférence
        preference_value (str): Valeur de la préférence
        user_id (str): Identifiant de l'utilisateur
    """
    session = Session()
    
    try:
        # Vérifier si la préférence existe déjà
        existing_pref = session.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_name == preference_name
        ).first()
        
        if existing_pref:
            # Mettre à jour la valeur existante
            existing_pref.preference_value = preference_value
        else:
            # Créer une nouvelle préférence
            pref = UserPreference(
                user_id=user_id,
                preference_name=preference_name,
                preference_value=preference_value
            )
            session.add(pref)
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la sauvegarde de la préférence {preference_name}: {e}")
    
    finally:
        session.close()

def get_user_preference(preference_name, default_value=None, user_id="default"):
    """
    Récupère une préférence utilisateur de la base de données
    
    Args:
        preference_name (str): Nom de la préférence
        default_value: Valeur par défaut si la préférence n'existe pas
        user_id (str): Identifiant de l'utilisateur
        
    Returns:
        str: Valeur de la préférence
    """
    session = Session()
    
    try:
        pref = session.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_name == preference_name
        ).first()
        
        if pref:
            return pref.preference_value
        else:
            return default_value
        
    except Exception as e:
        print(f"Erreur lors de la récupération de la préférence {preference_name}: {e}")
        return default_value
    
    finally:
        session.close()

def get_recent_signals(limit=10):
    """
    Récupère les signaux récents de la base de données
    
    Args:
        limit (int): Nombre maximum de signaux à récupérer
        
    Returns:
        list: Liste des signaux récents
    """
    session = Session()
    
    try:
        signals = session.query(Signal).order_by(Signal.timestamp.desc()).limit(limit).all()
        return signals
        
    except Exception as e:
        print(f"Erreur lors de la récupération des signaux récents: {e}")
        return []
    
    finally:
        session.close()

def get_price_history(symbol, start_date=None, end_date=None):
    """
    Récupère l'historique des prix d'une cryptomonnaie de la base de données
    
    Args:
        symbol (str): Symbole de la cryptomonnaie
        start_date (datetime): Date de début
        end_date (datetime): Date de fin
        
    Returns:
        list: Liste des données de prix
    """
    session = Session()
    
    try:
        query = session.query(PriceHistory).filter(PriceHistory.symbol == symbol)
        
        if start_date:
            query = query.filter(PriceHistory.timestamp >= start_date)
        
        if end_date:
            query = query.filter(PriceHistory.timestamp <= end_date)
        
        query = query.order_by(PriceHistory.timestamp)
        
        return query.all()
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique des prix pour {symbol}: {e}")
        return []
    
    finally:
        session.close()

# Initialiser la base de données au démarrage
init_db()