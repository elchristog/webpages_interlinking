import os
import subprocess
import google.generativeai as genai
from datetime import datetime
import json
import random
import shutil
import re
from dotenv import load_dotenv
from generador_prompts import generar_prompt_antidetencion, inicializar_prompts
from generador_interlinking import decidir_si_enlazar, obtener_url_objetivo, obtener_anchor_text, inicializar_interlinking, obtener_enlace_autoridad
import sys
import argparse
import urllib.request
import colorsys
import time

load_dotenv()

# Variables globales para configuración dinámica
config_logic = None
premium_palettes = None
modelo = None

def cargar_recursos_maestros():
    global config_logic, premium_palettes, modelo
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(ruta_base, 'config_logic.json'), 'r', encoding='utf-8') as f:
        config_logic = json.load(f)
    
    with open(os.path.join(ruta_base, 'premium_palettes.json'), 'r', encoding='utf-8') as f:
        premium_palettes = json.load(f)["palettes"]
        
    # Configurar API y modelo desde config_logic
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)
    
    nombre_modelo = config_logic.get("ai", {}).get("model_name", "gemini-2.0-flash-exp")
    modelo = genai.GenerativeModel(nombre_modelo)

# ¡IMPORTANTE! Llamar a la función de carga al inicio
cargar_recursos_maestros()

