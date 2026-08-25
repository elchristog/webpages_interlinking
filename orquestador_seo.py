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
from PIL import Image
import colorsys
import time

load_dotenv()

def generar_slug_nicho(nicho):
    return re.sub(r'[^a-z0-9]+', '-', str(nicho).lower()).strip('-')

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

def gestionar_estado_contenido(sitio_id, ruta_proyecto, ruta_base, nombre_proyecto, modo_propagar):
    """
    Restaura el estado de src/content/ desde el backup de este sitio específico,
    o lo limpia completamente si es una generación desde cero.
    """
    ruta_src_content = os.path.join(ruta_proyecto, 'src', 'content')
    ruta_backup = os.path.join(ruta_base, 'sitios_generados', nombre_proyecto, sitio_id, 'md_backup')
    
    # Asegurar que exista la carpeta src/content de la plantilla
    os.makedirs(ruta_src_content, exist_ok=True)
    
    if modo_propagar:
        # Si estamos propagando (añadiendo pagina), restaurar el backup
        if os.path.exists(ruta_backup):
            shutil.copytree(ruta_backup, ruta_src_content, dirs_exist_ok=True)
            print(f"[+] Estado de contenido restaurado para {sitio_id}")
    else:
        # Si es generación base, borrar el backup si existe para empezar limpio
        if os.path.exists(ruta_backup):
            shutil.rmtree(ruta_backup)

def respaldar_estado_contenido(sitio_id, ruta_proyecto, ruta_base, nombre_proyecto):
    """
    Guarda todo src/content/ actual en la carpeta de backup del sitio específico
    antes de la compilación.
    """
    ruta_src_content = os.path.join(ruta_proyecto, 'src', 'content')
    ruta_backup = os.path.join(ruta_base, 'sitios_generados', nombre_proyecto, sitio_id, 'md_backup')
    
    if os.path.exists(ruta_src_content):
        if os.path.exists(ruta_backup):
            shutil.rmtree(ruta_backup)
        shutil.copytree(ruta_src_content, ruta_backup, dirs_exist_ok=True)
        print(f"[+] Estado de contenido respaldado para {sitio_id}")


