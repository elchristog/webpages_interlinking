import json
import random
import os

config = None
config_logic = None

def inicializar_interlinking(ruta_proyecto="."):
    global config, config_logic
    ruta_config = os.path.join(ruta_proyecto, 'config_enlaces.json')
    if os.path.exists(ruta_config):
        with open(ruta_config, 'r', encoding='utf-8') as file:
            config = json.load(file)
    else:
        raise FileNotFoundError(f"No se encontró config_enlaces.json en {ruta_proyecto}")
    
    # Cargar lógica dinámica
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Asumiendo que estamos en la raíz del repo
    # O mejor, buscarlo en la raíz del proyecto web_interlinking
    ruta_logic = os.path.join(ruta_base, 'webpages_interlinking', 'config_logic.json')
    if not os.path.exists(ruta_logic):
        # Fallback si se ejecuta desde otro lado
        ruta_logic = 'config_logic.json'
        
    if os.path.exists(ruta_logic):
        with open(ruta_logic, 'r', encoding='utf-8') as file:
            config_logic = json.load(file)
    else:
        # Default fallback if file is missing
        config_logic = {
            "interlinking": {
                "probability_link_money_site": 0.5,
                "money_site_home_weight": 40,
                "money_site_deep_weight": 60,
                "anchor_weights": {"brand": 50, "naked": 20, "generic": 15, "exact": 10, "partial": 5}
            }
        }

def decidir_si_enlazar():
    """Usa la probabilidad configurada en config_logic.json."""
    return random.random() <= config_logic["interlinking"]["probability_link_money_site"]

def obtener_url_objetivo():
    """Usa los pesos configurados para Home vs Deep Links."""
    home_weight = config_logic["interlinking"]["money_site_home_weight"] / 100.0
    if random.random() <= home_weight:
        return config["money_site"]["home_url"]
    else:
        return random.choice(config["money_site"]["deep_links"])

def obtener_anchor_text():
    """Usa los pesos configurados en config_logic.json para los tipos de anchor."""
    weights = config_logic["interlinking"]["anchor_weights"]
    tipos = ['marca', 'desnudos', 'genericos', 'exactos', 'parciales']
    # Mapear nombres de las llaves si son diferentes
    key_map = {
        'marca': 'brand',
        'desnudos': 'naked',
        'genericos': 'generic',
        'exactos': 'exact',
        'parciales': 'partial'
    }
    pesos_list = [weights[key_map[t]] for t in tipos]
    
    tipo_elegido = random.choices(tipos, weights=pesos_list, k=1)[0]
    return random.choice(config["anchor_texts"][tipo_elegido])

def obtener_enlace_autoridad():
    """Selecciona un enlace gubernamental u oficial para distraer y dar legitimidad."""
    return random.choice(config["enlaces_autoridad"])

def inyectar_instrucciones_ia(ciudad_objetivo):
    """
    Genera el prompt maestro que le enviarás a la API de IA (ej. Gemini o OpenAI)
    para que redacte el artículo con los enlaces ya integrados en el contexto.
    Legacy implementation if not using generador_prompts.py
    """
    
    # Enlaces de distracción obligatorios (Outbound links)
    enlace_outbound = obtener_enlace_autoridad()
    instruccion_base = f"""
    Eres un experto en procesos migratorios y de salud. Redacta un artículo informativo 
    sobre las oportunidades para enfermeras internacionales en {ciudad_objetivo}.
    
    REGLA 1: Debes incluir naturalmente un enlace hacia esta fuente oficial: {enlace_outbound}
    """
    
    # Si cae en el 30%, inyectamos nuestro Money Site
    if decidir_si_enlazar():
        url_money_site = obtener_url_objetivo()
        anchor = obtener_anchor_text()
        
        instruccion_money_site = f"""
        REGLA 2: Dentro del texto, de forma muy conversacional y natural, debes integrar 
        un enlace hacia '{url_money_site}'. El texto ancla EXACTO que debes usar para 
        este enlace es: '{anchor}'. No lo pongas al final como despedida, intégralo en 
        un párrafo explicativo.
        """
        prompt_final = instruccion_base + instruccion_money_site
    else:
        prompt_final = instruccion_base
        
    return prompt_final

# ==========================================
# SIMULACIÓN DE EJECUCIÓN DEL SCRIPT
# ==========================================
if __name__ == "__main__":
    print("Generando instrucciones para 3 artículos espejo...\n")
    
    ciudades = ["Tampa, FL", "Zephyrhills, FL", "Atlanta, GA"]
    
    for ciudad in ciudades:
        print(f"--- Construyendo artículo para: {ciudad} ---")
        prompt = inyectar_instrucciones_ia(ciudad)
        print(prompt)
        print("-" * 50)
