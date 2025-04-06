import json
import random
from datetime import datetime

def analyze_crypto_data(crypto_data, technical_indicators):
    """
    Analyse les données d'une cryptomonnaie pour obtenir des conseils d'investissement.
    
    Args:
        crypto_data (dict): Données de la cryptomonnaie (prix, volume, etc.)
        technical_indicators (dict): Indicateurs techniques calculés
        
    Returns:
        dict: Analyse et conseils d'investissement
    """
    try:
        symbol = crypto_data.get("symbol", "")
        current_price = crypto_data.get("current_price", 0)
        price_change_24h = crypto_data.get("price_change_percentage_24h", 0)
        price_change_7d = crypto_data.get("price_change_percentage_7d", 0)
        
        # Récupérer les indicateurs techniques clés
        rsi = technical_indicators.get("RSI", 50)
        macd = technical_indicators.get("MACD", 0)
        macd_signal = technical_indicators.get("MACD_signal", 0)
        bb_upper = technical_indicators.get("BB_upper", 0)
        bb_middle = technical_indicators.get("BB_middle", 0)
        bb_lower = technical_indicators.get("BB_lower", 0)
        
        # Analyser le RSI
        rsi_analysis = ""
        if rsi > 70:
            rsi_analysis = f"Le RSI de {rsi:.2f} indique que {symbol} est actuellement suracheté."
            rsi_signal = "vendre"
        elif rsi < 30:
            rsi_analysis = f"Le RSI de {rsi:.2f} indique que {symbol} est actuellement survendu."
            rsi_signal = "acheter"
        else:
            rsi_analysis = f"Le RSI de {rsi:.2f} indique que {symbol} est dans une zone neutre."
            rsi_signal = "attendre"
        
        # Analyser le MACD
        macd_analysis = ""
        if macd > macd_signal:
            macd_analysis = f"Le MACD ({macd:.2f}) est au-dessus de sa ligne de signal ({macd_signal:.2f}), indiquant une tendance haussière."
            macd_signal = "acheter"
        else:
            macd_analysis = f"Le MACD ({macd:.2f}) est en-dessous de sa ligne de signal ({macd_signal:.2f}), indiquant une tendance baissière."
            macd_signal = "vendre"
        
        # Analyser les Bandes de Bollinger
        bb_analysis = ""
        if current_price > bb_upper:
            bb_analysis = f"Le prix actuel ({current_price:.2f}) est au-dessus de la bande supérieure de Bollinger ({bb_upper:.2f}), suggérant une condition de surachat."
            bb_signal = "vendre"
        elif current_price < bb_lower:
            bb_analysis = f"Le prix actuel ({current_price:.2f}) est en-dessous de la bande inférieure de Bollinger ({bb_lower:.2f}), suggérant une condition de survente."
            bb_signal = "acheter"
        else:
            bb_analysis = f"Le prix actuel ({current_price:.2f}) est entre les bandes de Bollinger, suggérant une volatilité normale."
            bb_signal = "attendre"
        
        # Déterminer la recommandation finale
        signals = [rsi_signal, macd_signal, bb_signal]
        buy_count = signals.count("acheter")
        sell_count = signals.count("vendre")
        
        if buy_count > sell_count:
            recommendation = "acheter"
            reason = "La majorité des indicateurs techniques suggèrent une tendance haussière."
        elif sell_count > buy_count:
            recommendation = "vendre"
            reason = "La majorité des indicateurs techniques suggèrent une tendance baissière."
        else:
            recommendation = "attendre"
            reason = "Les indicateurs techniques donnent des signaux mixtes."
        
        # Évaluer le niveau de risque
        # Base: 3 (modéré)
        # +1 si forte volatilité, -1 si faible volatilité
        # +1 si signaux contradictoires
        
        risk_level = 3
        if abs(price_change_24h) > 10 or abs(price_change_7d) > 20:
            risk_level += 1
        elif abs(price_change_24h) < 2 and abs(price_change_7d) < 5:
            risk_level = max(1, risk_level - 1)
            
        if len(set(signals)) == 3:  # Tous les signaux sont différents
            risk_level = min(5, risk_level + 1)
            
        # Créer l'analyse de marché
        if price_change_7d > 10:
            market_analysis = f"{symbol} a connu une forte hausse de {price_change_7d:.2f}% au cours des 7 derniers jours, indiquant un fort intérêt des investisseurs."
        elif price_change_7d < -10:
            market_analysis = f"{symbol} a subi une correction de {abs(price_change_7d):.2f}% au cours des 7 derniers jours, ce qui pourrait indiquer une pression de vente significative."
        else:
            market_analysis = f"{symbol} a évolué de {price_change_7d:.2f}% au cours des 7 derniers jours, montrant une relative stabilité."
            
        # Ajouter le contexte des 24 dernières heures
        if price_change_24h > 5:
            market_analysis += f" Sur les dernières 24 heures, la hausse de {price_change_24h:.2f}% suggère un momentum positif à court terme."
        elif price_change_24h < -5:
            market_analysis += f" La baisse de {abs(price_change_24h):.2f}% sur les dernières 24 heures pourrait indiquer un affaiblissement temporaire."
        else:
            market_analysis += f" Le prix est resté relativement stable à {price_change_24h:.2f}% sur les dernières 24 heures."
        
        # Perspectives à court terme
        if recommendation == "acheter":
            short_term = f"À court terme, {symbol} pourrait continuer sa dynamique positive. Surveillez les niveaux de résistance autour de {current_price * 1.1:.2f} et {current_price * 1.2:.2f}."
        elif recommendation == "vendre":
            short_term = f"À court terme, {symbol} pourrait faire face à des pressions de vente. Des niveaux de support potentiels se situent autour de {current_price * 0.9:.2f} et {current_price * 0.8:.2f}."
        else:
            short_term = f"À court terme, {symbol} pourrait connaître une consolidation entre {current_price * 0.95:.2f} et {current_price * 1.05:.2f}."
        
        # Perspectives à moyen terme
        medium_term = f"À moyen terme, la performance de {symbol} dépendra de l'évolution du marché global des cryptomonnaies et des développements spécifiques à ce projet."
        if random.random() > 0.5:  # Ajouter un peu de variété
            medium_term += " Surveillez les annonces des développeurs et les tendances générales du marché pour ajuster votre stratégie."
        else:
            medium_term += " Considérez une stratégie d'investissement échelonné pour profiter des fluctuations de prix."
        
        # Résumé
        summary = f"Analyse de {symbol}: {recommendation.capitalize()} - {reason} Prix actuel: {current_price:.2f}, Variation sur 7 jours: {price_change_7d:.2f}%. Niveau de risque: {risk_level}/5."
        
        # Construire le résultat
        result = {
            "analyse_marche": market_analysis,
            "analyse_technique": f"{rsi_analysis} {macd_analysis} {bb_analysis}",
            "recommandation": recommendation,
            "niveau_risque": risk_level,
            "perspectives_court_terme": short_term,
            "perspectives_moyen_terme": medium_term,
            "resume": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        return {
            "erreur": f"Erreur lors de l'analyse: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "recommandation": "indéterminée"
        }

def generate_investment_strategy(portfolio_data, risk_profile="moderate"):
    """
    Génère une stratégie d'investissement personnalisée basée sur le portefeuille actuel et le profil de risque.
    
    Args:
        portfolio_data (dict): Données du portefeuille actuel
        risk_profile (str): Profil de risque ("conservative", "moderate", "aggressive")
        
    Returns:
        dict: Stratégie d'investissement personnalisée
    """
    try:
        # Convertir le profil de risque en français
        risk_profile_fr = {
            "conservative": "conservateur",
            "moderate": "modéré",
            "aggressive": "agressif"
        }.get(risk_profile, "modéré")
        
        # Analyser le portefeuille
        total_value = 0
        portfolio_composition = {}
        
        # Crypto de base à suggérer
        top_cryptos = ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "DOT", "AVAX", "LINK", "MATIC"]
        stable_cryptos = ["USDT", "USDC", "DAI", "BUSD"]
        defi_cryptos = ["UNI", "AAVE", "COMP", "MKR", "SNX", "CAKE", "CRV"]
        
        # Cryptos détenues
        held_cryptos = list(portfolio_data.keys())
        
        # Évaluer la diversification actuelle
        if len(held_cryptos) <= 1:
            diversification = "très faible"
        elif len(held_cryptos) <= 3:
            diversification = "faible"
        elif len(held_cryptos) <= 5:
            diversification = "moyenne"
        elif len(held_cryptos) <= 8:
            diversification = "bonne"
        else:
            diversification = "excellente"
            
        # Cryptos à ajouter (celles qui ne sont pas déjà dans le portefeuille)
        cryptos_to_add = []
        
        # Recommandations basées sur le profil de risque
        if risk_profile == "conservative":
            # Profil conservateur: Bitcoin, Ethereum et stablecoins
            crypto_recommendations = ["BTC", "ETH"] + stable_cryptos
            allocation = {
                "BTC": "40%",
                "ETH": "30%",
                "Stablecoins": "20%",
                "Autres altcoins établis": "10%"
            }
            cryptos_to_add = [c for c in crypto_recommendations if c not in held_cryptos][:3]
            risk_management = "Privilégiez la sécurité avec une forte allocation en Bitcoin et Ethereum. Conservez 20% de votre portefeuille en stablecoins pour profiter des opportunités d'achat. Évitez les cryptomonnaies à petite capitalisation."
            short_term_strategy = "Achetez graduellement lors des baisses du marché (dollar cost averaging) pour réduire l'impact de la volatilité."
            long_term_strategy = "Concentrez-vous sur l'accumulation de Bitcoin et Ethereum pour une croissance stable à long terme. Rééquilibrez votre portefeuille tous les trimestres."
            
        elif risk_profile == "aggressive":
            # Profil agressif: Plus d'altcoins et de projets DeFi
            crypto_recommendations = top_cryptos[2:8] + defi_cryptos[:4]
            allocation = {
                "BTC": "20%",
                "ETH": "20%",
                "Altcoins à moyenne cap": "40%",
                "Altcoins à petite cap": "15%",
                "Stablecoins": "5%"
            }
            cryptos_to_add = [c for c in crypto_recommendations if c not in held_cryptos][:5]
            risk_management = "Profil agressif: Surveillez attentivement les projets à plus haut risque dans votre portefeuille. Définissez des seuils de prise de profit et de stop-loss clairs. Envisagez de prendre des bénéfices régulièrement."
            short_term_strategy = "Recherchez activement des opportunités de trading à court terme tout en maintenant une base solide de cryptos établies."
            long_term_strategy = "Recherchez les projets innovants dans les domaines émergents comme la DeFi, les NFT et le Web3. Révisez votre stratégie mensuellement."
            
        else:  # moderate
            # Profil modéré: Équilibre entre sécurité et opportunités
            crypto_recommendations = top_cryptos[:5] + ["DOT", "LINK"]
            allocation = {
                "BTC": "30%",
                "ETH": "25%",
                "Altcoins établis": "30%",
                "Stablecoins": "15%"
            }
            cryptos_to_add = [c for c in crypto_recommendations if c not in held_cryptos][:4]
            risk_management = "Maintenez un équilibre entre croissance et sécurité. Gardez 15% en stablecoins pour les opportunités d'achat. Limitez chaque altcoin individuel à maximum 10% de votre portefeuille."
            short_term_strategy = "Suivez une approche mixte: investissement à long terme pour BTC et ETH, avec des ajustements tactiques sur les altcoins selon les conditions du marché."
            long_term_strategy = "Diversifiez progressivement dans des projets blockchain solides avec des cas d'utilisation réels. Réévaluez votre portefeuille tous les deux mois."
            
        # Cryptos potentiellement à vendre (bas rendement ou haut risque par rapport au profil)
        cryptos_to_sell = []
        for crypto in held_cryptos:
            # Logique simple: pour un profil conservateur, suggérer de vendre les cryptos qui ne sont pas dans les recommandations
            if risk_profile == "conservative" and crypto not in ["BTC", "ETH"] + stable_cryptos:
                cryptos_to_sell.append(crypto)
            # Pour un profil modéré, garder la plupart des cryptos mais suggérer des ajustements
            elif risk_profile == "moderate" and crypto not in top_cryptos and crypto not in stable_cryptos:
                if random.random() > 0.7:  # Ajouter un peu d'aléatoire pour que ce ne soit pas toujours les mêmes suggestions
                    cryptos_to_sell.append(crypto)
        
        # Limiter le nombre de cryptos à vendre à 2 maximum
        cryptos_to_sell = cryptos_to_sell[:2]
        
        # Évaluation du portefeuille
        if not portfolio_data:
            portfolio_evaluation = "Votre portefeuille est actuellement vide. C'est le moment idéal pour commencer à construire une stratégie d'investissement basée sur votre profil de risque."
        else:
            portfolio_evaluation = f"Votre portefeuille actuel présente une diversification {diversification}. "
            
            if len(held_cryptos) == 1:
                portfolio_evaluation += f"Vous êtes actuellement investi uniquement dans {held_cryptos[0]}, ce qui présente un risque de concentration élevé."
            else:
                portfolio_evaluation += f"Vous êtes investi dans {len(held_cryptos)} cryptomonnaies différentes, ce qui "
                if diversification in ["très faible", "faible"]:
                    portfolio_evaluation += "est insuffisant pour une bonne gestion des risques."
                elif diversification == "moyenne":
                    portfolio_evaluation += "offre un niveau de diversification acceptable, mais pourrait être amélioré."
                else:
                    portfolio_evaluation += "offre une bonne protection contre la volatilité des actifs individuels."
        
        # Résumé
        summary = f"Stratégie pour un profil {risk_profile_fr}: "
        
        if not portfolio_data:
            summary += f"Commencez à construire un portefeuille diversifié avec les cryptomonnaies recommandées. Maintenez une allocation de {allocation.get('BTC', '30%')} en Bitcoin comme base solide."
        else:
            if cryptos_to_add:
                summary += f"Envisagez d'ajouter {', '.join(cryptos_to_add)} à votre portefeuille. "
            if cryptos_to_sell:
                summary += f"Reconsidérez votre position sur {', '.join(cryptos_to_sell)}. "
            summary += f"Allocation cible: {allocation.get('BTC', '30%')} BTC, {allocation.get('ETH', '20%')} ETH et {allocation.get('Altcoins établis', '30%')} en altcoins établis."
            
        # Construire le résultat
        result = {
            "evaluation_portefeuille": portfolio_evaluation,
            "allocation_recommandee": ", ".join([f"{k}: {v}" for k, v in allocation.items()]),
            "cryptos_a_ajouter": cryptos_to_add,
            "cryptos_a_vendre": cryptos_to_sell,
            "strategie_court_terme": short_term_strategy,
            "strategie_long_terme": long_term_strategy,
            "gestion_risques": risk_management,
            "resume": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        return {
            "erreur": f"Erreur lors de la génération de la stratégie: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def get_market_sentiment():
    """
    Analyse le sentiment général du marché des cryptomonnaies.
    
    Returns:
        dict: Analyse du sentiment du marché
    """
    try:
        # Simuler une analyse basée sur des données prédéfinies
        # En pratique, cette fonction pourrait utiliser des données de marché réelles
        
        # Générer un sentiment aléatoire avec une légère tendance haussière
        sentiment_options = ["haussier", "neutre", "baissier"]
        weights = [0.4, 0.4, 0.2]  # Légère tendance haussière/neutre
        sentiment_global = random.choices(sentiment_options, weights=weights)[0]
        
        # Facteurs clés selon le sentiment
        facteurs_cles = []
        if sentiment_global == "haussier":
            facteurs_cles = [
                "Adoption institutionnelle croissante des cryptomonnaies",
                "Tendance technique haussière sur Bitcoin et Ethereum",
                "Liquidité accrue sur les marchés financiers mondiaux",
                "Développements positifs dans l'écosystème DeFi",
                "Intérêt renouvelé des investisseurs particuliers"
            ]
        elif sentiment_global == "baissier":
            facteurs_cles = [
                "Incertitudes réglementaires dans plusieurs pays clés",
                "Pression de vente sur les principales cryptomonnaies",
                "Retrait des capitaux des fonds d'investissement crypto",
                "Inquiétudes concernant la scalabilité de certains réseaux",
                "Corrélation avec les marchés boursiers en baisse"
            ]
        else:  # neutre
            facteurs_cles = [
                "Consolidation du marché après une période de volatilité",
                "Signaux techniques mixtes sur les principaux actifs",
                "Attente de catalyseurs majeurs pour orienter le marché",
                "Volume d'échanges modéré indiquant une phase d'accumulation",
                "Équilibre entre les développements positifs et les défis réglementaires"
            ]
            
        # Sélectionner quelques facteurs aléatoirement pour plus de variété
        facteurs_cles = random.sample(facteurs_cles, k=min(3, len(facteurs_cles)))
        
        # Cryptos prometteuses selon le sentiment
        top_cryptos = ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "DOT", "AVAX", "LINK", "MATIC"]
        defi_cryptos = ["UNI", "AAVE", "COMP", "MKR", "SNX", "CAKE", "CRV"]
        
        if sentiment_global == "haussier":
            # En marché haussier, sélectionner mix de blue chips et altcoins à fort potentiel
            cryptos_prometteuses = ["BTC", "ETH"] + random.sample(top_cryptos[2:] + defi_cryptos, k=3)
        elif sentiment_global == "baissier":
            # En marché baissier, privilégier les valeurs refuges
            cryptos_prometteuses = ["BTC", "ETH", "BNB"] + random.sample(["USDT", "USDC"], k=1)
        else:  # neutre
            # En marché neutre, mix équilibré
            cryptos_prometteuses = random.sample(top_cryptos[:5], k=2) + random.sample(top_cryptos[5:] + defi_cryptos[:3], k=2)
        
        # Risques à surveiller
        risques_communs = [
            "Volatilité accrue du marché à court terme",
            "Évolutions réglementaires dans les principales juridictions",
            "Corrélation avec les marchés traditionnels en période d'incertitude",
            "Problèmes de sécurité et piratages potentiels d'exchanges ou de protocoles",
            "Liquidité limitée pour certains altcoins",
            "Risque de correction technique après des hausses rapides",
            "Impacts macroéconomiques sur les actifs risqués"
        ]
        
        risques_a_surveiller = random.sample(risques_communs, k=3)
        
        # Conseils généraux selon le sentiment
        if sentiment_global == "haussier":
            conseils_generaux = "Dans ce marché haussier, gardez une discipline d'investissement rigoureuse. Envisagez de prendre des bénéfices progressivement lors des hausses significatives et maintenez une réserve de liquidités pour profiter d'éventuelles corrections. Diversifiez votre portefeuille tout en gardant une position solide sur Bitcoin et Ethereum."
        elif sentiment_global == "baissier":
            conseils_generaux = "En période de marché baissier, la préservation du capital doit être prioritaire. Privilégiez les cryptomonnaies à forte capitalisation, envisagez d'augmenter vos positions en stablecoins, et évitez les altcoins à faible capitalisation plus risqués. Utilisez une stratégie d'achat échelonné (DCA) plutôt que des achats massifs."
        else:  # neutre
            conseils_generaux = "Dans ce marché neutre, c'est le moment idéal pour réévaluer votre stratégie. Concentrez-vous sur les projets ayant des fondamentaux solides et de véritables cas d'utilisation. Maintenez une allocation équilibrée entre cryptos établies et projets prometteurs, tout en gardant une réserve de stablecoins pour les opportunités futures."
        
        # Construire le résultat
        result = {
            "sentiment_global": sentiment_global,
            "facteurs_cles": facteurs_cles,
            "cryptos_prometteuses": cryptos_prometteuses,
            "risques_a_surveiller": risques_a_surveiller,
            "conseils_generaux": conseils_generaux,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        return {
            "erreur": f"Erreur lors de l'analyse du sentiment du marché: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "sentiment_global": "indéterminé"
        }

def ask_ai_advisor(question, context=None):
    """
    Répond à une question spécifique sur les cryptomonnaies.
    
    Args:
        question (str): Question à poser
        context (dict): Contexte supplémentaire (optionnel)
        
    Returns:
        str: Réponse du conseiller IA
    """
    try:
        # Mots-clés pour la détection des sujets de questions
        keywords = {
            "bitcoin": ["bitcoin", "btc", "satoshi", "nakamoto", "halving"],
            "ethereum": ["ethereum", "eth", "vitalik", "buterin", "smart contract", "contrat intelligent", "gaz", "gas", "ether"],
            "defi": ["defi", "finance décentralisée", "yield farming", "liquidity pool", "pool de liquidité", "staking", "prêt", "lending"],
            "nft": ["nft", "non-fungible", "non fongible", "collection", "art", "token"],
            "altcoins": ["altcoin", "alternative", "sol", "solana", "cardano", "ada", "ripple", "xrp", "dot", "polkadot"],
            "regulation": ["régulation", "regulation", "loi", "légal", "légale", "juridique", "impôt", "taxe", "taxes"],
            "trading": ["trading", "trader", "graphique", "chart", "chandeliers", "bougie", "support", "résistance", "tendance", "trend"],
            "wallets": ["wallet", "portefeuille", "stockage", "seed", "graine", "clé privée", "private key", "ledger", "trezor", "cold", "hot"],
            "mining": ["mining", "minage", "mineur", "miner", "preuve de travail", "proof of work", "pow", "hashrate", "asic"],
            "staking": ["staking", "stake", "preuve d'enjeu", "proof of stake", "pos", "validators", "validateurs", "récompense"],
            "general": ["crypto", "blockchain", "décentralisé", "decentralized", "token", "monnaie", "investissement", "investir"]
        }
        
        # Base de réponses par sujet
        responses = {
            "bitcoin": [
                "Bitcoin est la première et la plus grande cryptomonnaie par capitalisation de marché. Créée en 2009 par une personne ou un groupe sous le pseudonyme de Satoshi Nakamoto, Bitcoin fonctionne sur un réseau décentralisé utilisant la technologie blockchain. Sa rareté (limitée à 21 millions d'unités) et sa résistance à la censure en font un actif souvent comparé à 'l'or numérique'. Pour investir dans le Bitcoin, privilégiez une stratégie d'achat régulier (DCA) pour réduire l'impact de la volatilité.",
                "Le Bitcoin est considéré comme une réserve de valeur et un hedge contre l'inflation par de nombreux investisseurs. Son mécanisme de halving, qui réduit de moitié les récompenses des mineurs tous les 4 ans environ, crée une pression déflationniste qui a historiquement contribué à l'appréciation de son prix sur le long terme. Cependant, le Bitcoin reste un actif très volatil, et il est recommandé de n'investir que ce que vous êtes prêt à perdre.",
                "Le réseau Bitcoin utilise un mécanisme de consensus appelé Preuve de Travail (PoW), où les mineurs résolvent des problèmes cryptographiques complexes pour valider les transactions et sécuriser le réseau. Cette méthode est très sécurisée mais consomme beaucoup d'énergie, ce qui a suscité des débats sur l'impact environnemental du Bitcoin. De nombreux mineurs se tournent vers des sources d'énergie renouvelable pour atténuer cette préoccupation."
            ],
            "ethereum": [
                "Ethereum est bien plus qu'une simple cryptomonnaie. C'est une plateforme décentralisée qui permet l'exécution de 'contrats intelligents' et la création d'applications décentralisées (dApps). L'ETH (Ether) est la cryptomonnaie native qui alimente ce réseau. Ethereum a connu une évolution majeure avec son passage à Ethereum 2.0, utilisant désormais la Preuve d'Enjeu (PoS) qui est bien plus efficace énergétiquement que la Preuve de Travail (PoW).",
                "Les contrats intelligents d'Ethereum sont des programmes informatiques qui s'exécutent automatiquement lorsque certaines conditions sont remplies, sans nécessiter d'intermédiaire. Cette innovation a permis le développement de tout un écosystème de finance décentralisée (DeFi). Les frais de transaction sur Ethereum (appelés 'gas') varient en fonction de la congestion du réseau et sont payés en ETH.",
                "Ethereum continue de se développer avec plusieurs mises à jour majeures prévues pour améliorer sa scalabilité, notamment via des solutions de couche 2 comme Optimism et Arbitrum. Ces améliorations visent à réduire les frais de transaction et à augmenter la capacité du réseau, tout en maintenant sa sécurité et sa décentralisation. L'investissement dans l'ETH est généralement considéré comme moins risqué que dans les autres altcoins, mais reste plus volatile que le Bitcoin."
            ],
            "defi": [
                "La Finance Décentralisée (DeFi) représente un écosystème de services financiers opérant sur des blockchains, principalement Ethereum. Elle permet d'accéder à des services comme les prêts, l'épargne, et les échanges sans intermédiaires traditionnels comme les banques. Les principaux avantages incluent l'accessibilité mondiale, la transparence, et potentiellement des rendements plus élevés que dans la finance traditionnelle. Cependant, la DeFi comporte aussi des risques significatifs de piratage, d'erreurs dans les contrats intelligents, et une volatilité importante.",
                "Le staking et le yield farming sont des stratégies populaires dans la DeFi. Le staking consiste à verrouiller vos cryptomonnaies pour soutenir la sécurité et les opérations d'un réseau blockchain en échange de récompenses. Le yield farming, quant à lui, implique de déplacer vos actifs entre différents protocoles pour maximiser les rendements, souvent en fournissant de la liquidité aux plateformes d'échange décentralisées (DEX). Ces stratégies peuvent offrir des rendements attractifs mais comportent des risques comme l'impermanent loss (perte impermanente).",
                "Pour débuter dans la DeFi, il est recommandé de commencer avec des protocoles établis ayant fait leurs preuves en matière de sécurité, comme Aave, Compound ou Uniswap. Utilisez toujours des portefeuilles non-custodial (où vous contrôlez vos clés privées) et ne risquez qu'un capital que vous pouvez vous permettre de perdre. Restez informé sur les audits de sécurité des protocoles que vous utilisez et diversifiez vos investissements pour minimiser les risques."
            ],
            "nft": [
                "Les NFT (Non-Fungible Tokens ou Jetons Non Fongibles) sont des actifs numériques uniques représentant la propriété d'un objet spécifique, comme une œuvre d'art, un objet dans un jeu vidéo, ou même un tweet. Contrairement aux cryptomonnaies comme le Bitcoin, chaque NFT a des caractéristiques uniques et ne peut pas être échangé à égalité avec un autre NFT. Les NFT sont principalement créés sur la blockchain Ethereum, mais d'autres réseaux comme Solana ou Polygon sont également populaires pour leur faible coût de transaction.",
                "Pour investir dans les NFT, recherchez des collections avec une communauté solide, une équipe développeur transparente, et une feuille de route claire. La valeur d'un NFT est souvent liée à sa rareté, son utilité (par exemple dans les jeux ou le métaverse), et la réputation de son créateur. Soyez conscient que le marché des NFT peut être extrêmement volatil et que la liquidité peut être limitée pour certaines collections.",
                "Au-delà de l'art numérique, les NFT trouvent des applications dans de nombreux domaines: gaming (avec le concept play-to-earn), immobilier virtuel dans le métaverse, billetterie d'événements, certification de produits de luxe, et même dans les domaines de l'identité numérique et des droits d'auteur. Ces usages pratiques pourraient contribuer à l'adoption à long terme de la technologie NFT, au-delà de l'engouement spéculatif."
            ],
            "altcoins": [
                "Les altcoins (alternatives au Bitcoin) présentent des opportunités d'investissement avec un potentiel de croissance parfois supérieur à celui du Bitcoin, mais comportent généralement plus de risques. Les projets comme Solana (SOL), Cardano (ADA), ou Polkadot (DOT) visent à résoudre différents problèmes de scalabilité et d'interopérabilité. Pour investir dans les altcoins, évaluez la technologie sous-jacente, l'équipe de développement, la communauté, et les cas d'utilisation réels du projet.",
                "La diversification est cruciale lorsqu'on investit dans les altcoins. Considérez une approche où une partie significative de votre portefeuille reste investie dans des cryptomonnaies établies comme Bitcoin et Ethereum (60-80%), tandis que le reste est alloué aux altcoins avec différents niveaux de risque. Surveillez régulièrement vos investissements et soyez prêt à ajuster votre stratégie en fonction de l'évolution du marché et des progrès technologiques.",
                "Les cycles des altcoins suivent souvent ceux du Bitcoin, mais avec une volatilité amplifiée. Pendant les marchés haussiers, les altcoins peuvent surperformer le Bitcoin (période appelée 'altseason'), tandis qu'en marché baissier, ils tendent à perdre plus de valeur. Pour naviguer ces cycles, restez informé des tendances du marché, des développements technologiques, et considérez des stratégies de prise de profit régulières lorsque vos altcoins réalisent des gains significatifs."
            ],
            "regulation": [
                "La régulation des cryptomonnaies varie considérablement d'un pays à l'autre. Dans certains pays, les cryptos sont pleinement légales et bénéficient d'un cadre réglementaire clair, tandis que dans d'autres, elles peuvent être fortement restreintes ou même interdites. En France, les cryptomonnaies sont légales et encadrées par la loi PACTE, avec l'AMF (Autorité des Marchés Financiers) qui supervise les PSAN (Prestataires de Services sur Actifs Numériques).",
                "En matière de fiscalité des cryptomonnaies en France, les plus-values réalisées lors de la vente sont soumises à un prélèvement forfaitaire unique (PFU) de 30% (ou 'flat tax'), comprenant 12,8% d'impôt sur le revenu et 17,2% de prélèvements sociaux. Les transactions crypto-à-crypto ne sont pas imposables tant qu'il n'y a pas de conversion en monnaie fiat (euro, dollar, etc.). Il est essentiel de tenir un registre précis de toutes vos transactions pour faciliter votre déclaration fiscale.",
                "La régulation des cryptomonnaies continue d'évoluer rapidement. Des initiatives comme MiCA (Markets in Crypto-Assets) dans l'Union Européenne visent à établir un cadre harmonisé. Pour les investisseurs, une bonne pratique consiste à utiliser des plateformes d'échange réglementées, à conserver des enregistrements détaillés de vos transactions, et à consulter régulièrement un conseiller fiscal spécialisé dans les cryptomonnaies pour rester en conformité avec les lois en vigueur."
            ],
            "trading": [
                "Le trading de cryptomonnaies requiert discipline, stratégie et gestion des émotions. Contrairement à l'investissement à long terme, le trading implique des transactions plus fréquentes pour profiter des fluctuations de prix. Les débutants devraient commencer avec de petites sommes et privilégier des stratégies simples comme l'achat sur les supports et la vente sur les résistances. L'analyse technique, qui étudie les graphiques de prix et les indicateurs mathématiques, est largement utilisée par les traders de crypto.",
                "Les indicateurs techniques courants dans le trading de crypto incluent les moyennes mobiles (MA), l'indice de force relative (RSI), la convergence/divergence des moyennes mobiles (MACD) et les bandes de Bollinger. Ces outils peuvent aider à identifier les tendances, les niveaux de surachat/survente, et les moments potentiels d'entrée ou de sortie. Cependant, aucun indicateur n'est infaillible, et il est généralement recommandé d'en utiliser plusieurs conjointement pour confirmer les signaux.",
                "La gestion des risques est cruciale dans le trading de crypto. Une règle fondamentale est de ne jamais risquer plus de 1-2% de votre capital total sur une seule transaction. Utilisez systématiquement des ordres stop-loss pour limiter vos pertes potentielles. La règle risque/récompense suggère de ne prendre une position que si le gain potentiel est au moins 2 à 3 fois supérieur à la perte potentielle. Enfin, gardez un journal de trading pour analyser vos performances et améliorer votre stratégie au fil du temps."
            ],
            "wallets": [
                "Les portefeuilles crypto (wallets) sont des outils essentiels pour sécuriser vos actifs numériques. Ils se divisent principalement en deux catégories : les portefeuilles chauds (hot wallets), connectés à internet pour faciliter les transactions, et les portefeuilles froids (cold wallets), stockés hors ligne pour une sécurité maximale. Pour des montants importants, privilégiez un portefeuille froid comme Ledger ou Trezor. Pour les transactions quotidiennes, un portefeuille chaud comme MetaMask peut être plus pratique.",
                "La sécurité de votre portefeuille dépend de votre phrase de récupération (seed phrase), généralement composée de 12 à 24 mots. Cette phrase est la clé ultime vers vos actifs et ne doit jamais être partagée, stockée en ligne ou photographiée. Notez-la physiquement sur papier ou mieux, gravez-la sur une plaque métallique, et conservez-la dans un lieu sécurisé. Activez l'authentification à deux facteurs (2FA) lorsque c'est possible, et vérifiez toujours les adresses de destination avant d'envoyer des cryptomonnaies.",
                "Différents types de cryptomonnaies peuvent nécessiter différents portefeuilles. Par exemple, les tokens ERC-20 (basés sur Ethereum) peuvent être stockés dans des portefeuilles compatibles Ethereum comme MetaMask, Trust Wallet ou MyCrypto. Pour le Bitcoin, des options comme Electrum, BlueWallet ou les portefeuilles matériels sont populaires. Pour une gestion simplifiée de plusieurs cryptomonnaies, des portefeuilles multi-coins comme Exodus ou Atomic Wallet peuvent être pratiques, bien qu'ils offrent généralement moins de fonctionnalités spécifiques que les portefeuilles dédiés."
            ],
            "mining": [
                "Le minage de cryptomonnaies est le processus par lequel les transactions sont vérifiées et ajoutées à la blockchain. Pour le Bitcoin et certaines autres cryptos, ce processus utilise un mécanisme appelé Preuve de Travail (PoW), où les mineurs résolvent des problèmes cryptographiques complexes, nécessitant une puissance de calcul significative. En récompense, les mineurs reçoivent des tokens nouvellement créés et des frais de transaction. De nos jours, le minage rentable de Bitcoin nécessite généralement du matériel spécialisé (ASIC) et un accès à de l'électricité bon marché.",
                "Pour débuter dans le minage, vous devez d'abord choisir la cryptomonnaie à miner. Le Bitcoin est très compétitif et difficile à miner pour les particuliers, tandis que certains altcoins peuvent être plus accessibles. Ensuite, sélectionnez le matériel approprié : des ASICs pour le Bitcoin, ou des cartes graphiques puissantes (GPU) pour des cryptos comme Ethereum Classic ou Ravencoin. Calculez votre consommation électrique et utilisez des calculateurs de rentabilité en ligne pour estimer vos gains potentiels avant d'investir.",
                "Une alternative au minage solo est de rejoindre un pool de minage, où plusieurs mineurs combinent leur puissance de calcul et partagent les récompenses proportionnellement. Cela permet d'obtenir des revenus plus réguliers, bien que plus modestes. Le cloud mining, où vous louez de la puissance de minage à distance, est une autre option, mais méfiez-vous des arnaques dans ce domaine. Avec le passage d'Ethereum à la Preuve d'Enjeu, de nombreux mineurs se sont tournés vers d'autres cryptos comme Ethereum Classic, Ravencoin, ou Ergo."
            ],
            "staking": [
                "Le staking est un procédé qui consiste à verrouiller ses cryptomonnaies dans un portefeuille pour participer au fonctionnement d'un réseau blockchain utilisant la Preuve d'Enjeu (PoS). En échange, les participants reçoivent des récompenses, généralement sous forme de tokens supplémentaires. C'est comparable à un dépôt bancaire rémunéré, mais dans l'univers crypto. Les rendements varient généralement entre 3% et 20% par an, selon la cryptomonnaie et les conditions du réseau.",
                "Pour faire du staking, vous devez d'abord posséder une cryptomonnaie qui utilise le mécanisme PoS ou l'une de ses variantes, comme Cardano (ADA), Solana (SOL), Polkadot (DOT) ou Ethereum (ETH) depuis sa mise à jour. Vous pouvez ensuite utiliser un portefeuille compatible avec le staking pour cette cryptomonnaie, ou passer par une plateforme d'échange qui offre des services de staking. Chaque option présente des compromis entre simplicité, sécurité et rendement.",
                "Le staking comporte certains risques à considérer : la volatilité du prix de la cryptomonnaie staked peut entraîner des pertes supérieures aux gains du staking ; certains réseaux imposent des périodes de blocage pendant lesquelles vous ne pouvez pas retirer vos fonds ; et il existe un risque de slashing (pénalité) si votre validateur ne respecte pas les règles du réseau. Pour minimiser ces risques, diversifiez vos investissements de staking et choisissez des validateurs ou des pools de staking réputés avec un historique fiable."
            ],
            "general": [
                "Les cryptomonnaies représentent une évolution technologique et financière majeure, fonctionnant sur des réseaux décentralisés appelés blockchains. Cette technologie permet des transferts de valeur sans intermédiaires, avec transparence et résistance à la censure. Pour les investisseurs débutants, une approche prudente consiste à commencer par les cryptomonnaies établies comme Bitcoin et Ethereum, puis à diversifier progressivement vers d'autres projets après avoir acquis une bonne compréhension du marché.",
                "La stratégie d'investissement en cryptomonnaies dépend de votre profil de risque et de vos objectifs. L'achat régulier (Dollar Cost Averaging ou DCA) est recommandé pour les débutants, permettant d'étaler les investissements dans le temps et de réduire l'impact de la volatilité. Pour la sécurité, privilégiez les plateformes d'échange réglementées et transférez vos actifs vers des portefeuilles non-custodial pour un contrôle total. N'investissez que ce que vous êtes prêt à perdre, étant donné la volatilité inhérente à ce marché.",
                "L'écosystème crypto est en constante évolution, avec des innovations dans divers domaines : finance décentralisée (DeFi), tokens non-fongibles (NFT), applications décentralisées (dApps), et solutions de scalabilité (Layer 2, sidechains). Pour rester informé, suivez des sources fiables comme CoinDesk, Cointelegraph, ou The Block, ainsi que les développeurs et chercheurs réputés sur Twitter ou Discord. Participez à des communautés pour échanger des connaissances, mais gardez un esprit critique face aux conseils d'investissement, particulièrement pendant les périodes d'euphorie du marché."
            ]
        }
        
        # Détecter le sujet principal de la question
        question_lower = question.lower()
        topic_scores = {}
        
        for topic, topic_keywords in keywords.items():
            score = sum(1 for keyword in topic_keywords if keyword in question_lower)
            topic_scores[topic] = score
        
        # Déterminer le sujet avec le score le plus élevé
        best_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
        
        # Si aucun sujet spécifique n'est détecté, utiliser le sujet général
        if topic_scores[best_topic] == 0:
            best_topic = "general"
        
        # Sélectionner une réponse aléatoire du sujet
        selected_response = random.choice(responses[best_topic])
        
        # Personnaliser la réponse
        personalized_intro = f"Concernant votre question sur {best_topic}, voici ce que je peux vous dire : \n\n"
        
        return personalized_intro + selected_response
    
    except Exception as e:
        return f"Je ne peux pas répondre à cette question pour le moment. Veuillez essayer de reformuler ou poser une autre question sur les cryptomonnaies. Erreur: {str(e)}"

def save_ai_analysis_to_db(symbol, analysis_data, user_id="default"):
    """
    Sauvegarde l'analyse IA dans la base de données pour référence future.
    
    Args:
        symbol (str): Symbole de la cryptomonnaie
        analysis_data (dict): Données d'analyse
        user_id (str): Identifiant de l'utilisateur
    """
    # Cette fonction serait implémentée pour sauvegarder les analyses dans la base de données
    # pour l'instant, cette fonctionnalité est laissée comme une extension future
    pass