def generar_contenido_ia(sitio_id, nicho, palabras_clave, ruta_proyecto, modo="articulo", contenido_base=None, slug_override=None, nombre_sitio="este sitio", nombre_empresa="Enfermera en Estados Unidos"):
    """Llama a Gemini para generar el artículo o la home en formato Markdown."""
    
    config_global = cargar_config_global(ruta_proyecto)
    nombre_empresa = config_global.get("nombre_empresa", "Enfermera en Estados Unidos") # Extract nombre_empresa from global config

    poner_enlace = decidir_si_enlazar()
    url_destino = obtener_url_objetivo() if poner_enlace else "N/A"
    anchor = obtener_anchor_text() if poner_enlace else "N/A"

    url_outbound = obtener_enlace_autoridad()
    
    # Check for local project images
    ruta_imagenes = os.path.join(ruta_proyecto, 'imagenes')
    imagenes_proyecto = []
    if os.path.exists(ruta_imagenes):
        slug_nicho = generar_slug_nicho(nicho) if nicho else "imagen-seo"
        archivos_img = sorted([f for f in os.listdir(ruta_imagenes) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')) and 'logo' not in f.lower()])
        for i, img in enumerate(archivos_img):
            imagenes_proyecto.append(f"/imagenes_proyecto/{slug_nicho}-{i+1}.webp")
                
    prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor, url_outbound=url_outbound, modo=modo, contenido_base=contenido_base, nombre_sitio=nombre_sitio, nombre_empresa=nombre_empresa, imagenes_proyecto=imagenes_proyecto)
    
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
        fecha_str = datetime.now().strftime('%Y-%m-%d')
        frontmatter = f"""---
title: "{nicho.title()}"
pubDate: {fecha_str}
description: "Guía definitiva sobre {nicho}."
team: "david-lee"
image:
  url: "/src/images/blog/1.jpg"
  alt: "{nicho.title()}"
tags:
  - enfermeria
  - empleos
---

"""
    
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
        dir_posts = os.path.join(ruta_proyecto, 'src', 'content', 'posts')
        if os.path.exists(dir_posts):
            ruta_dir = dir_posts
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
    
    import re
    contenido_limpio = '\n'.join(lineas_limpias)
    contenido_limpio = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer" class="ui-inline-link">\1</a>', contenido_limpio)

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

# Función de limpiar_markdowns eliminada porque gestionar_estado_contenido maneja la limpieza.

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
                contenido = contenido.replace("url(&#x27;/", "url('./")
                contenido = contenido.replace("url(&#x27;", "url('")
                contenido = contenido.replace("&#x27;)", "')")
                contenido = contenido.replace("url('/", "url('./")
                contenido = contenido.replace('url("/', 'url("./')

                # Reemplazar placeholders por imágenes reales del proyecto
                import re
                img_idx = 1
                def repl_placeholder(match):
                    nonlocal img_idx
                    res = f'src="./imagenes_proyecto/ofertas-de-empleo-y-salarios-promedios-para-enfermeras-extranjeras-en-miami-y-tampa-florida-{(img_idx % 8) + 1}.webp"'
                    img_idx += 1
                    return res
                contenido = re.sub(r'src="https?://via\.placeholder\.com/[^"]+"', repl_placeholder, contenido)
                
                # Caso especial para sitemaps y otros si es necesario
                # Si estamos en blog/slug/index.html, necesitamos ../../
                depth = root.replace(ruta_persistente, "").count(os.sep)
                if depth > 0:
                    prefix = "../" * depth
                    contenido = contenido.replace('href="./', f'href="{prefix}')
                    contenido = contenido.replace('src="./', f'src="{prefix}')
                    contenido = contenido.replace('url("./', f'url("{prefix}')
                    contenido = contenido.replace("url('./", f"url('{prefix}")

                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(contenido)

def procesar_e_inyectar_media(sitio_id, ruta_proyecto, ruta_base, nombre_proyecto, nicho):
    """
    Procesa el logo e imágenes del proyecto, los convierte a WebP, 
    crea los favicons y reemplaza las referencias de imagen en componentes,
    páginas y markdown para que apunten a los archivos .webp locales del nicho.
    """
    ruta_imagenes = os.path.join(ruta_base, 'proyectos', nombre_proyecto, 'imagenes')
    ruta_public_imagenes = os.path.join(ruta_proyecto, 'public', 'imagenes_proyecto')
    
    if os.path.exists(ruta_public_imagenes):
        shutil.rmtree(ruta_public_imagenes)
        
    os.makedirs(ruta_public_imagenes, exist_ok=True)
    slug_nicho = generar_slug_nicho(nicho) if nicho else "imagen-seo"
    
    archivos_webp_generados = []
    
    if os.path.exists(ruta_imagenes):
        todos_archivos = sorted([f for f in os.listdir(ruta_imagenes) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg'))])
        archivos_img = [f for f in todos_archivos if 'logo' not in f.lower()]
        archivos_logo = [f for f in todos_archivos if 'logo' in f.lower()]

        # 1. Procesar Logo y Favicon
        if archivos_logo:
            logo_src = os.path.join(ruta_imagenes, archivos_logo[0])
            logo_dst = os.path.join(ruta_public_imagenes, "logo.webp")
            favicon_ico = os.path.join(ruta_proyecto, "public", "favicon.ico")
            favicon_png = os.path.join(ruta_proyecto, "public", "favicon.png")
            apple_touch = os.path.join(ruta_proyecto, "public", "apple-touch-icon.png")
            
            try:
                with Image.open(logo_src) as im:
                    im.save(logo_dst, "webp", quality=90)
                    if im.mode != "RGBA":
                        im_ico = im.convert("RGBA")
                    else:
                        im_ico = im
                    im_ico.save(favicon_ico, "ICO", sizes=[(32, 32), (48, 48)])
                    im_ico.save(favicon_png, "PNG")
                    im_ico.save(apple_touch, "PNG")
                    print(f"[Media Injector] Logo y Favicons generados en WebP e ICO")
            except Exception as e:
                print(f"[-] Error al generar favicons desde logo: {e}")
                shutil.copy2(logo_src, logo_dst)
                shutil.copy2(logo_src, favicon_ico)
                shutil.copy2(logo_src, favicon_png)
                shutil.copy2(logo_src, apple_touch)

        # 2. Convertir imágenes a .webp
        for i, img in enumerate(archivos_img):
            src_path = os.path.join(ruta_imagenes, img)
            dst_filename = f"{slug_nicho}-{i+1}.webp"
            dst_path = os.path.join(ruta_public_imagenes, dst_filename)
            
            try:
                with Image.open(src_path) as im:
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    im.save(dst_path, "webp", quality=85)
                    archivos_webp_generados.append(f"/imagenes_proyecto/{dst_filename}")
            except Exception as e:
                print(f"[-] Error al convertir {img} a webp: {e}")
                shutil.copy2(src_path, dst_path)
                archivos_webp_generados.append(f"/imagenes_proyecto/{dst_filename}")
    
    if not archivos_webp_generados:
        archivos_webp_generados = ["/imagenes_proyecto/logo.webp"]

    # 3. Inyectar Logo en componentes Logo.astro y BigLogo.astro
    rutas_componentes = os.path.join(ruta_proyecto, 'src', 'components')
    if os.path.exists(rutas_componentes):
        for root, dirs, files in os.walk(rutas_componentes):
            for file in files:
                if file in ("Logo.astro", "BigLogo.astro"):
                    logo_file_path = os.path.join(root, file)
                    try:
                        with open(logo_file_path, 'w', encoding='utf-8') as f:
                            f.write('''---
const { class: className = "", ...rest } = Astro.props;
---
<img
  src="/imagenes_proyecto/logo.webp"
  alt="Logo"
  class={className || "h-8 w-auto object-contain"}
  {...rest}
  onerror="this.onerror=null; this.src='/favicon.ico';"
/>
''')
                        print(f"[Media Injector] Actualizado {file} -> /imagenes_proyecto/logo.webp")
                    except Exception as e:
                        print(f"[-] Error actualizando logo en {file}: {e}")

    # 4. Actualizar Favicons.astro
    if os.path.exists(rutas_componentes):
        for root, dirs, files in os.walk(rutas_componentes):
            for file in files:
                if file == "Favicons.astro":
                    fav_path = os.path.join(root, file)
                    try:
                        with open(fav_path, 'w', encoding='utf-8') as f:
                            f.write('''<!-- Favicons -->
<link rel="icon" type="image/webp" href="/imagenes_proyecto/logo.webp" />
<link rel="shortcut icon" href="/imagenes_proyecto/logo.webp" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="icon" href="/favicon.ico" sizes="any" />
''')
                        print(f"[Media Injector] Actualizado Favicons.astro -> /imagenes_proyecto/logo.webp")
                    except Exception as e:
                        print(f"[-] Error actualizando favicons: {e}")

    # 5. Reemplazar imágenes dummy por imágenes .webp en components, pages y content
    rutas_a_escanear = [
        os.path.join(ruta_proyecto, 'src', 'components'),
        os.path.join(ruta_proyecto, 'src', 'pages'),
        os.path.join(ruta_proyecto, 'src', 'content')
    ]

    img_counter = 0
    num_imgs = len(archivos_webp_generados)

    for carpeta in rutas_a_escanear:
        if not os.path.exists(carpeta):
            continue
        for root, dirs, files in os.walk(carpeta):
            for file in files:
                if file.endswith(('.astro', '.md', '.tsx', '.jsx')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        modificado = False
                        
                        # 1. Detectar y reemplazar imports ESM de imágenes (import VarName from "@/images/...")
                        patron_import_img = r'import\s+([A-Za-z0-9_]+)\s+from\s+["\']([^"\']*(?:/images/|@/images/)[^"\']+)["\'];?'
                        imports_encontrados = re.findall(patron_import_img, content)
                        for var_name, import_path in imports_encontrados:
                            if "logo" in import_path.lower() or "logo" in var_name.lower():
                                img_actual = "/imagenes_proyecto/logo.webp"
                            else:
                                img_actual = archivos_webp_generados[img_counter % num_imgs]
                                img_counter += 1
                            
                            # Reemplazar la declaración import por const VarName = "img_actual";
                            content = re.sub(
                                r'import\s+' + re.escape(var_name) + r'\s+from\s+["\'][^"\']+["\'];?',
                                f'const {var_name} = "{img_actual}";',
                                content
                            )
                            modificado = True

                        # 2. Convertir todas las etiquetas <Image ... /> y </Image> en etiquetas <img ... />
                        if re.search(r'<Image\b', content):
                            content = re.sub(r'<Image\b', '<img', content)
                            content = re.sub(r'</Image>', '</img>', content)
                            modificado = True

                        # 3. Reemplazar rutas dummy de imágenes restantes (/src/images/..., @/images/..., etc.)
                        patron_dummy = r'(/src/images/[^\s"\'\)]+|@/images/[^\s"\'\)]+|\./_astro/[^\s"\'\)]+)'
                        matches = re.findall(patron_dummy, content)
                        if matches:
                            for match in set(matches):
                                if "logo" in match.lower():
                                    content = content.replace(match, "/imagenes_proyecto/logo.webp")
                                else:
                                    img_actual = archivos_webp_generados[img_counter % num_imgs]
                                    img_counter += 1
                                    content = content.replace(match, img_actual)
                                modificado = True

                        if modificado:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"[Media Injector] Imágenes WebP inyectadas en {file}")
                    except Exception as e:
                        pass

def compilar_y_persistir(sitio_id, ruta_proyecto, ruta_base, nombre_proyecto, nicho=""):
    """Construye el sitio y lo mueve a una carpeta persistente para su visualización."""
    ruta_sitios = os.path.join(ruta_base, 'sitios_generados', nombre_proyecto)
    os.makedirs(ruta_sitios, exist_ok=True)
    ruta_persistente = os.path.join(ruta_sitios, sitio_id)
    
    print(f"[*] Compilando Astro para {sitio_id}...")
    comando_build = "npm run build"
    subprocess.run(comando_build, cwd=ruta_proyecto, shell=True)
    
    # Mover dist a la carpeta persistente
    dist_path = os.path.join(ruta_proyecto, 'dist')
    if not os.path.exists(ruta_persistente):
        os.makedirs(ruta_persistente, exist_ok=True)
    
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

def personalizar_componentes_plantilla(ruta_astro, nicho, palabras_clave):
    """
    Escanea la carpeta src/components/, src/pages/ y src/content/ del proyecto Astro
    y reemplaza automáticamente cualquier texto de relleno en inglés por contenido en español
    adaptado al nicho del sitio.
    """
    if not os.path.exists(ruta_astro):
        return

    nicho_title = nicho.strip()
    kw_str = ", ".join(palabras_clave[:3]) if palabras_clave else "enfermería en USA"

    reemplazos_directos = [
        # Heros & Headers principales
        ("Plug it in before your coffee gets cold", f"Todo lo que necesitas para ejercer como Enfermera en EE. UU."),
        ("Clean, no-BS interface. Set it up in minutes, send emails even faster.", f"Un programa estructurado para acompañarte desde la convalidación hasta tu trabajo hospitalario."),
        ("Built by developers who were sick of broken email APIs", f"Ventajas Exclusivas de Nuestro Programa de Reclutamiento"),
        ("We got tired of wrestling with clunky tools, so we built the email platform we always wanted — fast, clean, and actually works without swearing at your terminal.", f"Diseñamos un proceso transparente e integral, respaldado por expertos en inmigración y docentes de enfermería."),
        ("Write Like a Human, Not a Hacker", f"Asesoría Personalizada y Acompañamiento Continuo"),
        ("Finally, an editor that doesn’t fight you. Format, style, and send emails without touching a single . Build visually, tweak freely, and leave the HTML rage-quits behind.", f"Te acompañamos en cada etapa: evaluación de credenciales CGFNS, preparación de examen y trámite consular."),
        ("Contact Management That Doesn’t Suck", f"Gestión Consular y Patrocinio Visa EB-3"),
        ("Import your entire list in minutes — whether it’s 50 or 50,000. See every contact’s details without clicking through 12 tabs. It’s like a CRM, but without the bloat (or the monthly breakdown).", f"Un equipo legal de inmigración gestiona tu petición I-140 y visa de residencia permanente (Green Card)."),
        ("Broadcast Analytics (Because Guesswork Is for Amateurs)", f"Preparación del Examen NCLEX-RN con Métodos Probados"),
        ("See who opened, clicked, ignored, or rage-deleted your email. Real insights, no fluff — so you actually know what’s working (and what’s not).", f"Nuestros docentes capacitados te guían con simuladores reales NGN para aprobar en tu primer intento."),
        ("Email, But Actually Good", f"Tu Futuro como Enfermera en EE. UU. Empieza Hoy"),
        ("No setup rituals. No DNS sorcery. Just emails that send, land, and look damn good doing it. — Available now. Because why wait?", f"Evaluamos tu perfil profesional sin costo y trazamos la ruta directa hacia tu empleo en EE. UU."),
        ("Plans that grow with your ambition (or chaos)", f"Programas Diseñados para Tu Éxito Profesional"),
        ("Start free. Pay when your side project accidentally turns into a business.", f"Elige la fase en la que te encuentras o realiza la ruta completa con nuestro acompañamiento."),
        ("No concepts. Just real websites.", f"Licencia de Enfermería & Oportunidades Laborales"),
        ("A curated collection of production websites worth studying — layout, hierarchy, interaction, and execution. Use them to benchmark your own work, not to copy it.", f"Guía actualizada sobre homologación de títulos, visados de residencia EB-3 y salarios de enfermería."),
        ("Design Smarter. Build Better.", f"Guía Oficial: {nicho_title}"),
        ("A course for developers who care about design. Learn to craft beautiful, responsive UIs with precision — from layout to component polish.", f"Información estratégica sobre revalidación de credenciales, cursos NCLEX-RN y patrocinio hospitalario."),
        ("What will you sharpen next?", f"Recursos Destacados y Guías de Estudio"),
        ("New lessons and UI patterns released regularly. Stay sharp, stay current — and keep building with confidence.", f"Explora nuestros artículos detallados sobre trámites de enfermería, visas laborales y consejos de examen."),

        # Botones y enlaces de navegación
        ("Get full access", "Solicitar Evaluación Gratuita"),
        ("Get Started", "Iniciar Proceso"),
        ("Get pro access", "Conocer Requisitos"),
        ("Upgrade Now", "Aplicar al Programa"),
        ("Learn more", "Ver Guías"),
        ("Buy Brightlight", "Contacto"),
        ("Buy ", "Contacto "),
        ("Sign in", "Asesoría"),
        ("Overview", "Inicio"),

        # Tarjetas de características
        ("Test Mode (aka Safe Chaos)", "Homologación Directa"),
        ("Blow things up without consequences. Simulate everything, send nothing. Perfect for testing, debugging, and not losing your job.", "Evaluamos tus credenciales universitarias para cumplir los requisitos del Board de Enfermería."),
        ("Webhooks That Actually Work", "Preparación NCLEX-RN"),
        ("We ping your server the second something happens — delivery, open, click, bounce, interpretive dance. You’ll know.", "Clases en vivo y simuladores adaptativos NGN con más de 3,000 preguntas preparatorias."),
        ("Live Logs (Bring Popcorn)", "Patrocinio Visa EB-3"),
        ("Every request, every response, every oops — logged in real time. It's like tailing your server logs, but less painful.", "Petición de Residencia Permanente (Green Card) para ti, tu cónyuge e hijos menores de 21 años."),
        ("Retry Logic That Babysits for You", "Contratos Hospitalarios"),
        ("Flaky internet? Broken SMTP? We’ve got auto-retries so you don’t have to watch your queue like a hawk on Red Bull.", "Ofertas laborales directas con sistemas de salud acreditados en Estados Unidos."),
        ("Open & Click Tracking (Legally Not Creepy)", "Salarios Competitivos"),
        ("Want to know who opened what and clicked where? So do we. Welcome to legally acceptable email surveillance.", "Ingresos promedio desde $75,000 hasta $110,000 USD anuales según tu especialidad."),
        ("Markup Freedom (Build It Your Way)", "Bono de Reubicación"),
        ("Whatever you write, we’ll render it without crying over inline styles.", "Asistencia para tiquetes aéreos, alojamiento inicial y trámites de llegada."),
        ("Inbox Previews (For the Control Freak in You)", "Inglés Clínico Especializado"),
        ("Preview your masterpiece before it hits the inbox. Yes, even in Outlook. Especially in Outlook.", "Entrenamiento enfocado en vocabulario médico para certificar TOEFL iBT o IELTS Academic."),
        ("Custom Domains (Stop Using Sketchy Emails)", "Acompañamiento VIP 1 a 1"),
        ("Send from your own domain and stop looking like a scammer. Nobody trusts ‘noreply@fakedomain.biz’.", "Asesoría personalizada en cada etapa del proceso hasta tu incorporación hospitalaria.")
    ]

    rutas_a_escanear = [
        os.path.join(ruta_astro, 'src', 'components'),
        os.path.join(ruta_astro, 'src', 'pages'),
        os.path.join(ruta_astro, 'src', 'content')
    ]

    for carpeta in rutas_a_escanear:
        if not os.path.exists(carpeta):
            continue
        for root, dirs, files in os.walk(carpeta):
            for file in files:
                if file.endswith(('.astro', '.md', '.tsx', '.jsx')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        modificado = False
                        for orig, reemp in reemplazos_directos:
                            if orig in content:
                                content = content.replace(orig, reemp)
                                modificado = True
                        
                        if modificado:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"[Text Injector] Personalizado {file} -> {nicho[:30]}...")
                    except Exception as e:
                        pass


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

    # NUEVO: Procesar e inyectar logo, favicons e imágenes WebP del nicho
    procesar_e_inyectar_media(sitio_id, sitio['ruta_astro'], ruta_base, nombre_proyecto, sitio.get('nicho', 'Enfermera en Estados Unidos'))

    # NUEVO: Personalizar automáticamente textos de componentes de la plantilla en español según el nicho
    personalizar_componentes_plantilla(sitio['ruta_astro'], sitio.get('nicho', 'Enfermera en Estados Unidos'), sitio.get('palabras_clave', []))

    # NUEVO: Gestionar estado
    gestionar_estado_contenido(sitio_id, sitio['ruta_astro'], ruta_base, nombre_proyecto, modo_propagar)

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
        print(f"[*] Generando artículo inicial para {sitio_id}...")
        markdown_ia, slug_generado = generar_contenido_ia(sitio_id, sitio['nicho'], sitio['palabras_clave'], ruta_proyecto_config, modo="articulo")
        
        # PROCESAR IMÁGENES SEO (Incluso en base si hubiera, aunque usualmente no hay en base)
        markdown_ia = procesar_imagenes_seo(sitio_id, sitio['nicho'], markdown_ia, ruta_recursos, sitio['ruta_astro'])
        
        guardar_markdown(sitio['ruta_astro'], markdown_ia, slug_generado, modo="articulo")
    
    # NUEVO: Respaldar estado antes de compilar
    respaldar_estado_contenido(sitio_id, sitio['ruta_astro'], ruta_base, nombre_proyecto)
    
    compilar_y_persistir(sitio_id, sitio['ruta_astro'], ruta_base, nombre_proyecto, sitio.get('nicho', ''))
    return {"id": sitio_id, "dominio": configuracion_actual["dominio"]}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador SEO PBN - Generador de Sitios Espejo")
    parser.add_argument("proyecto", help="Nombre del proyecto (ej: enfermera_en_estados_unidos)")
    parser.add_argument("--propagar", action="store_true", help="Activa el modo propagación de contenido específico")
    parser.add_argument("--modo", choices=["home", "pestaña", "blog"], default="articulo", help="Tipo de contenido a propagar")
    parser.add_argument("--slug", help="Slug para la pestaña o artículo (obligatorio para --modo pestaña)")
    parser.add_argument("--inputfile", help="Archivo .txt con el contenido base o tema a propagar")
    parser.add_argument("--cola", nargs='?', const='ALL', help="Procesa archivos en input_cola/. Especifica un archivo (ej: mi_articulo.json) o deja vacío para listar disponibles.")
    parser.add_argument("--sitio_id", help="Filtra la generación/propagación únicamente para el sitio especificado (ej: money_site)")
    
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
                if args.sitio_id and sitio["id"] != args.sitio_id:
                    continue
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
