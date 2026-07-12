import requests
import xml.etree.ElementTree as ET

GOOGLE_NEWS_RSS = "https://news.google.com/rss"

def get_news(country: str = "fr", category: str = "technology", page_size: int = 5) -> str:
    """Récupère les titres d'actualité via Google News RSS."""
    try:
        # Google News RSS avec paramètres de langue et catégorie
        url = f"{GOOGLE_NEWS_RSS}/headlines?hl={country}&gl={country}&ceid={country}:{country}&topic={category}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LIA/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        items = root.findall(".//item")
        if not items:
            return "Aucune actualité trouvée."
        result = []
        for item in items[:page_size]:
            title = item.find("title").text
            source = item.find("source").text if item.find("source") is not None else "?"
            result.append(f"- {title} ({source})")
        return "\n".join(result)
    except Exception as e:
        return f"Erreur lors de la récupération des actualités : {e}"

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_news",
        "description": "Récupère les titres de l'actualité via Google News RSS (gratuit).",
        "parameters": {
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "Code pays (fr, us, de...)."},
                "category": {"type": "string", "description": "Catégorie: technology, business, sports..."},
                "page_size": {"type": "integer", "description": "Nombre d'articles (max 10)."}
            },
            "required": []
        }
    }
}

def run(**args) -> str:
    return get_news(**args)
