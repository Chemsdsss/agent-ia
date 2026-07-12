#!/usr/bin/env python3
"""
Lancement initial de LIA - Détecte le matériel et configure le mode.
"""
import json
from detector import get_system_info, estimate_model_compatibility, check_ollama_installed, get_installed_models, pull_model
from ui import clear_screen, print_logo, info, error, Colors

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def setup_wizard():
    clear_screen()
    print_logo()
    
    print(f"{Colors.CYAN}=== Assistant de configuration LIA ===\n{Colors.RESET}")
    
    # 1. Détection matérielle
    print("Analyse de votre matériel...")
    sys_info = get_system_info()
    
    print(f"{Colors.GREEN}")
    print(f"  Système : {sys_info['os']}")
    print(f"  CPU : {sys_info['cpu']} ({sys_info['cpu_cores']} cœurs, {sys_info['cpu_threads']} threads)")
    print(f"  RAM : {sys_info['ram_total_gb']} Go (disponible : {sys_info['ram_available_gb']} Go)")
    print(f"  Disque libre : {sys_info['disk_free_gb']} Go")
    if sys_info.get('has_gpu'):
        print(f"  GPU : {sys_info['gpu_name']} ({sys_info['gpu_memory_mb']} Mo)")
    else:
        print(f"  GPU : Aucun détecté")
    print(f"{Colors.RESET}")
    
    # 2. Choix du mode
    print("\nMode de fonctionnement :")
    print(f"  {Colors.ORANGE}[1]{Colors.RESET} Mode API (Groq) - Nécessite une connexion Internet, gratuit avec limites")
    print(f"  {Colors.ORANGE}[2]{Colors.RESET} Mode Local (Ollama) - Fonctionne hors ligne, selon votre matériel")
    print(f"  {Colors.ORANGE}[3]{Colors.RESET} Mode Auto - Utilise le local si assez puissant, sinon API")
    
    while True:
        choice = input(f"\n{Colors.ORANGE}Votre choix (1/2/3) : {Colors.RESET}").strip()
        if choice in ['1', '2', '3']:
            break
        print("Choix invalide.")
    
    config = load_config()
    
    if choice == '1':
        # Mode API
        config["local_mode"] = False
        config["groq_api_base"] = "https://api.groq.com/openai/v1"
        print("\nMode API sélectionné. Assurez-vous d'avoir une clé Groq.")
        api_key = input("Clé API Groq (ou Entrée si déjà dans l'environnement) : ").strip()
        if api_key:
            config["api_keys"] = [api_key]
    
    elif choice == '2':
        # Mode Local
        if not check_ollama_installed():
            print("\nOllama n'est pas installé.")
            install = input("Voulez-vous l'installer automatiquement ? (o/n) : ").strip().lower()
            if install == 'o':
                from detector import install_ollama
                install_ollama()
            else:
                print("Installation annulée. Repassez en mode API.")
                return
        
        # Proposer les modèles compatibles
        models = estimate_model_compatibility(sys_info)
        installed = get_installed_models()
        
        print(f"\n{Colors.CYAN}Modèles disponibles pour votre machine :{Colors.RESET}")
        for i, model in enumerate(models, 1):
            status = "[installé]" if model["name"] in installed else ""
            print(f"  {Colors.ORANGE}[{i}]{Colors.RESET} {model['name']} ({model['size']}) - {model['quality']} {status}")
        
        if not models:
            print(f"\n{Colors.RED}Votre machine n'a pas assez de ressources pour un modèle local.{Colors.RESET}")
            print("Passage en mode API.")
            config["local_mode"] = False
            save_config(config)
            return
        
        while True:
            try:
                model_choice = int(input(f"\n{Colors.ORANGE}Choisissez un modèle (1-{len(models)}) : {Colors.RESET}"))
                if 1 <= model_choice <= len(models):
                    break
            except:
                pass
            print("Choix invalide.")
        
        chosen_model = models[model_choice - 1]
        
        # Télécharger si pas déjà installé
        if chosen_model["name"] not in installed:
            print(f"\nTéléchargement de {chosen_model['name']}...")
            pull_model(chosen_model["name"])
        
        config["local_mode"] = True
        config["model"] = chosen_model["name"]
        config["groq_api_base"] = "http://localhost:11434/v1"
        config["api_keys"] = ["sk-local"]
        
        print(f"\n{Colors.GREEN}Modèle {chosen_model['name']} prêt !{Colors.RESET}")
    
    elif choice == '3':
        # Mode Auto
        models = estimate_model_compatibility(sys_info)
        if models and check_ollama_installed():
            print("\nVotre machine peut faire tourner un modèle local. Passage en mode local.")
            config["local_mode"] = True
            config["model"] = models[-1]["name"]  # le plus puissant compatible
            config["groq_api_base"] = "http://localhost:11434/v1"
            config["api_keys"] = ["sk-local"]
            if models[-1]["name"] not in get_installed_models():
                pull_model(models[-1]["name"])
        else:
            print("\nMode local impossible. Passage en mode API.")
            config["local_mode"] = False
            config["groq_api_base"] = "https://api.groq.com/openai/v1"
    
    save_config(config)
    print(f"\n{Colors.GREEN}Configuration terminée ! Lancez 'python main.py'{Colors.RESET}")

if __name__ == "__main__":
    setup_wizard()
