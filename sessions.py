import os
import json
import uuid
from datetime import datetime

SESSIONS_DIR = "sessions"

def ensure_sessions_dir():
    os.makedirs(SESSIONS_DIR, exist_ok=True)

def create_session(name="Nouvelle session"):
    ensure_sessions_dir()
    session_id = str(uuid.uuid4())[:8]
    filename = f"{session_id}.json"
    data = {
        "id": session_id,
        "name": name,
        "created": datetime.now().isoformat(),
        "messages": []
    }
    with open(os.path.join(SESSIONS_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return session_id

def load_session(session_id):
    filename = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_session(session_id, messages, name=None):
    ensure_sessions_dir()
    filename = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    data = load_session(session_id) or {"id": session_id, "created": datetime.now().isoformat()}
    data["messages"] = messages
    if name:
        data["name"] = name
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_sessions():
    ensure_sessions_dir()
    sessions = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions.append({"id": data["id"], "name": data.get("name", "Sans nom"), "created": data["created"][:19]})
    return sorted(sessions, key=lambda s: s["created"], reverse=True)

def delete_session(session_id):
    filename = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filename):
        os.remove(filename)
        return True
    return False
