import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def _get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

def fetch_page(url: str) -> str:
    driver = _get_driver()
    try:
        driver.get(url)
        time.sleep(2)
        text = driver.find_element(By.TAG_NAME, "body").text[:2000]
        return text
    finally:
        driver.quit()

def click_button(url: str, button_text: str) -> str:
    driver = _get_driver()
    try:
        driver.get(url)
        time.sleep(1)
        buttons = driver.find_elements(By.XPATH, f"//*[contains(text(),'{button_text}')]")
        if not buttons:
            return f"Bouton '{button_text}' introuvable."
        buttons[0].click()
        time.sleep(2)
        return driver.find_element(By.TAG_NAME, "body").text[:2000]
    finally:
        driver.quit()

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Récupère le texte d'une page web.",
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
            "name": "click_button",
            "description": "Clique sur un bouton et retourne le résultat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "button_text": {"type": "string", "description": "Texte du bouton (ex: 'Accepter')."}
                },
                "required": ["url", "button_text"]
            }
        }
    }
]

def run(tool_name: str, args: dict) -> str:
    if tool_name == "fetch_page": return fetch_page(**args)
    elif tool_name == "click_button": return click_button(**args)
    else: return f"Outil navigateur inconnu: {tool_name}"
