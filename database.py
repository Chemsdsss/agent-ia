import sqlite3, os

DB_FILE = "lia_data.db"

def _connect():
    return sqlite3.connect(DB_FILE)

def execute_sql(query: str) -> str:
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            if not rows:
                return "(aucun résultat)"
            return "\n".join([", ".join(map(str, row)) for row in rows])
        else:
            conn.commit()
            return f"Succès. Lignes affectées: {cur.rowcount}"
    except Exception as e:
        return f"Erreur SQL: {e}"
    finally:
        conn.close()

def list_tables() -> str:
    return execute_sql("SELECT name FROM sqlite_master WHERE type='table';")

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Exécute une requête SQL sur la base de données locale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Requête SQL."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Liste les tables de la base de données.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def run(tool_name: str, args: dict) -> str:
    if tool_name == "execute_sql": return execute_sql(**args)
    elif tool_name == "list_tables": return list_tables()
    else: return f"Outil DB inconnu: {tool_name}"
