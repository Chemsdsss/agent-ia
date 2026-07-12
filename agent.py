#!/usr/bin/env python3
"""
Agent LIA – Version unifiée
Supporte le mode API (Groq) et le mode local (Ollama).
"""
import json
import os
import re
import time
from typing import List, Dict, Any

# ---------------------------------------------------------------------
# Imports internes
# ---------------------------------------------------------------------
from utils import chat_completion
from tools import TOOLS as CORE_TOOLS, execute_tool as core_execute
from ui import assistant, tool_use, tool_result, error, info

# ---------------------------------------------------------------------
# Imports des modules supplémentaires (optionnels mais recommandés)
# ---------------------------------------------------------------------
try:
    import github
except ImportError:
    github = None

try:
    import video
except ImportError:
    video = None

try:
    import news
except ImportError:
    news = None

try:
    import browser
except ImportError:
    browser = None

try:
    import database
except ImportError:
    database = None

try:
    import plugins
except ImportError:
    plugins = None

# ---------------------------------------------------------------------
# Prompt système
# ---------------------------------------------------------------------
SYSTEM_PROMPT = """Tu es LIA, un assistant développeur avancé et proactif.
Tu disposes de nombreux outils pour :
- Écrire/lire/exécuter des fichiers (write_file, read_file, execute_command, list_files)
- Chercher sur le web (web_search), télécharger des pages (http_get)
- Mémoriser des informations (remember) et les rappeler (recall)
- Gérer GitHub (create_repo, list_issues, create_issue) – si configuré
- Rechercher des vidéos YouTube (search_videos)
- Lire les actualités (get_news)
- Automatiser un navigateur (fetch_page, click_button)
- Interroger une base SQL (execute_sql, list_tables)
- Utiliser des plugins chargés dynamiquement

Règles :
- Si l'utilisateur demande une action, utilise l'outil approprié.
- Tu peux aussi parler normalement, sans outil.
- Pour les tâches complexes, crée un plan avec <plan>étape1; étape2</plan> (optionnel).
- Après avoir écrit du code, teste‑le et corrige les erreurs automatiquement.
- Sois concis, efficace, et propose des améliorations.
"""

# ---------------------------------------------------------------------
# Construction de la liste d'outils complète
# ---------------------------------------------------------------------
def build_all_tools():
    """Fusionne tous les schémas d'outils disponibles (core + modules + plugins)."""
    all_tools = list(CORE_TOOLS)   # copie de la liste de base

    # Plugins
    if plugins:
        for p in plugins.load_plugins():
            all_tools.append(p["schema"])

    # Modules externes
    if github:
        all_tools.extend(github.TOOL_SCHEMAS)
    if video:
        all_tools.append(video.TOOL_SCHEMA)
    if news:
        all_tools.append(news.TOOL_SCHEMA)
    if browser:
        all_tools.extend(browser.TOOL_SCHEMAS)
    if database:
        all_tools.extend(database.TOOL_SCHEMAS)

    return all_tools, plugins.load_plugins() if plugins else []

# ---------------------------------------------------------------------
# Dispatcher unifié des appels d'outils
# ---------------------------------------------------------------------
def execute_any_tool(tool_name: str, args: dict, workspace: str, backup_dir: str, plugins_list: list) -> str:
    # 1. Outils de base (tools.py)
    if tool_name in [t["function"]["name"] for t in CORE_TOOLS]:
        return core_execute(tool_name, args, workspace, backup_dir)

    # 2. Plugins
    for p in plugins_list:
        if p["schema"]["function"]["name"] == tool_name:
            return p["function"](**args)

    # 3. GitHub
    if github and tool_name in [t["function"]["name"] for t in github.TOOL_SCHEMAS]:
        return github.run(tool_name, args)

    # 4. YouTube
    if video and tool_name == video.TOOL_SCHEMA["function"]["name"]:
        return video.run(**args)

    # 5. Actualités
    if news and tool_name == news.TOOL_SCHEMA["function"]["name"]:
        return news.run(**args)

    # 6. Navigateur
    if browser and tool_name in [t["function"]["name"] for t in browser.TOOL_SCHEMAS]:
        return browser.run(tool_name, args)

    # 7. Base de données
    if database and tool_name in [t["function"]["name"] for t in database.TOOL_SCHEMAS]:
        return database.run(tool_name, args)

    return f"Outil inconnu : {tool_name}"

