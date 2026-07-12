import requests
from typing import Optional

def web_search(query: str, num_results: int = 3) -> str:
    """Recherche DuckDuckGo (gratuite, sans clé API). Retourne les résultats formatés."""
    try:
        # Utilise l'API DuckDuckGo instant (non officielle mais fiable)
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=5
        )
        data = response.json()
        # Résumé principal
        abstract = data.get("Abstract", "")
        # Résultats connexes
        related = [r["Text"] for r in data.get("RelatedTopics", [])[:num_results]]
        result = abstract if abstract else ""
        if related:
            result += "\n\nRésultats:\n" + "\n".join(f"- {r}" for r in related)
        return result.strip() or "Aucun résultat."
    except Exception as e:
        return f"Erreur recherche: {e}"

def http_get(url: str) -> str:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text[:2000]  # limiter la taille
    except Exception as e:
        return f"Erreur HTTP: {e}"