def cargar_config_global(ruta_proyecto):
    with open(os.path.join(ruta_proyecto, 'config_global.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_config_sitios(ruta_proyecto):
    with open(os.path.join(ruta_proyecto, 'config_sitios.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_config_menus(ruta_proyecto):
    ruta_menus = os.path.join(ruta_proyecto, 'config_menus.json')
    if os.path.exists(ruta_menus):
        with open(ruta_menus, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generar_menu_dinamico(config_menus):
    """Genera un menú con variaciones de keywords según el config_menus."""
    if not config_menus:
        return None
    
    nuevo_menu = []
    for item in config_menus["menu_structure"]:
        categoria = item["id"]
        if categoria in config_menus["variations"]:
            nombre = random.choice(config_menus["variations"][categoria])
        else:
            nombre = categoria.title()
        
        nuevo_menu.append({
            "nombre": nombre,
            "ruta": item["ruta"]
        })
    return nuevo_menu

def guardar_config_global(ruta_proyecto, data):
    ruta_destino = os.path.join(ruta_proyecto, 'config_global.json')
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def escribir_config_inyectada(ruta_proyecto, data):
    ruta_data = os.path.join(ruta_proyecto, 'src', 'data')
    os.makedirs(ruta_data, exist_ok=True)
    ruta_destino = os.path.join(ruta_data, 'config_inyectada.json')
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hsl_to_relative_luminance(h, s, l):
    """
    Calcula la luminancia relativa según el estándar WCAG.
    h: [0, 360], s: [0, 100], l: [0, 100]
    """
    # Convertir HSL a RGB [0, 1]
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    
    # Convertir sRGB a lineal
    def to_linear(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    rl, gl, bl = to_linear(r), to_linear(g), to_linear(b)
    
    # Luminancia relativa
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl

def calcular_contraste_contra_blanco(luminancia):
    """
    Razón de contraste (L1 + 0.05) / (L2 + 0.05)
    Para blanco (L1 = 1.0), es 1.05 / (luminancia + 0.05)
    """
    return 1.05 / (luminancia + 0.05)

def generar_paleta_aleatoria(sitio_id):
    """
    Selecciona una paleta premium de la lista curada.
    Usa el sitio_id como semilla para que sea determinista pero diferente por sitio.
    """
    seed = sum(ord(c) for c in sitio_id)
    random.seed(seed)
    
    paleta = random.choice(premium_palettes)
    
    # Reset random seed after selection to not affect other logic
    random.seed(time.time()) 
    
    return {
        "primary": paleta["primary"],
        "secondary": paleta["secondary"],
        "accent": paleta["accent"],
        "text_bold": paleta["text_bold"],
        "meta": {
            "name": paleta["name"],
            "system": "OKLCH Premium v2"
        }
    }

def limpiar_indices(ruta_proyecto):
    ruta_index = os.path.join(ruta_proyecto, 'src', 'content', 'index.md')
    if os.path.exists(ruta_index):
        os.remove(ruta_index)
        print(f"[*] Index anterior eliminado en {ruta_proyecto}")

def generar_contenido_ia(sitio_id, nicho, palabras_clave, ruta_proyecto, modo="articulo", contenido_base=None, slug_override=None, nombre_sitio="este sitio", nombre_empresa="Enfermera en Estados Unidos"):
    """Llama a Gemini para generar el artículo o la home en formato Markdown."""
    
    config_global = cargar_config_global(ruta_proyecto)
    nombre_empresa = config_global.get("nombre_empresa", "Enfermera en Estados Unidos") # Extract nombre_empresa from global config

    poner_enlace = decidir_si_enlazar()
    url_destino = obtener_url_objetivo() if poner_enlace else "N/A"
    anchor = obtener_anchor_text() if poner_enlace else "N/A"

    url_outbound = obtener_enlace_autoridad()
    prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor, url_outbound=url_outbound, modo=modo, contenido_base=contenido_base, nombre_sitio=nombre_sitio, nombre_empresa=nombre_empresa)
    
    respuesta = modelo.generate_content(prompt)
    content = respuesta.text
    if content.startswith("```markdown"):
        content = content[11:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
        
    config_global = cargar_config_global(ruta_proyecto)
    # YouTube Strategy (Cargando de config_logic)
    prob_distraccion = config_logic["content"]["video_distraction_probability"]
    video_distraccion = random.random() <= prob_distraccion
    if video_distraccion:
        video_url = random.choice(config_global["videos"]["distraccion"])
    else:
        video_url = random.choice(config_global["videos"]["conversion"])
        
    video_iframe = f"\n\n### Recomendación en Video\n<iframe width='560' height='315' src='{video_url}' frameborder='0' allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture' allowfullscreen></iframe>"
    
    if modo == "home":
        slug_generado = "index"
        frontmatter = f"---\ntitulo: \"{nicho.title()}\"\ndescripcion: \"Bienvenidos a {nicho}.\"\nslug: \"index\"\n---\n\n"
    elif modo == "pestaña":
        slug_generado = slug_override if slug_override else f"pagina-{int(datetime.now().timestamp())}"
        frontmatter = f"---\ntitulo: \"{nicho.title()}\"\ndescripcion: \"Información oficial sobre {nicho}.\"\nslug: \"{slug_generado}\"\n---\n\n"
    else:
        slug_generado = f"{sitio_id}-guia-oficial-{int(datetime.now().timestamp())}"
        frontmatter = f"---\ntitulo: \"{nicho.title()}\"\ndescripcion: \"Guía definitiva sobre {nicho}.\"\nslug: \"{slug_generado}\"\nfecha: \"{datetime.now().strftime('%Y-%m-%d')}\"\n---\n\n"
    
    content = frontmatter + content.strip() + video_iframe
    return content, slug_generado

def guardar_markdown(ruta_proyecto, contenido_md, slug, modo="articulo"):
    if modo == "home":
        ruta_dir = os.path.join(ruta_proyecto, 'src', 'content')
        os.makedirs(ruta_dir, exist_ok=True)
        ruta_destino = os.path.join(ruta_dir, "index.md")
    elif modo == "pestaña":
        ruta_dir = os.path.join(ruta_proyecto, 'src', 'content', 'paginas')
        os.makedirs(ruta_dir, exist_ok=True)
        ruta_destino = os.path.join(ruta_dir, f"{slug}.md")
    else:
        ruta_dir = os.path.join(ruta_proyecto, 'src', 'content', 'articulos')
        os.makedirs(ruta_dir, exist_ok=True)
        ruta_destino = os.path.join(ruta_dir, f"{slug}.md")
    
    # Post-procesamiento agresivo para evitar fugas de HTML (raw code blocks)
    lineas_limpias = []
    for linea in contenido_md.split('\n'):
        linea_strip = linea.strip()
        # Si la línea empieza con una etiqueta HTML, removemos todos los espacios al inicio
        if linea_strip.startswith('<') or linea_strip.startswith('</'):
            lineas_limpias.append(linea_strip)
        elif linea_strip.startswith('```'):
             # Evitar que la IA envuelva secciones UI en backticks
             continue 
        else:
            lineas_limpias.append(linea)
    
    contenido_limpio = '\n'.join(lineas_limpias)

    with open(ruta_destino, 'w', encoding='utf-8') as f:
        f.write(contenido_limpio)
    print(f"[+] Archivo guardado: {ruta_destino}")

def procesar_imagenes_seo(sitio_id, nicho, md_content, ruta_recursos, ruta_proyecto_astro):
    """
    Escanea el Markdown en busca de imágenes locales, las copia al proyecto Astro
    con nombres optimizados para SEO y actualiza las rutas.
    """
    if not ruta_recursos or not os.path.isdir(ruta_recursos):
        return md_content

    # Carpeta destino en el proyecto Astro (SITIO ESPECÍFICO)
    # Usamos public/assets/images/[sitio_id] para evitar colisiones
    ruta_public = os.path.join(ruta_proyecto_astro, 'public', 'assets', 'images', sitio_id)
    os.makedirs(ruta_public, exist_ok=True)

    # Patrón para ![alt](src) o <img src="src">
    patrones = [
        r'!\[.*?\]\((.*?)\)',
        r'<img.*?src=["\'](.*?)["\']'
    ]

    for patron in patrones:
        matches = re.findall(patron, md_content)
        for original_src in matches:
            # Solo procesamos si no es una URL externa
            if not original_src.startswith(('http', 'https', '//')):
                nombre_archivo = os.path.basename(original_src)
                ruta_origen = os.path.join(ruta_recursos, nombre_archivo)

                if os.path.exists(ruta_origen):
                    # Generar nombre SEO: slug-nicho + nombre-original
                    slug_nicho = re.sub(r'[^a-z0-0]+', '-', nicho.lower()).strip('-')
                    ext = os.path.splitext(nombre_archivo)[1]
                    nuevo_nombre = f"{slug_nicho}-{os.path.splitext(nombre_archivo)[0]}{ext}"
                    ruta_destino = os.path.join(ruta_public, nuevo_nombre)

                    shutil.copy2(ruta_origen, ruta_destino)
                    
                    # Ruta relativa para la web (desde el raiz de public)
                    web_path = f"/assets/images/{sitio_id}/{nuevo_nombre}"
                    md_content = md_content.replace(original_src, web_path)
                    print(f"[SEO Image] {nombre_archivo} -> {nuevo_nombre}")

    return md_content

def limpiar_markdowns(ruta_proyecto):
    ruta_dir = os.path.join(ruta_proyecto, 'src', 'content', 'articulos')
    if os.path.exists(ruta_dir):
        for f in os.listdir(ruta_dir):
            if f.endswith(".md"):
                os.remove(os.path.join(ruta_dir, f))

def post_procesar_rutas_locales(ruta_persistente):
    """Convierte rutas absolutas en relativas para previsualización local."""
    for root, dirs, files in os.walk(ruta_persistente):
        for file in files:
            if file.endswith(".html"):
                ruta_archivo = os.path.join(root, file)
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                # Reemplazar rutas absolutas de activos y enlaces
                contenido = contenido.replace('href="/', 'href="./')
                contenido = contenido.replace('src="/', 'src="./')
                
                # Caso especial para sitemaps y otros si es necesario
                # (Ajustar según sea necesario si hay niveles de profundidad)
                # Si estamos en blog/slug/index.html, necesitamos ../../
                depth = root.replace(ruta_persistente, "").count(os.sep)
                if depth > 0:
                    prefix = "../" * depth
                    contenido = contenido.replace('href="./', f'href="{prefix}')
                    contenido = contenido.replace('src="./', f'src="{prefix}')

                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(contenido)

def compilar_y_persistir(sitio_id, ruta_proyecto, ruta_base, nombre_proyecto):
    """Construye el sitio y lo mueve a una carpeta persistente para su visualización."""
    ruta_sitios = os.path.join(ruta_base, 'sitios_generados', nombre_proyecto)
    os.makedirs(ruta_sitios, exist_ok=True)
    ruta_persistente = os.path.join(ruta_sitios, sitio_id)
    
    print(f"[*] Compilando Astro para {sitio_id}...")
    comando_build = "npm run build"
    subprocess.run(comando_build, cwd=ruta_proyecto, shell=True)
    
    # Mover dist a la carpeta persistente
    dist_path = os.path.join(ruta_proyecto, 'dist')
    if os.path.exists(ruta_persistente):
        # SI la carpeta existe, no la borramos completa para no perder el MD si ya estaba
        pass
    else:
        os.makedirs(ruta_persistente, exist_ok=True)
    
    # [NUEVO] Persistir el Markdown original para revisión manual si falla el build
    ruta_md_origen = os.path.join(ruta_proyecto, 'src', 'content', 'index.md')
    if os.path.exists(ruta_md_origen):
        shutil.copy2(ruta_md_origen, os.path.join(ruta_persistente, "index.md"))
        print(f"[Backup MD] index.md guardado en {ruta_persistente}")

    subprocess.run(comando_build, cwd=ruta_proyecto, shell=True)
    
    if os.path.exists(dist_path):
        shutil.copytree(dist_path, ruta_persistente, dirs_exist_ok=True)
        post_procesar_rutas_locales(ruta_persistente)
        print(f"[+] Sitio {sitio_id} persistido y post-procesado en: {ruta_persistente}")
    else:
        print(f"[-] Error: No se encontró la carpeta /dist tras la compilación en {ruta_proyecto}")

def generar_index_dashboard(ruta_base, sitios, nombre_proyecto):
    """Genera un archivo index.html central para navegar entre los sitios del proyecto."""
    ruta_dashboard = os.path.join(ruta_base, 'sitios_generados', nombre_proyecto, 'index.html')
    
    # [FIX] Asegurar que usamos todos los sitios disponibles en la carpeta si 'sitios' viene incompleto
    ruta_sitios_folder = os.path.dirname(ruta_dashboard)
    sitios_en_disco = [d for d in os.listdir(ruta_sitios_folder) if os.path.isdir(os.path.join(ruta_sitios_folder, d))]
    
    # Re-mapear para tener la información mínima necesaria para el dashboard
    sitios_finales = []
    for s_id in sitios_en_disco:
        es_money = (s_id == 'money_site')
        # Intentar buscar el dominio en el objeto 'sitios' original si existe
        dominio = next((s['dominio'] for s in sitios if s['id'] == s_id), "Previsualización local")
        sitios_finales.append({"id": s_id, "dominio": dominio, "is_money": es_money})

    # Sort: money_site first, then alphabetical
    sitios_finales.sort(key=lambda x: (not x["is_money"], x["id"]))

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PBN Control Center - {nombre_proyecto}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #fcfcfd; }}
        .glass {{ background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(229, 231, 235, 0.5); }}
        .card-money {{ background: linear-gradient(135deg, #000 0%, #1a1a1a 100%); }}
    </style>
</head>
<body class="p-6 md:p-12 lg:p-20 text-zinc-900">
    <div class="max-w-7xl mx-auto">
        <header class="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-zinc-200 pb-12">
            <div>
                <div class="flex items-center gap-3 mb-4">
                    <span class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                    <span class="text-xs font-bold tracking-widest uppercase text-zinc-400">Network Live Preview</span>
                </div>
                <h1 class="text-5xl font-extrabold tracking-tight text-black">{nombre_proyecto.replace('_', ' ').title()}</h1>
                <p class="text-zinc-500 mt-3 text-lg">PBN Management Dashboard & Site Auditor</p>
            </div>
            <div class="flex gap-4">
                <div class="glass px-6 py-4 rounded-2xl text-center">
                    <span class="block text-2xl font-bold">{len(sitios_en_disco)}</span>
                    <span class="text-[10px] uppercase tracking-wider font-bold text-zinc-400">Sitios Totales</span>
                </div>
            </div>
        </header>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
    """
    
    for s in sitios_finales:
        if s['is_money']:
            card_classes = "card-money text-white shadow-2xl ring-offset-2 ring-2 ring-blue-600"
            badge = "<span class='bg-blue-600 text-[10px] px-2 py-1 rounded-full font-black uppercase tracking-tighter'>Money Site</span>"
            text_muted = "text-zinc-400"
        else:
            card_classes = "glass hover:bg-white hover:shadow-xl transition-all duration-300"
            badge = "<span class='bg-zinc-100 text-zinc-500 text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-tighter'>Mirror</span>"
            text_muted = "text-zinc-500"

        html += f"""
            <a href="./{s['id']}/index.html" target="_blank" class="{card_classes} group p-8 min-h-[18rem] flex flex-col justify-between rounded-[2rem] border border-zinc-100">
                <div>
                   <div class="flex justify-between items-start mb-6">
                       <div class="w-10 h-10 bg-zinc-100 dark:bg-zinc-800 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                           <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9h18"/></svg>
                       </div>
                       {badge}
                   </div>
                   <h2 class="font-bold text-xl leading-tight group-hover:text-blue-600 transition-colors uppercase tracking-tight">{s['id'].replace('_', ' ').replace('-', ' ')}</h2>
                   <p class="{text_muted} text-xs mt-3 font-medium truncate">{s['dominio']}</p>
                </div>
                <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-widest group-hover:translate-x-1 transition-transform">
                    Explorar Sitio 
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                </div>
            </a>
        """
        
    html += """
        </div>
        <footer class="mt-32 pt-8 border-t border-zinc-100 flex justify-between items-center text-zinc-400 text-[10px] font-bold uppercase tracking-widest">
            <span>PBN Control Center v2.0</span>
            <span>Generado: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """</span>
        </footer>
    </div>
</body>
</html>
    """
    
    with open(ruta_dashboard, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[+] Dashboard generado en: {ruta_dashboard}")

def preparar_identidad_sitio(sitio_id, configuracion_actual, config_global, config_menus, ruta_proyecto_config):
    """Configura y persiste la identidad (colores, layout, etc) de un sitio."""
    cambio_detectado = False
    
    # Generar Menú Dinámico si existe configuración
    menu_dinamico = generar_menu_dinamico(config_menus)
    if menu_dinamico:
        configuracion_actual["menu_global"] = menu_dinamico
        print(f"[*] Menú dinámico generado para {sitio_id}")
    
    if "layout" not in configuracion_actual:
        configuracion_actual["layout"] = random.choice(config_logic["ui"]["layouts"])
        cambio_detectado = True
    
    if "nav_footer_version" not in configuracion_actual:
        configuracion_actual["nav_footer_version"] = random.choice(config_logic["ui"]["available_nav_versions"] if "available_nav_versions" in config_logic["ui"] else ["v1", "v2", "v3"])
        cambio_detectado = True

    if "font_family" not in configuracion_actual:
        configuracion_actual["font_family"] = random.choice(config_logic["ui"]["available_fonts"])
        cambio_detectado = True
    
    if configuracion_actual.get("layout") == "LayoutB" and "sidebar_pos" not in configuracion_actual:
        configuracion_actual["sidebar_pos"] = random.choice(["left", "right"])
        cambio_detectado = True

    if "color_palette" not in configuracion_actual or "meta" not in configuracion_actual["color_palette"] or configuracion_actual["color_palette"]["meta"].get("system") != "OKLCH Premium v2":
        configuracion_actual["color_palette"] = generar_paleta_aleatoria(sitio_id)
        cambio_detectado = True
    
    if cambio_detectado:
        config_global["sitios"][sitio_id] = configuracion_actual
        guardar_config_global(ruta_proyecto_config, config_global)
        print(f"[!] Identidad persistida para {sitio_id}")
    
    return configuracion_actual

def procesar_sitio(sitio, config_global, config_menus, ruta_proyecto_config, ruta_base, nombre_proyecto, modo_propagar=None, input_base=None, slug_pestaña=None, ruta_recursos=None):
    sitio_id = sitio['id']
    print(f"\n=== Procesando {sitio_id} ===")
    
    # Limpiar dist para evitar rastro de otros sitios
    dist_path = os.path.join(sitio['ruta_astro'], 'dist')
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    
    configuracion_actual = config_global["sitios"][sitio_id].copy()
    configuracion_actual["dominio"] = sitio.get("dominio", "http://localhost:4321")
    
    configuracion_actual = preparar_identidad_sitio(sitio_id, configuracion_actual, config_global, config_menus, ruta_proyecto_config)
    
    # Asegurar nombre de empresa global
    nombre_empresa_global = config_global.get("nombre_empresa", "Enfermera en Estados Unidos")
    if "footer" in configuracion_actual:
        configuracion_actual["footer"]["empresa_legal"] = nombre_empresa_global
    
    escribir_config_inyectada(sitio['ruta_astro'], configuracion_actual)

    if modo_propagar:
        # Modo propagación dirigida
        print(f"[*] Propagando {modo_propagar} para {sitio_id}...")
        contenido_ia, slug_final = generar_contenido_ia(
            sitio_id, 
            sitio['nicho'], 
            sitio['palabras_clave'], 
            ruta_proyecto_config, 
            modo=modo_propagar, 
            contenido_base=input_base,
            slug_override=slug_pestaña,
            nombre_sitio=configuracion_actual["nombre_sitio"],
            nombre_empresa=nombre_empresa_global
        )
        
        # PROCESAR IMÁGENES SEO
        contenido_ia = procesar_imagenes_seo(sitio_id, sitio['nicho'], contenido_ia, ruta_recursos, sitio['ruta_astro'])
        
        guardar_markdown(sitio['ruta_astro'], contenido_ia, slug_final, modo=modo_propagar)
    else:
        # Modo generación base/bulk
        limpiar_markdowns(sitio['ruta_astro'])
        limpiar_indices(sitio['ruta_astro'])
        
        print(f"[*] Generando artículo inicial para {sitio_id}...")
        markdown_ia, slug_generado = generar_contenido_ia(sitio_id, sitio['nicho'], sitio['palabras_clave'], ruta_proyecto_config, modo="articulo")
        
        # PROCESAR IMÁGENES SEO (Incluso en base si hubiera, aunque usualmente no hay en base)
        markdown_ia = procesar_imagenes_seo(sitio_id, sitio['nicho'], markdown_ia, ruta_recursos, sitio['ruta_astro'])
        
        guardar_markdown(sitio['ruta_astro'], markdown_ia, slug_generado)
    
    compilar_y_persistir(sitio_id, sitio['ruta_astro'], ruta_base, nombre_proyecto)
    return {"id": sitio_id, "dominio": configuracion_actual["dominio"]}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador SEO PBN - Generador de Sitios Espejo")
    parser.add_argument("proyecto", help="Nombre del proyecto (ej: enfermera_en_estados_unidos)")
    parser.add_argument("--propagar", action="store_true", help="Activa el modo propagación de contenido específico")
    parser.add_argument("--modo", choices=["home", "pestaña", "blog"], default="articulo", help="Tipo de contenido a propagar")
    parser.add_argument("--slug", help="Slug para la pestaña o artículo (obligatorio para --modo pestaña)")
    parser.add_argument("--inputfile", help="Archivo .txt con el contenido base o tema a propagar")
    parser.add_argument("--cola", nargs='?', const='ALL', help="Procesa archivos en input_cola/. Especifica un archivo (ej: mi_articulo.json) o deja vacío para listar disponibles.")
    
    args = parser.parse_args()
    
    nombre_proyecto = args.proyecto
    ruta_base = os.getcwd()
    ruta_proyecto_config = os.path.join(ruta_base, 'proyectos', nombre_proyecto)
    
    if not os.path.exists(ruta_proyecto_config):
        print(f"[-] Error: No existe la carpeta del proyecto en {ruta_proyecto_config}")
        sys.exit(1)

    peticiones = []
    
    if args.cola:
        ruta_cola = os.path.join(ruta_proyecto_config, 'input_cola')
        if not os.path.exists(ruta_cola):
            print("[-] Error: No existe la carpeta input_cola/")
            sys.exit(1)
            
        # Listar archivos y CARPETAS
        elementos_disponibles = sorted([f for f in os.listdir(ruta_cola) if not f.startswith('.')])
        
        if not elementos_disponibles:
            print("[*] La cola está vacía.")
            sys.exit(0)

        # Si el usuario NO especificó un archivo (args.cola es 'ALL')
        if args.cola == 'ALL':
            print("\n[*] Elementos disponibles en la cola (input_cola/):")
            for i, f in enumerate(elementos_disponibles, 1):
                tipo = "[DIR]" if os.path.isdir(os.path.join(ruta_cola, f)) else "[FILE]"
                print(f"  {i}. {tipo} {f}")
            print("\n[!] Por seguridad, debes especificar qué elemento quieres generar.")
            print(f"Ejemplo: python orquestador_seo.py {nombre_proyecto} --cola {elementos_disponibles[0]}")
            sys.exit(0)
        else:
            # El usuario especificó un archivo o carpeta
            item_buscado = args.cola
            ruta_item = os.path.join(ruta_cola, item_buscado)
            
            # Fallback si no puso .json y no es carpeta
            if not os.path.exists(ruta_item) and not item_buscado.endswith(".json"):
                ruta_item += ".json"

            if os.path.exists(ruta_item):
                if os.path.isdir(ruta_item):
                    # Es una CARPETA: buscar primer JSON dentro
                    jsons = [f for f in os.listdir(ruta_item) if f.endswith(".json")]
                    if not jsons:
                        print(f"[-] Error: No hay ningun archivo .json dentro de la carpeta {item_buscado}")
                        sys.exit(1)
                    
                    ruta_json = os.path.join(ruta_item, jsons[0])
                    with open(ruta_json, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                        data["_ruta_recursos"] = ruta_item # Inyectar ruta para luego usarla
                        peticiones.append(data)
                else:
                    # Es un ARCHIVO con una o más peticiones
                    with open(ruta_item, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                        if isinstance(data, list):
                            peticiones.extend(data)
                        else:
                            peticiones.append(data)
            else:
                print(f"[-] Error: No se encuentra el elemento '{args.cola}' en input_cola/")
                sys.exit(1)
    elif args.inputfile:
        if os.path.exists(args.inputfile):
            with open(args.inputfile, 'r', encoding='utf-8') as f:
                input_text = f.read()
            peticiones.append({
                "modo": args.modo,
                "slug": args.slug,
                "input_base": input_text
            })
        else:
            print(f"[-] Error: No se encuentra el archivo de entrada {args.inputfile}")
            sys.exit(1)
    elif args.propagar:
        # Si se usa --propagar sin inputfile, buscamos un input default o error
        print("[-] Error: Debes especificar --inputfile o usar --cola")
        sys.exit(1)

    inicializar_interlinking(ruta_proyecto_config)
    inicializar_prompts(ruta_proyecto_config)
    
    config_global = cargar_config_global(ruta_proyecto_config)
    config_sitios = cargar_config_sitios(ruta_proyecto_config)
    config_menus = cargar_config_menus(ruta_proyecto_config)
    
    if not peticiones:
        # Generación base (bulk) si no hay peticiones específicas
        print("[*] Iniciando generación base (bulk)...")
        sitios_procesados = []
        for sitio in config_sitios["sitios_espejo"]:
            resultado = procesar_sitio(
                sitio, config_global, config_menus, 
                ruta_proyecto_config, ruta_base, nombre_proyecto
            )
            sitios_procesados.append(resultado)
        generar_index_dashboard(ruta_base, sitios_procesados, nombre_proyecto)
    else:
        sitios_procesados = []
        for p in peticiones:
            print(f"\n[*] Procesando petición: {p.get('tema', p.get('slug', 'sin nombre'))}")
            modo_ejecucion = p.get("modo", "articulo")
            input_text = p.get("contenido") or p.get("tema") or p.get("input_base") or p.get("contenido_base")
            slug_pestaña = p.get("slug")
            
            ruta_recursos = p.get("_ruta_recursos")
            for sitio in config_sitios["sitios_espejo"]:
                resultado = procesar_sitio(
                    sitio, config_global, config_menus, 
                    ruta_proyecto_config, ruta_base, nombre_proyecto,
                    modo_propagar=modo_ejecucion,
                    input_base=input_text,
                    slug_pestaña=slug_pestaña,
                    ruta_recursos=ruta_recursos
                )
                sitios_procesados.append(resultado)
            generar_index_dashboard(ruta_base, sitios_procesados, nombre_proyecto)

    print("\n[!!!] PROCESO COMPLETADO [!!!]")
    print(f"Dashboard: file://{os.path.join(ruta_base, 'sitios_generados', nombre_proyecto, 'index.html')}")