# ---------------------------------------------------------------------
# Agent principal
# ---------------------------------------------------------------------
class Agent:
    def __init__(self, config: dict):
        self.api_keys = config["api_keys"]
        self.model = config["model"]
        self.fallbacks = config.get("fallback_models", [])
        self.max_iter = config.get("max_iterations", 10)
        self.max_tokens = config.get("max_tokens", 1024)
        self.api_base = config.get("groq_api_base", "https://api.groq.com/openai/v1")
        self.workspace = config["workspace_dir"]
        self.backup_dir = config["backup_dir"]
        self.auto_plan = config.get("auto_plan", True)
        self.local_mode = config.get("local_mode", False)          # <-- mode local (Ollama)

        # Historique de la conversation (prompt système uniquement au départ)
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Outils et plugins
        self.all_tools, self.plugins_list = build_all_tools()

    def _call_model(self, tools=True):
        """Appelle le modèle en essayant les fallbacks, avec gestion du mode local."""
        models = [self.model] + self.fallbacks
        last_err = None
        for model in models:
            try:
                return chat_completion(
                    self.api_keys,
                    model,
                    self.messages,
                    tools=self.all_tools if tools else None,
                    max_tokens=self.max_tokens,
                    api_base=self.api_base,
                    local_mode=self.local_mode,   # <-- transmis à l'API
                )
            except Exception as e:
                last_err = str(e)
                error(f"Modèle {model} : {last_err}")
        raise RuntimeError(f"Aucun modèle n'a fonctionné : {last_err}")

    def process_input(self, user_input: str):
        os.makedirs(self.workspace, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        self.messages.append({"role": "user", "content": user_input})

        try:
            resp = self._call_model()
        except RuntimeError as e:
            error(str(e))
            return

        choice = resp["choices"][0]
        msg = choice["message"]

        # Boucle d'interaction (jusqu'à max_iter ou fin de tâche)
        for iteration in range(self.max_iter):
            # Gestion d'un plan auto-détecté
            plan = self._extract_plan(msg.get("content", ""))
            if plan and self.auto_plan:
                info("Plan détecté, exécution étape par étape.")
                self.messages.append({"role": "assistant", "content": msg.get("content")})
                for step in plan:
                    self.messages.append({"role": "user", "content": f"Étape : {step}"})
                    resp = self._call_model()
                    msg = resp["choices"][0]["message"]
                    if msg.get("tool_calls"):
                        self._handle_tool_calls(msg)
                        resp = self._call_model()
                        msg = resp["choices"][0]["message"]
                break

            # Si pas d'appel d'outil, c'est une réponse simple
            if not msg.get("tool_calls"):
                if msg.get("content"):
                    assistant(msg["content"])
                self.messages.append({"role": "assistant", "content": msg.get("content")})
                break

            # Afficher le texte éventuel avant les outils
            if msg.get("content"):
                assistant(msg["content"])

            # Exécuter les outils
            self._handle_tool_calls(msg)

            # Obtenir la prochaine réponse du modèle
            try:
                resp = self._call_model()
            except RuntimeError as e:
                error(str(e))
                break
            msg = resp["choices"][0]["message"]
        else:
            info("Nombre maximum d'itérations atteint.")

    def _handle_tool_calls(self, msg):
        """Exécute tous les tool_calls présents dans le message."""
        self.messages.append({
            "role": "assistant",
            "content": msg.get("content"),
            "tool_calls": msg["tool_calls"]
        })
        for tc in msg["tool_calls"]:
            tool_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            tool_use(tool_name, args)
            result = execute_any_tool(tool_name, args, self.workspace, self.backup_dir, self.plugins_list)
            tool_result(result)
            self.messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result
            })

    def _extract_plan(self, text):
        """Extrait les étapes d'un plan depuis une balise <plan>...</plan>."""
        match = re.search(r'<plan>(.*?)</plan>', text, re.DOTALL)
        if match:
            return [s.strip() for s in match.group(1).split(';') if s.strip()]
        return None

    def review_code(self, file_path: str):
        """Analyse le code d'un fichier et affiche les retours."""
        full = os.path.join(self.workspace, file_path)
        if not os.path.exists(full):
            error(f"Fichier introuvable : {file_path}")
            return
        with open(full, "r", encoding="utf-8") as f:
            code = f.read()
        self.messages.append({
            "role": "user",
            "content": f"Analyse ce code (bugs, style, sécurité, performances) :\n```\n{code}\n```\nRéponds sans utiliser d'outil."
        })
        try:
            resp = self._call_model(tools=False)
        except RuntimeError as e:
            error(str(e))
            return
        msg = resp["choices"][0]["message"]
        if msg.get("content"):
            assistant(msg["content"])
        self.messages.append({"role": "assistant", "content": msg.get("content")})
