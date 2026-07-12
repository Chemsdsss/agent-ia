import os
import shutil
import subprocess
import requests
import json
from datetime import datetime
from typing import Dict, Any

# ---------------------------------------------------------------------
# Mémoire persistante (faits + préférences)
# ---------------------------------------------------------------------
MEMORY_FILE = "memory.json"

def _load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"facts": [], "prefs": {}}

def _save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def remember(fact: str) -> str:
    """Enregistre un fait dans la mémoire."""
    mem = _load_memory()
    mem["facts"].append(fact)
    _save_memory(mem)
    return "Mémorisé."

def recall(query: str = "") -> str:
    """Rappelle les faits mémorisés (filtrage optionnel)."""
    mem = _load_memory()
    facts = mem["facts"]
    if query:
        facts = [f for f in facts if query.lower() in f.lower()]
    if facts:
        return "\n".join(f"- {f}" for f in facts)
    return "Aucune information mémorisée."

def set_preference(key: str, value: str) -> str:
    mem = _load_memory()
    mem["prefs"][key] = value
    _save_memory(mem)
    return f"Préférence enregistrée : {key} = {value}"

def get_preference(key: str) -> str:
    mem = _load_memory()
    return mem["prefs"].get(key, "Non défini.")

# ---------------------------------------------------------------------
# Opérations sur les fichiers
# ---------------------------------------------------------------------
def backup_file(workspace_dir: str, backup_dir: str, file_path: str):
    """Crée une sauvegarde horodatée si le fichier existe."""
    full_src = os.path.join(workspace_dir, file_path)
    if not os.path.exists(full_src):
        return
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path}_{timestamp}"
    shutil.copy2(full_src, os.path.join(backup_dir, backup_name))

def write_file(workspace_dir: str, backup_dir: str, file_path: str, content: str) -> str:
    full = os.path.join(workspace_dir, file_path)
    if os.path.exists(full):
        backup_file(workspace_dir, backup_dir, file_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"[OK] Fichier '{file_path}' écrit."

def read_file(workspace_dir: str, file_path: str) -> str:
    full = os.path.join(workspace_dir, file_path)
    if not os.path.exists(full):
        return f"Fichier introuvable : {file_path}"
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

def execute_command(workspace_dir: str, command: str) -> str:
    try:
        r = subprocess.run(command, shell=True, cwd=workspace_dir,
                           capture_output=True, text=True, timeout=30)
        out = r.stdout
        if r.stderr:
            out += "\n[stderr]\n" + r.stderr
        if r.returncode != 0:
            out += f"\n[code retour : {r.returncode}]"
        return out.strip() if out else "(aucune sortie)"
    except Exception as e:
        return f"Erreur d'exécution : {e}"

def list_files(workspace_dir: str, path: str = ".") -> str:
    p = os.path.join(workspace_dir, path)
    if not os.path.exists(p):
        return f"Dossier introuvable : {path}"
    items = os.listdir(p)
    if not items:
        return "(dossier vide)"
    return "\n".join(sorted(items))

# ---------------------------------------------------------------------
# Recherche web et HTTP
# ---------------------------------------------------------------------
def web_search(query: str) -> str:
    try:
        resp = requests.get("https://api.duckduckgo.com/",
                            params={"q": query, "format": "json", "no_html": 1},
                            timeout=5)
        data = resp.json()
        abstract = data.get("AbstractText", "")
        related = [r["Text"] for r in data.get("RelatedTopics", [])[:3]]
        result = abstract if abstract else ""
        if related:
            result += "\n".join(f"- {r}" for r in related)
        return result.strip() if result else "Aucun résultat."
    except Exception as e:
        return f"Erreur recherche : {e}"

def http_get(url: str) -> str:
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.text[:2000]
    except Exception as e:
        return f"Erreur HTTP : {e}"

# ---------------------------------------------------------------------
# Définitions des outils (schémas OpenAI)
# ---------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Créer ou écraser un fichier. Sauvegarde automatique de l'ancien.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier."},
                    "content": {"type": "string", "description": "Contenu complet."}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lire le contenu d'un fichier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Exécuter une commande shell dans l'espace de travail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Commande à exécuter."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lister les fichiers et dossiers d'un répertoire.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Chemin relatif ('.' pour la racine)."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Rechercher une information sur le Web (DuckDuckGo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mots-clés."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_get",
            "description": "Faire une requête HTTP GET et retourner le contenu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL complète."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Mémoriser une information pour plus tard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "Texte à retenir."}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Rappeler des informations mémorisées (filtrage par mot-clé).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mot-clé (optionnel)."}
                },
                "required": []
            }
        }
    }
]

# ---------------------------------------------------------------------
# Dispatcher principal (utilisé par l'agent)
# ---------------------------------------------------------------------
def execute_tool(tool_name: str, args: Dict[str, Any], workspace_dir: str, backup_dir: str) -> str:
    if tool_name == "write_file":
        return write_file(workspace_dir, backup_dir, args["file_path"], args["content"])
    elif tool_name == "read_file":
        return read_file(workspace_dir, args["file_path"])
    elif tool_name == "execute_command":
        return execute_command(workspace_dir, args["command"])
    elif tool_name == "list_files":
        return list_files(workspace_dir, args.get("path", "."))
    elif tool_name == "web_search":
        return web_search(args["query"])
    elif tool_name == "http_get":
        return http_get(args["url"])
    elif tool_name == "remember":
        return remember(args["fact"])
    elif tool_name == "recall":
        return recall(args.get("query", ""))
    else:
        return f"Outil inconnu : {tool_name}"
