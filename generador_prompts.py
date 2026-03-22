import random

import json
import os

config_prompts = {"personas": [], "formatos": []}
config_logic = None

def inicializar_prompts(ruta_proyecto="."):
    global config_prompts, config_logic
    ruta_config = os.path.join(ruta_proyecto, 'config_prompts.json')
    if os.path.exists(ruta_config):
        with open(ruta_config, 'r', encoding='utf-8') as file:
            config_prompts = json.load(file)
    
    # Cargar lógica dinámica
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_logic = os.path.join(ruta_base, 'webpages_interlinking', 'config_logic.json')
    if not os.path.exists(ruta_logic):
        ruta_logic = 'config_logic.json'
        
    if os.path.exists(ruta_logic):
        with open(ruta_logic, 'r', encoding='utf-8') as file:
            config_logic = json.load(file)
    else:
        raise FileNotFoundError(f"No se encontró config_prompts.json en {ruta_proyecto}")

def generar_prompt_antidetencion(nicho_actual, palabras_clave, url_money_site, anchor_text, url_outbound="https://wikipedia.org", modo="articulo", contenido_base=None, nombre_sitio="este sitio", nombre_empresa="Enfermera en Estados Unidos"):
    """
    Construye un prompt hiper-específico rotando identidades y formatos estructurales
    para evadir la detección de contenido programático (AI Spam).
    
    modo: "articulo" (genera post nuevo), "home" (reescribe contenido_base) o "pestaña" (informativa)
    """

    # 3. Selección Aleatoria de las Listas en Config
    # Detectar si estamos en modo página (home/pestaña) o blog (articulo/blog)
    categoria = "paginas" if modo in ["home", "pestaña"] else "blog"
    
    if categoria in config_prompts:
        persona_elegida = random.choice(config_prompts[categoria]["personas"])
        formato_elegido = random.choice(config_prompts[categoria]["formatos"])
    else:
        # Fallback para compatibilidad con el formato antiguo si fuera necesario
        lista_personas = config_prompts.get("personas", ["Eres un experto en el tema."])
        lista_formatos = config_prompts.get("formatos", ["Escribe en formato profesional."])
        persona_elegida = random.choice(lista_personas)
        formato_elegido = random.choice(lista_formatos)

    # 4. Construcción del Prompt Maestro
    instruccion_modo = ""
    if modo == "home" and contenido_base:
        instruccion_modo = f"""
        OBJETIVO: Convierte el texto FUENTE en una página de inicio (HOME) altamente PERSUASIVA y TRANSACCIONAL para '{nombre_sitio}'.
        ESTILO: Directo, vendedor, enfocado en BENEFICIOS y en qué ofrece el sitio. Usa un lenguaje que invite a la acción (CTA).
        REGLA DE ORO: La redacción debe ser TOTALMENTE única y adaptada al nicho: {nicho_actual}. No solo informes, ¡VENDE la idea o el servicio!
        ESTRUCTURA: Usa encabezados que resalten promesas de valor. Convierte los datos informativos en beneficios tangibles para el usuario.
        SEO: La palabra clave principal '{palabras_clave[0]}' debe aparecer en el H1 (o primer H2) y en las primeras 50 palabras.
        
        TEXTO FUENTE A TRANSFORMAR:
        {contenido_base}
        """
    elif modo == "pestaña":
        tema = contenido_base if contenido_base else nicho_actual
        instruccion_modo = f"""
        OBJETIVO: Crea una página de aterrizaje (Landing/Pestaña) TRANSACCIONAL y PERSUASIVA sobre el TEMA para el sitio '{nombre_sitio}'.
        TEMA: {tema}
        NICHO: {nicho_actual}
        TONO: Profesional pero orientado a CONVERSIÓN. Resalta por qué el usuario debería interesarse en este tema/servicio.
        ESTRUCTURA: Usa viñetas para listar beneficios. Incluye secciones de "Por qué elegirnos" o "Lo que obtendrás" de forma natural.
        SEO: Optimiza para '{palabras_clave[0]}'. Debe sentirse como una página oficial que resuelve una necesidad específica.
        """
    elif modo == "blog" or modo == "articulo":
        tema = contenido_base if contenido_base else nicho_actual
        instruccion_modo = f"""
        OBJETIVO: Crea un artículo de BLOG INFORMATIVO y educativo sobre el TEMA para el sitio '{nombre_sitio}'.
        TEMA: {tema}
        NICHO: {nicho_actual}
        TONO: Educativo, útil y detallado. Resuelve dudas del usuario de forma exhaustiva.
        PALABRAS CLAVE: {', '.join(palabras_clave)}
        SEO: Distribuye las palabras clave de forma natural. Prioriza la intención de búsqueda informativa.
        REGLA LOCAL: Usa el entorno de '{nicho_actual}' para contextualizar la información con ejemplos reales.
        """
    else:
        # Fallback genérico
        tema = contenido_base if contenido_base else nicho_actual
        instruccion_modo = f"""
        TEMA CENTRAL: {tema}
        CONTEXTO: {nicho_actual}
        PALABRAS CLAVE: {', '.join(palabras_clave)}
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

    REGLAS_SEO_AVANZADO = """
    REQUISITOS SEO Y LEGIBILIDAD (YOAST STYLE):
    1. Keyphrase distribution: Distribuye la palabra clave principal de forma equilibrada en todo el texto.
    2. Outbound links: DEBES incluir enlaces a fuentes externas oficiales o de Wikipedia.
    3. Keyphrase in introduction: La palabra clave debe aparecer en el primer párrafo de forma obligatoria.
    4. Consecutive sentences: EVITA que 3 o más frases seguidas comiencen con la misma palabra. Varía la estructura.
    5. Transition words: Usa palabras de transición (ej: "Por consiguiente", "Además", "Sin embargo", "A continuación") en al menos el 25% de las oraciones.
    6. Passive voice: Usa predominantemente la voz activa. La voz pasiva debe ser mínima (menos del 10%).
    7. Paragraph length: Los párrafos deben ser CORTOS (máximo 3-4 líneas).
    8. Keyphrase density: La palabra clave principal debe aparecer al menos 5-6 veces en el texto.
    9. Keyphrase in meta description: Asegúrate de que el primer párrafo sea potente y contenga la keyword.
    10. Keyphrase in subheadings: Usa la palabra clave o sus sinónimos en al menos el 50% de los subtítulos H2 y H3.
    11. Text length: El texto DEBE tener al menos 1300 palabras para una cobertura completa.
    """

    REGLAS_LEGIBILIDAD_ASTRO = """
    REGLA DE FORMATO (LIMPIO PARA ASTRO Y ALTA ACCESIBILIDAD):
    Genera el contenido usando Markdown y HTML estándar con clases semánticas. 
    
    - ACCESIBILIDAD: El texto debe ser fácil de leer. Usa párrafos cortos.
    - ESPACIADO: Usa `<div class="ui-spacer"></div>` para separar las secciones principales.
    - TÍTULOS: Usa encabezados H1 (solo uno al inicio), H2 (centrados con clase `text-center`), H3 estándar.
    - RESALTADO: Para destacar ideas clave, usa `<span class="ui-highlight">TEXTO RESALTADO</span>`.
    - ICONOS: Incluye un emoji relevante al inicio de los subtítulos principales.
    - SEPARADORES: Usa `<hr class="ui-divider">` para dividir secciones.
    """

    REQUISITOS_WORD_COUNT = config_logic["content"]["min_word_count"] if config_logic else 1300
    MAX_SENTENCES = config_logic["content"]["paragraph_max_sentences"] if config_logic else 3

    REGLAS_COMPONENTES_UI = """
    REQUISITOS DE COMPONENTES VISUALES (UI):
    Para que el contenido sea dinámico y no solo texto, DEBES usar estas estructuras HTML con clases semánticas en al menos 3 secciones del artículo:

    1. TARJETA PREMIUM (ui-card): Úsala para resaltar consejos clave.
       Formato: <div class="ui-card"><h3>Título</h3><p>Contenido...</p></div>

    2. RECUADROS DE LLAMADA (ui-callout):
       - Info: <div class="ui-callout ui-callout-info"><span>ℹ️</span><p>Información útil...</p></div>
       - Tip: <div class="ui-callout ui-callout-tip"><span>💡</span><p>Consejo experto...</p></div>
       - Warning: <div class="ui-callout ui-callout-warning"><span>⚠️</span><p>Atención/Advertencia...</p></div>

    3. TABLA DE COMPARACIÓN (ui-comparison-table): Úsala para comparar datos técnicos.
       Formato: <table class="ui-comparison-table"><thead><tr><th>Concepto</th><th>Detalle</th></tr></thead><tbody><tr><td>Dato 1</td><td>Explicación 1</td></tr></tbody></table>

    4. LISTA DE PASOS (ui-step-list): 
       Formato: <div class="ui-step-list"><div class="ui-step-item"><h4>Paso 1</h4><p>Descripción...</p></div></div>

    5. GRID DE TEXTO + IMAGEN (ui-grid-2):
       <div class="ui-grid-2">
         <div><h3>Título</h3><p>Texto...</p></div>
         <div class="ui-image-side"><img src="URL_IMAGEN" alt="Descripción"></div>
       </div>

    6. ESTADÍSTICAS (ui-stats):
       <div class="ui-stats"><div class="ui-stat-item"><span class="ui-stat-value">97%</span><span class="ui-stat-label">Éxito</span></div></div>

    7. ACORDEÓN / FAQ (ui-accordion): 
       <div class="ui-accordion"><details><summary>¿Pregunta?</summary><div class="accordion-content">Respuesta...</div></details></div>

    8. LÍNEA DE TIEMPO (ui-timeline):
       <div class="ui-timeline"><div class="ui-timeline-step"><span class="step-number">1</span><h4>Título</h4><p>Texto...</p></div></div>

    9. HERO CALLOUT (ui-hero-callout): Bloque de alto impacto visual.
       Formato: <div class="ui-hero-callout"><h2>Título Impactante</h2><p>Texto persuasivo...</p></div>

    10. LISTA DE VERIFICACIÓN (ui-check-list):
        <div class="ui-check-list"><div class="ui-check-item"><span>✅</span><p>Beneficio...</p></div></div>

    11. CITA DESTACADA (ui-quote):
        <div class="ui-quote">"Frase de autoridad."</div>

    12. HERO DE ALTO IMPACTO (ui-hero-full): Úsalo al inicio.
        <div class="ui-hero-full">
          <div class="hero-content">
            <h1>TÍTULO GIGANTE</h1>
            <p>Subtítulo potente.</p>
          </div>
        </div>

    13. SECCIÓN DE ANCHO COMPLETO (ui-section-dark / ui-section-accent / ui-section-sand):
        <div class="ui-section-dark"><div class="container">...</div></div>

    14. GRID MULTI-COLUMNA (ui-grid-3 / ui-grid-4):
        <div class="ui-grid-3">...</div>
    """

    prompt = f"""
    {persona_elegida}
    
    {formato_elegido}
    
    {instruccion_modo}
    
    {REGLAS_SEO_AVANZADO}
    
    {REGLAS_LEGIBILIDAD_ASTRO}
    
    {REGLAS_COMPONENTES_UI}
    
    INSTRUCCIONES DE REDACCIÓN (OBLIGATORIAS):
    1. REGLA DE UNICIDAD RADICAL: Estás generando una de las 16 variantes para una red. Es CRÍTICO que este texto sea 100% original. Cambia el orden de los conceptos, usa sinónimos poco comunes, y varía la longitud de las oraciones. Si el tema es general, aterrizalo a la realidad de '{nicho_actual}' y menciona elementos locales (hospitales, leyes estatales, clima laboral en esa zona) para que Google no vea dos textos iguales.
    2. DISEÑO NIVEL PRO: Tu objetivo es crear una LANDING PAGE DE LUJO. NO generes un bloque de texto plano. Debes jugar con la distribución del contenido usando los componentes UI indicados (class="ui-...").
       - INICIO: Empieza OBLIGATORIAMENTE con un `ui-hero-full` con un título H1 gigante.
       - RITMO VISUAL: Alterna secciones de "Ancho Completo" con secciones de lectura estándar.
       - MULTI-COLUMNAS: Para mostrar beneficios o requisitos, usa un `ui-grid-3` o `ui-grid-4`.
    3. REGLA DE MARCA: El sitio web '{nombre_sitio}' pertenece a la empresa '{nombre_empresa}'. Siempre que te refieras a la organización detrás de la web, usa el nombre '{nombre_empresa}'.
    4. REGLA DE FORMATO: Devuelve el texto en Markdown con los fragmentos HTML de los componentes UI indicados.
    5. REGLA DE LONGITUD: El texto debe tener al menos {REQUISITOS_WORD_COUNT} palabras. Usa párrafos de máximo {MAX_SENTENCES} oraciones.
    6. REGLA DE AUTORIDAD: Debes incluir naturalmente un enlace hacia esta fuente oficial/gubernamental: {url_outbound}. El texto ancla debe ser natural y relevante al contexto.
    7. REGLA DE LEGIBILIDAD: Usa muchas palabras de transición. Evita la voz pasiva. NO uses colores claros para el texto general.
    
    RESTRICCIONES NEGATIVAS (EVITAR PATRONES DE IA):
    - PROHIBIDO usar: "En conclusión", "En resumen", "Por otro lado", "Es importante destacar que", "Adentrémonos", "En el vertiginoso mundo de", "No importa si eres... o si eres...".
    - Empieza con un gancho directo. No hagas intros de "En este artículo hablaremos de...".
    
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
