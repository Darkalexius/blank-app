import os
import json
from datetime import datetime

class IAAgent:
    def __init__(self):
        self._password = "admin123"  # À changer pour un vrai mot de passe
        self.conversation_history = []
        
    def authenticate(self, password):
        return password == self._password
        
    def process_query(self, query, context=None):
        try:
            # Ajouter la requête à l'historique
            self.conversation_history.append({
                "role": "user",
                "content": query,
                "timestamp": datetime.now().isoformat()
            })
            
            # Analyse de base de la requête
            response = {
                "type": self._categorize_query(query),
                "response": self._generate_response(query, context),
                "timestamp": datetime.now().isoformat()
            }
            
            # Ajouter la réponse à l'historique
            self.conversation_history.append({
                "role": "assistant",
                "content": response["response"],
                "timestamp": response["timestamp"]
            })
            
            return response
            
        except Exception as e:
            return {
                "type": "error",
                "response": f"Erreur lors du traitement de la requête: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _categorize_query(self, query):
        query = query.lower()
        if any(word in query for word in ["analyse", "prédis", "tendance"]):
            return "analysis"
        elif any(word in query for word in ["acheter", "vendre", "trader"]):
            return "trading"
        else:
            return "general"
            
    def _generate_response(self, query, context=None):
        query_type = self._categorize_query(query)
        
        if query_type == "analysis":
            return "Pour analyser les marchés, je vous conseille de regarder les indicateurs techniques comme le RSI et le MACD, ainsi que le volume des échanges."
        elif query_type == "trading":
            return "Pour le trading, assurez-vous de bien gérer vos risques et de ne pas investir plus que ce que vous pouvez vous permettre de perdre."
        else:
            return "Je suis votre assistant IA pour l'analyse et le trading de cryptomonnaies. Comment puis-je vous aider ?"
            
    def get_conversation_history(self):
        return self.conversation_history