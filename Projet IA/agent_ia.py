import json
import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_agent_response(msg: str, history: List[Dict[str, Any]]) -> str:
    """
    Appelle un vrai LLM via OpenRouter pour générer une réponse dynamique.
    """
    if not history:
        context_text = "Aucun événement enregistré."
        latest_url = ""
    else:
        latest = history[-1]
        latest_url = latest.get('url', '')
        context_text = f"Dernier événement analysé :\n"
        context_text += f"- Verdict NIDS : {latest.get('verdict')}\n"
        context_text += f"- Probabilité d'attaque : {latest.get('attack_probability', 0):.3f}\n"
        context_text += f"- Anomalie Zero-Day : {latest.get('is_anomaly')}\n"
        context_text += f"- URL surveillée : {latest.get('url', 'Aucune')}\n"
        top_f = latest.get("top_features", [])
        if top_f:
            context_text += f"- Caractéristiques clés (SHAP) : {', '.join(top_f[:3])}\n"
            
        blocks = sum(1 for e in history if e.get("verdict") == "BLOCK")
        context_text += f"\nStatistiques globales : {blocks} blocages sur les {len(history)} derniers événements."

    system_prompt = f"""Tu es une Sentinelle IA, un expert en cybersécurité pour le système Supply Chain Control Tower (SCCT).
Ton rôle est d'expliquer les alertes réseau avec précision et de proposer des solutions de remédiation claires.
Tu peux répondre à TOUTES les questions générales concernant la sécurité informatique et la cybersécurité.
Utilise le contexte suivant pour répondre à la question de l'administrateur. Sois professionnel, concis, et base-toi sur les données fournies.
Ne mentionne pas que tu es une IA. Fournis une analyse pointue basée sur les traits SHAP.

Si tu analyses une attaque (Verdict: BLOCK) et qu'une URL surveillée est présente, ajoute obligatoirement cette balise à la fin :
![Capture d'écran du site ciblé](https://image.thum.io/get/width/800/crop/800/{latest_url})

CONTEXTE ACTUEL DU SYSTÈME NIDS :
{context_text}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:9000",
        "X-Title": "SCCT NIDS",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": msg}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            if response.status_code == 404:
                return "❌ Erreur : Le modèle IA est temporairement indisponible sur OpenRouter. Essayez plus tard."
            return f"❌ Erreur de l'Agent IA (API OpenRouter : {response.status_code})."
    except Exception as e:
        return f"❌ Impossible de joindre l'Agent IA : {str(e)}"
