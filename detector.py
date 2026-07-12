import os
import sys
import platform
import subprocess
import psutil
import json
from typing import Dict, List, Tuple

def get_system_info() -> Dict:
    """Récupère les informations matérielles de la machine."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu": platform.processor(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
        "disk_free_gb": round(psutil.disk_usage('/').free / (1024**3), 1),
    }
    
    # Détection GPU (NVIDIA via nvidia-smi, sinon CPU only)
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            gpu_info = result.stdout.strip().split(',')
            info["gpu_name"] = gpu_info[0].strip()
            info["gpu_memory_mb"] = int(gpu_info[1].strip().replace(' MiB', ''))
            info["has_gpu"] = True
        else:
            info["has_gpu"] = False
    except:
        info["has_gpu"] = False
    
    return info

def estimate_model_compatibility(info: Dict) -> List[Dict]:
    """Estime quels modèles peuvent tourner sur cette machine."""
    models = []
    ram_gb = info["ram_available_gb"]
    has_gpu = info.get("has_gpu", False)
    gpu_mem = info.get("gpu_memory_mb", 0) / 1024 if has_gpu else 0
    
    # Modèles légers (1-3 Go de RAM)
    if ram_gb >= 4:
        models.append({
            "name": "phi3:mini",
            "size": "2.3 Go",
            "ram_needed": "4 Go",
            "gpu_optional": True,
            "quality": "Basique - code simple, chat",
            "command": "ollama pull phi3:mini"
        })
        models.append({
            "name": "tinyllama",
            "size": "637 Mo",
            "ram_needed": "2 Go",
            "gpu_optional": True,
            "quality": "Très basique - chat uniquement",
            "command": "ollama pull tinyllama"
        })
    
    # Modèles moyens (4-8 Go de RAM)
    if ram_gb >= 8:
        models.append({
            "name": "llama3.2:3b",
            "size": "2.0 Go",
            "ram_needed": "6 Go",
            "gpu_optional": True,
            "quality": "Bon - code, chat, outils",
            "command": "ollama pull llama3.2:3b"
        })
        models.append({
            "name": "mistral:7b",
            "size": "4.1 Go",
            "ram_needed": "8 Go",
            "gpu_optional": True,
            "quality": "Très bon - code avancé, raisonnement",
            "command": "ollama pull mistral:7b"
        })
    
    # Modèles puissants (16+ Go de RAM ou GPU)
    if ram_gb >= 16 or (has_gpu and gpu_mem >= 6):
        models.append({
            "name": "llama3.1:8b",
            "size": "4.7 Go",
            "ram_needed": "16 Go (ou 8 Go + GPU)",
            "gpu_recommended": True,
            "quality": "Excellent - comme GPT-4 mini",
            "command": "ollama pull llama3.1:8b"
        })
    
    if ram_gb >= 32 or (has_gpu and gpu_mem >= 12):
        models.append({
            "name": "llama3.3:70b",
            "size": "40 Go",
            "ram_needed": "32 Go (ou GPU 12+ Go)",
            "gpu_recommended": True,
            "quality": "Exceptionnel - niveau Claude/GPT-4",
            "command": "ollama pull llama3.3:70b"
        })
    
    return models

def check_ollama_installed() -> bool:
    """Vérifie si Ollama est installé."""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def install_ollama():
    """Installe Ollama automatiquement (Linux)."""
    print("\nInstallation d'Ollama...")
    subprocess.run(['curl', '-fsSL', 'https://ollama.com/install.sh', '|', 'sh'], shell=True)
    subprocess.run(['ollama', 'serve'], start_new_session=True)

def get_installed_models() -> List[str]:
    """Liste les modèles déjà téléchargés dans Ollama."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # skip header
            return [line.split()[0] for line in lines if line.strip()]
    except:
        pass
    return []

def pull_model(model_name: str):
    """Télécharge un modèle Ollama."""
    print(f"\nTéléchargement du modèle {model_name}...")
    subprocess.run(['ollama', 'pull', model_name])
