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
    7. Paragraph length: Los párrafos deben ser CORTOS (máximo 3-4 líneas o 3 oraciones).
    8. Keyphrase density: La palabra clave principal debe aparecer al menos 5-6 veces en el texto.
    9. Keyphrase in meta description: Asegúrate de que el primer párrafo (que servirá de base para la meta descripción) contenga la palabra clave.
    10. Keyphrase in subheadings: Usa la palabra clave o sus sinónimos en al menos el 50% de los subtítulos H2 y H3.
    11. Text length: El texto DEBE tener al menos 1300 palabras para una cobertura completa y autoridad.
    """

    FORMATO_WORDPRESS_BLOQUES = """
    REGLA DE FORMATO (ESTRUCTURA DE BLOQUES WORDPRESS):
    Usa ESTRICTAMENTE los siguientes marcadores de comentarios para separar el contenido, esto es vital para la legibilidad:
    
    - Para Espacios: 
    <!-- wp:spacer {"height":"50px"} -->
    <div style="height:50px" aria-hidden="true" class="wp-block-spacer"></div>
    <!-- /wp:spacer -->

    - Para Párrafos (usar esta estructura):
    <!-- wp:paragraph {"style":{"typography":{"fontStyle":"normal","fontWeight":"300","lineHeight":"2"}},"fontSize":"medium"} -->
    <p style="font-style:normal;font-weight:300;line-height:2">CONTENIDO EL PÁRRAFO AQUÍ</p>
    <!-- /wp:paragraph -->

    - Para Títulos (H2 Centrados):
    <!-- wp:heading {"textAlign":"center","style":{"typography":{"fontStyle":"normal","fontWeight":"300","lineHeight":"2"}},"fontSize":"large"} -->
    <h2 class="wp-block-heading has-text-align-center has-large-font-size" style="font-style:normal;font-weight:300;line-height:2"><strong>TÍTULO AQUÍ</strong></h2>
    <!-- /wp:heading -->

    - Líneas Separadoras: Usa `<hr class="wp-block-separator has-alpha-channel-opacity" style="border-top: 1px solid #ccc; margin: 40px 0;">` para dividir secciones importantes.
    
    - Resaltado (Highlights): Para frases CRÍTICAS o ideas importantes, usa un resaltado de fondo verde claro que sea ACCESIBLE (contraste alto):
    `<span style="background-color: #d4edda; color: #155724; padding: 2px 5px; border-radius: 3px;">TEXTO RESALTADO</span>`. Asegúrate de que el contraste sea apto para PageSpeed Insights.
    
    - Iconos: NO incluyas imágenes. En su lugar, usa iconos de texto o emojis relevantes al inicio de cada sección principal (ej: 🏥, 📚, ✈️, 💰) para mejorar la escaneabilidad.
    """

    prompt = f"""
    {persona_elegida}
    
    {formato_elegido}
    
    {instruccion_modo}
    
    {REGLAS_SEO_AVANZADO}
    
    {FORMATO_WORDPRESS_BLOQUES}
    
    INSTRUCCIONES DE REDACCIÓN (OBLIGATORIAS):
    1. REGLA DE UNICIDAD RADICAL: Estás generando una de las 16 variantes para una red. Es CRÍTICO que este texto sea 100% original. Cambia el orden de los conceptos, usa sinónimos poco comunes, y varía la longitud de las oraciones. Si el tema es general, aterrizalo a la realidad de '{nicho_actual}' y menciona elementos locales (hospitales, leyes estatales, clima laboral en esa zona) para que Google no vea dos textos iguales.
    2. REGLA DE FORMATO: Devuelve el texto ÚNICAMENTE con la estructura de bloques de WordPress especificada arriba. NO uses Markdown estándar para párrafos o títulos, usa los tags `<!-- wp:... -->` y el HTML interno.
    3. REGLA DE LONGITUD: El texto debe tener al menos 1300 palabras.
    4. REGLA DE AUTORIDAD: Debes incluir naturalmente un enlace hacia esta fuente oficial/gubernamental: {url_outbound}. El texto ancla debe ser natural y relevante al contexto.
    5. REGLA DE LEGIBILIDAD: Usa muchas palabras de transición. Evita la voz pasiva.
    
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
