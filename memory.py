import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"facts": [], "preferences": {}}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def remember_fact(fact):
    mem = load_memory()
    mem["facts"].append(fact)
    save_memory(mem)

def recall_facts(query=None):
    mem = load_memory()
    if query:
        return [f for f in mem["facts"] if query.lower() in f.lower()]
    return mem["facts"]

def set_preference(key, value):
    mem = load_memory()
    mem["preferences"][key] = value
    save_memory(mem)

def get_preference(key):
    mem = load_memory()
    return mem["preferences"].get(key)
