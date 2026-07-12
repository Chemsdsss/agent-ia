#!/usr/bin/env python3
"""
Utilitaires de configuration et d'appel à l'API (Groq ou Ollama).
"""
import json
import os
import requests
from typing import List, Dict, Optional, Any

def load_config(config_path: str = "config.json") -> dict:
    """
    Charge la configuration depuis le fichier JSON.
    Injecte la variable d'environnement GROQ_API_KEY en tête de liste si présente.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        keys = config.get("api_keys", [])
        if env_key not in keys:
            keys.insert(0, env_key)
        config["api_keys"] = keys

    if not config.get("api_keys"):
        # En mode local, une clé factice est acceptée
        if config.get("local_mode", False):
            config["api_keys"] = ["sk-local"]
        else:
            raise ValueError(
                "Aucune clé API trouvée. Définissez GROQ_API_KEY ou ajoutez des clés dans config.json (api_keys)."
            )
    return config


def chat_completion(
    api_keys: List[str],
    model: str,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 1024,
    api_base: str = "https://api.groq.com/openai/v1",
    local_mode: bool = False,
) -> dict:
    """
    Appelle l'API de complétion de chat.

    - En mode API (local_mode=False), essaie successivement chaque clé de la liste.
    - En mode local (local_mode=True), utilise une seule requête sans Authorization.
    """
    # En mode local, on ne boucle pas sur les clés
    if local_mode:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                raise RuntimeError(f"Erreur API locale ({resp.status_code}): {resp.text[:200]}")
        except Exception as e:
            raise RuntimeError(f"Erreur de connexion au serveur local : {e}")

    # Mode API (rotation de clés)
    last_error = None
    for key in api_keys:
        try:
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    **({"tools": tools, "tool_choice": "auto"} if tools else {})
                },
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                last_error = f"Rate-limit sur clé {key[:8]}..."
            else:
                last_error = f"Erreur API ({resp.status_code}): {resp.text[:200]}"
        except Exception as e:
            last_error = str(e)
        # Passe à la clé suivante en cas d'échec

    raise RuntimeError(f"Toutes les clés API ont échoué. Dernière erreur : {last_error}")
