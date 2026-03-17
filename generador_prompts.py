import random

import json
import os

config_prompts = {"personas": [], "formatos": []}

def inicializar_prompts(ruta_proyecto="."):
    global config_prompts
    ruta_config = os.path.join(ruta_proyecto, 'config_prompts.json')
    if os.path.exists(ruta_config):
        with open(ruta_config, 'r', encoding='utf-8') as file:
            config_prompts = json.load(file)
    else:
        raise FileNotFoundError(f"No se encontró config_prompts.json en {ruta_proyecto}")

def generar_prompt_antidetencion(nicho_actual, palabras_clave, url_money_site, anchor_text, modo="articulo", contenido_base=None):
    """
    Construye un prompt hiper-específico rotando identidades y formatos estructurales
    para evadir la detección de contenido programático (AI Spam).
    
    modo: "articulo" (genera post nuevo) o "home" (reescribe contenido_base)
    """

    # 3. Selección Aleatoria de las Listas en Config
    persona_elegida = random.choice(config_prompts["personas"])
    formato_elegido = random.choice(config_prompts["formatos"])

    # 4. Construcción del Prompt Maestro
    instruccion_modo = ""
    if modo == "home" and contenido_base:
        instruccion_modo = f"""
        OBJETIVO: Re-escribe el siguiente texto FUENTE para convertirlo en una página de inicio (HOME) única y de altísima calidad.
        REGLA DE ORO: No copies frases del texto fuente. Debes re-imaginar todo el contenido usando tu perfil y formato asignado, pero manteniendo la oferta de valor y los datos de contacto.
        
        TEXTO FUENTE A RE-ESCRIBIR:
        {contenido_base}
        """
    else:
        instruccion_modo = f"""
        TEMA CENTRAL: {nicho_actual}
        PALABRAS CLAVE A INCLUIR NATURALMENTE: {', '.join(palabras_clave)}
        """

    prompt = f"""
    {persona_elegida}
    
    {formato_elegido}
    
    {instruccion_modo}
    
    INSTRUCCIONES DE REDACCIÓN (OBLIGATORIAS):
    1. REGLA DE FORMATO: Devuelve el texto ÚNICAMENTE en Markdown válido. Usa subtítulos H2 y H3.
    2. REGLA DE LONGITUD: El texto debe tener entre 800 y 1200 palabras. Usa párrafos cortos (máximo 3 oraciones por párrafo).
    
    RESTRICCIONES NEGATIVAS (PROHIBIDO USAR ESTAS FRASES):
    - NO uses transiciones robóticas como: "En conclusión", "En resumen", "Por otro lado", "Es importante destacar que", "Adentrémonos", "En el vertiginoso mundo de".
    - NO hagas una introducción genérica diciendo de qué vas a hablar. Empieza directo con el valor.
    - NO uses un tono excesivamente entusiasta o poético.
    
    INSTRUCCIÓN DE ENLAZADO (INTERLINKING SECRETO):
    Dentro del flujo natural del texto, en uno de los párrafos intermedios, debes integrar ESTRICTAMENTE el siguiente enlace promocional:
    - URL de destino: {url_money_site}
    - Texto ancla EXACTO: "{anchor_text}"
    El enlace debe integrarse de forma semántica, como una recomendación de una plataforma donde pueden revisar el proceso completo o buscar ayuda. NO lo pongas como un botón o al final del artículo.
    """
    
    return prompt

# ==========================================
# PRUEBA DEL GENERADOR
# ==========================================
if __name__ == "__main__":
    nicho = "Requisitos para trabajar en hospitales de Wesley Chapel"
    keywords = ["NCLEX Florida", "homologación enfermeras Wesley Chapel", "salarios"]
    
    prompt_final = generar_prompt_antidetencion(nicho, keywords, "https://enfermeraeeu.com", "revisa nuestro programa de preparación")
    print(prompt_final)
