import json
import random

import os

config = None

def inicializar_interlinking(ruta_proyecto="."):
    global config
    ruta_config = os.path.join(ruta_proyecto, 'config_enlaces.json')
    if os.path.exists(ruta_config):
        with open(ruta_config, 'r', encoding='utf-8') as file:
            config = json.load(file)
    else:
        raise FileNotFoundError(f"No se encontró config_enlaces.json en {ruta_proyecto}")

def decidir_si_enlazar():
    """Regla del 30%: Solo el 30% de los artículos llevarán enlace al Money Site."""
    return random.random() <= 0.30

def obtener_url_objetivo():
    """Regla de Profundidad: 40% al Home, 60% a Deep Links (páginas internas)."""
    if random.random() <= 0.40:
        return config["money_site"]["home_url"]
    else:
        return random.choice(config["money_site"]["deep_links"])

def obtener_anchor_text():
    """Regla de Diversificación: Elige el tipo de Anchor Text basado en pesos (weights)."""
    tipos = ['marca', 'desnudos', 'genericos', 'exactos', 'parciales']
    pesos = [50, 20, 15, 10, 5] # Los porcentajes que definimos
    
    tipo_elegido = random.choices(tipos, weights=pesos, k=1)[0]
    
    # Selecciona un texto aleatorio dentro de la categoría ganadora
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
