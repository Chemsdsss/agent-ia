import os, requests
from typing import Optional

TOKEN = config["github_token"]
BASE = "https://api.github.com"

def _headers():
    return {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

def create_repo(name: str, private: bool = False) -> str:
    data = {"name": name, "private": private, "auto_init": True}
    r = requests.post(f"{BASE}/user/repos", json=data, headers=_headers())
    return f"Répo créé : {r.json().get('html_url', 'erreur')}" if r.status_code == 201 else f"Erreur: {r.text}"

def list_issues(owner: str, repo: str) -> str:
    r = requests.get(f"{BASE}/repos/{owner}/{repo}/issues", headers=_headers())
    if r.status_code != 200:
        return f"Erreur: {r.text}"
    issues = r.json()
    if not issues:
        return "Aucune issue."
    return "\n".join(f"#{i['number']} {i['title']} ({i['state']})" for i in issues)

def create_issue(owner: str, repo: str, title: str, body: str = "") -> str:
    data = {"title": title, "body": body}
    r = requests.post(f"{BASE}/repos/{owner}/{repo}/issues", json=data, headers=_headers())
    return f"Issue créée : {r.json().get('html_url', 'erreur')}" if r.status_code == 201 else f"Erreur: {r.text}"

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_repo",
            "description": "Crée un nouveau dépôt GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nom du dépôt."},
                    "private": {"type": "boolean", "description": "Privé ? (défaut: false)"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_issues",
            "description": "Liste les issues d'un dépôt GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Propriétaire du dépôt."},
                    "repo": {"type": "string", "description": "Nom du dépôt."}
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue",
            "description": "Crée une issue dans un dépôt GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["owner", "repo", "title"]
            }
        }
    }
]

def run(tool_name: str, args: dict) -> str:
    if tool_name == "create_repo": return create_repo(**args)
    elif tool_name == "list_issues": return list_issues(**args)
    elif tool_name == "create_issue": return create_issue(**args)
    else: return f"Outil GitHub inconnu: {tool_name}"
