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

def generar_prompt_antidetencion(nicho_actual, palabras_clave, url_money_site, anchor_text, url_outbound="https://wikipedia.org", modo="articulo", contenido_base=None, nombre_sitio="este sitio"):
    """
    Construye un prompt hiper-específico rotando identidades y formatos estructurales
    para evadir la detección de contenido programático (AI Spam).
    
    modo: "articulo" (genera post nuevo), "home" (reescribe contenido_base) o "pestaña" (informativa)
    """

    # 3. Selección Aleatoria de las Listas en Config
    persona_elegida = random.choice(config_prompts["personas"])
    formato_elegido = random.choice(config_prompts["formatos"])

    # 4. Construcción del Prompt Maestro
    instruccion_modo = ""
    if modo == "home" and contenido_base:
        instruccion_modo = f"""
        OBJETIVO: Re-escribe el siguiente texto FUENTE para convertirlo en una página de inicio (HOME) única para el sitio '{nombre_sitio}'.
        REGLA DE ORO DE UNICIDAD: La redacción debe ser TOTALMENTE diferente al texto fuente. No se trata de cambiar unas palabras, sino de re-imaginar todo el mensaje desde la perspectiva de tu perfil y adaptarlo al nicho: {nicho_actual}.
        
        TEXTO FUENTE A RE-ESCRIBIR:
        {contenido_base}
        """
    elif modo == "pestaña":
        tema = contenido_base if contenido_base else nicho_actual
        instruccion_modo = f"""
        OBJETIVO: Crea una página institucional/informativa (Pestaña de Menú) sobre el siguiente TEMA para el sitio '{nombre_sitio}'.
        TEMA: {tema}
        NICHO DEL SITIO: {nicho_actual}
        TONO: Profesional, autoritario y servicial. Menos narrativo que un blog, más estructurado como una guía oficial.
        REGLA SEO: Debes incluir la palabra clave principal '{palabras_clave[0]}' en el primer título H2 y en el primer párrafo de forma natural.
        """
    else:
        tema = contenido_base if contenido_base else nicho_actual
        instruccion_modo = f"""
        TEMA CENTRAL: {tema}
        SITIO ACTUAL: {nombre_sitio}
        CONTEXTO DEL SITIO (NICHO): {nicho_actual}
        PALABRAS CLAVE: {', '.join(palabras_clave)}
        REGLA DE REDACCIÓN: Usa el nicho local '{nicho_actual}' para dar ejemplos específicos, mencionar hospitales de la zona o realidades del mercado local que no estén en el tema general.
        """

    instruccion_interlinking = ""
    if url_money_site != "N/A":
        instruccion_interlinking = f"""
    INSTRUCCIÓN DE ENLAZADO (INTERLINKING OBLIGATORIO):
    Dentro del flujo natural del texto, en uno de los párrafos intermedios, debes integrar ESTRICTAMENTE el siguiente enlace usando el formato Markdown `[Texto Ancla](URL)`:
    - URL de destino: {url_money_site}
    - Texto ancla EXACTO: "{anchor_text}"
    - Ejemplo de formato: [{anchor_text}]({url_money_site})
    El enlace debe integrarse de forma semántica, como una recomendación. NO lo pongas como un botón o al final del artículo.
    """
    else:
        instruccion_interlinking = """
    INSTRUCCIÓN DE ENLAZADO:
    NO incluyas ningún enlace promocional o externo hacia sitios comerciales en este artículo. Solo puedes enlazar a fuentes oficiales o gubernamentales como referencias.
    """

    prompt = f"""
    {persona_elegida}
    
    {formato_elegido}
    
    {instruccion_modo}
    
    INSTRUCCIONES DE REDACCIÓN (OBLIGATORIAS):
    1. REGLA DE UNICIDAD TOTAL: Si eres parte de una red de sitios, tu texto debe ser DRÁSTICAMENTE diferente a cualquier otro. Cambia la estructura, el orden de las ideas y el estilo gramatical.
    2. REGLA DE FORMATO: Devuelve el texto ÚNICAMENTE en Markdown válido. Usa subtítulos H2 y H3.
    3. REGLA DE LONGITUD: El texto debe tener entre 800 y 1200 palabras. Usa párrafos cortos (máximo 3 oraciones por párrafo).
    4. REGLA DE AUTORIDAD: Debes incluir naturalmente un enlace hacia esta fuente oficial/gubernamental: {url_outbound}. El texto ancla debe ser natural y relevante al contexto.

    RESTRICCIONES NEGATIVAS (PROHIBIDO USAR ESTAS FRASES):
    - NO uses transiciones robóticas como: "En conclusión", "En resumen", "Por otro lado", "Es importante destacar que", "Adentrémonos", "En el vertiginoso mundo de".
    - NO hagas una introducción genérica diciendo de qué vas a hablar. Empieza directo con el valor.
    - NO uses un tono excesivamente entusiasta o poético.
    
    {instruccion_interlinking}
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
