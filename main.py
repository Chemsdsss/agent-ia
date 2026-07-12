#!/usr/bin/env python3
"""
LIA – Agent Codeur Avancé
Interface en ligne de commande avec sessions persistantes.
Lancez : python main.py
"""
import os
import sys
from utils import load_config
from agent import Agent
from ui import clear_screen, print_logo, info, error, Colors

# ---------------------------------------------------------------------
# Mini gestionnaire de sessions (fichiers JSON dans ./sessions/)
# ---------------------------------------------------------------------
import json
import uuid
from datetime import datetime

SESSIONS_DIR = "sessions"

def ensure_sessions_dir():
    os.makedirs(SESSIONS_DIR, exist_ok=True)

def create_session(name="Nouvelle session"):
    ensure_sessions_dir()
    sid = str(uuid.uuid4())[:8]
    data = {
        "id": sid,
        "name": name,
        "created": datetime.now().isoformat(),
        "messages": []
    }
    with open(os.path.join(SESSIONS_DIR, f"{sid}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return sid

def load_session(sid):
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_session(sid, messages, name=None):
    ensure_sessions_dir()
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    data = load_session(sid) or {"id": sid, "created": datetime.now().isoformat()}
    data["messages"] = messages
    if name:
        data["name"] = name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def list_sessions():
    ensure_sessions_dir()
    sessions = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions.append({
                    "id": data["id"],
                    "name": data.get("name", "Sans nom"),
                    "created": data["created"][:19]
                })
    return sorted(sessions, key=lambda s: s["created"], reverse=True)

def delete_session(sid):
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

# ---------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------
def main():
    clear_screen()
    print_logo()

    config = load_config()
    current_session = None
    agent = None

    while True:
        try:
            if current_session:
                prompt = f"{Colors.ORANGE}[{current_session['name']}] >> {Colors.RESET}"
            else:
                prompt = f"{Colors.ORANGE}>> {Colors.RESET}"

            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            if agent and current_session:
                save_session(current_session["id"], agent.messages, name=current_session["name"])
                info("Session sauvegardée.")
            break

        if not user_input:
            continue

        # Commandes spéciales (préfixées par /)
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/new":
                name = arg if arg else "Nouvelle session"
                sid = create_session(name)
                current_session = {"id": sid, "name": name}
                agent = Agent(config)
                info(f"Session '{name}' créée (id: {sid}).")
                continue

            elif cmd == "/load":
                if not arg:
                    error("Usage : /load <id>")
                    continue
                data = load_session(arg)
                if data is None:
                    error("Session introuvable.")
                    continue
                current_session = {"id": arg, "name": data.get("name", "Sans nom")}
                agent = Agent(config)
                agent.messages = data.get("messages", [])
                info(f"Session '{current_session['name']}' chargée.")
                continue

            elif cmd == "/sessions":
                sessions = list_sessions()
                if not sessions:
                    info("Aucune session sauvegardée.")
                else:
                    print("\nSessions disponibles :")
                    for s in sessions:
                        print(f"  [{s['id']}] {s['name']} ({s['created']})")
                continue

            elif cmd == "/delete":
                if not arg:
                    error("Usage : /delete <id>")
                    continue
                if delete_session(arg):
                    info("Session supprimée.")
                    if current_session and current_session["id"] == arg:
                        current_session = None
                        agent = None
                else:
                    error("Session introuvable.")
                continue

            elif cmd == "/quit":
                if agent and current_session:
                    save_session(current_session["id"], agent.messages, name=current_session["name"])
                info("Fermeture de LIA.")
                break

            elif cmd == "/review":
                if not agent or not current_session:
                    error("Aucune session active. Créez-en une (/new).")
                    continue
                if not arg:
                    error("Usage : /review <fichier>")
                    continue
                agent.review_code(arg)
                save_session(current_session["id"], agent.messages, name=current_session["name"])
                continue

            elif cmd == "/clear":
                clear_screen()
                print_logo()
                continue

            elif cmd == "/help":
                print("Commandes :")
                print("  /new [nom]        Nouvelle session")
                print("  /load <id>        Charger une session")
                print("  /sessions         Lister les sessions")
                print("  /delete <id>      Supprimer une session")
                print("  /review <fichier> Analyser un fichier")
                print("  /clear            Effacer l'écran")
                print("  /quit             Quitter (sauvegarde auto)")
                continue

            else:
                error(f"Commande inconnue : {cmd}")
                continue

        # Message normal -> nécessite une session active
        if not agent or not current_session:
            error("Aucune session active. Tapez /new pour en créer une.")
            continue

        try:
            agent.process_input(user_input)
        except Exception as e:
            error(str(e))

        # Sauvegarde automatique après chaque interaction
        save_session(current_session["id"], agent.messages, name=current_session["name"])

if __name__ == "__main__":
    main()
