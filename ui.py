import os
import sys

# Tentative d'utiliser Rich pour un rendu plus joli, sinon on reste en ANSI
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ---------- Couleurs (codes ANSI) ----------
class Colors:
    ORANGE = '\033[38;5;208m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """Efface le terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    """Affiche un logo ASCII."""
    logo = f"""
{Colors.ORANGE}{Colors.BOLD}
  ██╗     ██╗ █████╗ 
  ██║     ██║██╔══██╗
  ██║     ██║███████║
  ██║     ██║██╔══██║
  ███████╗██║██║  ██║
  ╚══════╝╚═╝╚═╝  ╚═╝
{Colors.RESET}
{Colors.ORANGE}  Agent IA – par pas2profil{Colors.RESET}
"""
    print(logo)

def print_assistant_message(content):
    """Affiche le message de l'assistant."""
    if RICH_AVAILABLE:
        console = Console()
        md = Markdown(content)
        console.print(md)
    else:
        print(f"{Colors.ORANGE}LIA{Colors.RESET} > {content}")

def print_tool_call(tool_name, args):
    """Affiche l'appel d'outil de façon compacte."""
    msg = f"{Colors.YELLOW}🔧 {tool_name} {args}{Colors.RESET}"
    print(msg)

def print_tool_result(result):
    """Affiche le résultat d'un outil en version courte."""
    # On tronque les résultats longs
    if len(result) > 200:
        result = result[:200] + "..."
    print(f"{Colors.GREEN}   -> {result}{Colors.RESET}")

def print_error(message):
    """Affiche une erreur de manière concise."""
    # On extrait seulement la partie utile
    short = message
    if "402" in message:
        short = "Crédit insuffisant."
    elif "400" in message:
        short = "Requête invalide (modèle peut-être obsolète)."
    elif "404" in message:
        short = "Modèle introuvable."
    elif "429" in message:
        short = "Limite de taux atteinte, réessaye dans un instant."
    print(f"{Colors.RED}[ERREUR] {short}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.CYAN}{message}{Colors.RESET}")
