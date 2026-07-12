import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

BASE_URL = "https://www.youtube.com/results?search_query="

def search_videos(query: str, max_results: int = 3) -> str:
    """Recherche des vidéos YouTube sans clé API, en scrapant la page de résultats."""
    try:
        url = BASE_URL + quote(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Récupération des rendus vidéo dans le JSON initial
        script_tag = soup.find("script", string=lambda t: t and "var ytInitialData" in t)
        if not script_tag:
            return "Impossible de parser les résultats YouTube."
        import json
        data = json.loads(script_tag.string.split("var ytInitialData = ")[1].split(";</script>")[0])
        items = []
        # Navigation dans l'arbre JSON pour trouver les vidéos
        contents = (data.get("contents", {})
                    .get("twoColumnSearchResultsRenderer", {})
                    .get("primaryContents", {})
                    .get("sectionListRenderer", {})
                    .get("contents", [{}])[0]
                    .get("itemSectionRenderer", {})
                    .get("contents", []))
        for vid in contents:
            renderer = vid.get("videoRenderer")
            if renderer and len(items) < max_results:
                title = renderer.get("title", {}).get("runs", [{}])[0].get("text", "Sans titre")
                video_id = renderer.get("videoId", "")
                if video_id:
                    items.append(f"{title} → https://youtu.be/{video_id}")
        if not items:
            return "Aucune vidéo trouvée."
        return "\n".join(items)
    except Exception as e:
        return f"Erreur lors de la recherche YouTube : {e}"

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_videos",
        "description": "Recherche des vidéos YouTube sans clé API.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Mots-clés."},
                "max_results": {"type": "integer", "description": "Nombre de résultats (défaut: 3)"}
            },
            "required": ["query"]
        }
    }
}

def run(**args) -> str:
    return search_videos(**args)
