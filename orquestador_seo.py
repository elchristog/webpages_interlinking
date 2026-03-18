import os
import subprocess
import google.generativeai as genai
from datetime import datetime
import json
import random
import shutil
from dotenv import load_dotenv
from generador_prompts import generar_prompt_antidetencion, inicializar_prompts
from generador_interlinking import decidir_si_enlazar, obtener_url_objetivo, obtener_anchor_text, inicializar_interlinking, obtener_enlace_autoridad
import sys
import argparse
import urllib.request
import colorsys
import time

load_dotenv()

# Configurar API de Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
modelo = genai.GenerativeModel('gemini-2.5-flash')

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

def generar_paleta_aleatoria():
    """Genera una paleta de colores que cumpla con WCAG AA (4.5:1) contra blanco."""
    h = random.randint(0, 360)
    s = random.randint(50, 95)
    
    # Buscamos una luminosidad (l) que pase el contraste 4.5:1 contra blanco
    # Generalmente l <= 50-60% dependiendo del hue.
    def ajustar_por_accesibilidad(hue, sat):
        l_test = 50 # Empezamos en un punto medio
        intentos = 0
        while intentos < 50:
            lum = hsl_to_relative_luminance(hue, sat, l_test)
            ratio = calcular_contraste_contra_blanco(lum)
            if ratio >= 4.55: # Sutil margen sobre 4.5
                return l_test, ratio
            l_test -= 2 # Oscurecer
            if l_test < 10: break
            intentos += 1
        return 15, 7.0 # Fallback seguro muy oscuro

    l_prim, ratio_prim = ajustar_por_accesibilidad(h, s)
    
    # Variaciones para acento (complementario o rotado)
    h_acc = (h + random.randint(120, 240)) % 360
    l_acc, ratio_acc = ajustar_por_accesibilidad(h_acc, s)

    # Secundario: Un tono análogo o monocromático que también sea accesible
    h_sec = (h + 30) % 360 # Tono análogo
    l_sec, ratio_sec = ajustar_por_accesibilidad(h_sec, s - 20) # Menos saturado para ser "más suave"

    return {
        "primary": f"hsl({h}, {s}%, {l_prim}%)",
        "secondary": f"hsl({h_sec}, {max(0, s-20)}%, {l_sec}%)",
        "accent": f"hsl({h_acc}, {s}%, {l_acc}%)",
        "text_bold": f"hsl({h}, {s}%, 15%)", # Siempre oscuro para máxima legibilidad
        "meta": {
            "primary_contrast": f"{ratio_prim:.2f}",
            "secondary_contrast": f"{ratio_sec:.2f}",
            "accent_contrast": f"{ratio_acc:.2f}"
        }
    }

def limpiar_indices(ruta_proyecto):
    ruta_index = os.path.join(ruta_proyecto, 'src', 'content', 'index.md')
    if os.path.exists(ruta_index):
        os.remove(ruta_index)
        print(f"[*] Index anterior eliminado en {ruta_proyecto}")

def generar_contenido_ia(sitio_id, nicho, palabras_clave, ruta_proyecto, modo="articulo", contenido_base=None, slug_override=None, nombre_sitio="este sitio"):
    """Llama a Gemini para generar el artículo o la home en formato Markdown."""
    
    poner_enlace = decidir_si_enlazar()
    url_destino = obtener_url_objetivo() if poner_enlace else "N/A"
    anchor = obtener_anchor_text() if poner_enlace else "N/A"

    url_outbound = obtener_enlace_autoridad()
    prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor, url_outbound=url_outbound, modo=modo, contenido_base=contenido_base, nombre_sitio=nombre_sitio)
    
    respuesta = modelo.generate_content(prompt)
    content = respuesta.text
    if content.startswith("```markdown"):
        content = content[11:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
        
    config_global = cargar_config_global(ruta_proyecto)
    # YouTube Strategy
    video_distraccion = random.random() <= 0.80
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
    
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        f.write(contenido_md)
    print(f"[+] Archivo guardado: {ruta_destino}")

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
        shutil.rmtree(ruta_persistente)
    
    if os.path.exists(dist_path):
        shutil.copytree(dist_path, ruta_persistente)
        post_procesar_rutas_locales(ruta_persistente)
        print(f"[+] Sitio {sitio_id} persistido y post-procesado en: {ruta_persistente}")
    else:
        print(f"[-] Error: No se encontró la carpeta /dist tras la compilación en {ruta_proyecto}")

def generar_index_dashboard(ruta_base, sitios, nombre_proyecto):
    """Genera un archivo index.html central para navegar entre los sitios del proyecto."""
    ruta_dashboard = os.path.join(ruta_base, 'sitios_generados', nombre_proyecto, 'index.html')
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PBN Dashboard - Previsualización Local</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-zinc-50 p-8 md:p-20">
    <div class="max-w-6xl mx-auto">
        <header class="mb-12 border-b border-zinc-200 pb-8">
            <h1 class="text-4xl font-extrabold text-black tracking-tight">PBN Dashboard: {nombre_proyecto.replace('_', ' ').title()}</h1>
            <p class="text-zinc-500 mt-2">Navega y verifica los sitios generados para este proyecto.</p>
        </header>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    """
    
    for s in sitios:
        estilo = "bg-black text-white" if s['id'] == 'money_site' else "bg-white text-black outline outline-zinc-200"
        badge = "<span class='text-[10px] uppercase font-bold bg-blue-600 text-white px-2 py-0.5 rounded ml-2'>Main</span>" if s['id'] == 'money_site' else ""
        
        html += f"""
            <a href="./{s['id']}/index.html" target="_blank" class="{estilo} p-6 h-40 flex flex-col justify-between hover:scale-105 transition-transform shadow-sm">
                <div>
                   <h2 class="font-bold text-lg">{s['id'].replace('_', ' ').title()}{badge}</h2>
                   <p class="text-xs opacity-70 mt-1 line-clamp-2">{s.get('dominio', '')}</p>
                </div>
                <span class="text-xs font-mono">Abrir sitio →</span>
            </a>
        """
        
    html += """
        </div>
        <footer class="mt-20 text-center text-zinc-400 text-xs">
            Orquestador SEO PBN - Generado el """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """
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
        configuracion_actual["layout"] = random.choice(["LayoutA", "LayoutB", "LayoutC", "LayoutD", "LayoutE", "LayoutF", "LayoutG"])
        cambio_detectado = True
    
    if "nav_footer_version" not in configuracion_actual:
        configuracion_actual["nav_footer_version"] = random.choice(["v1", "v2", "v3"])
        cambio_detectado = True

    if "font_family" not in configuracion_actual:
        configuracion_actual["font_family"] = random.choice(["Inter", "Roboto", "Outfit", "Plus Jakarta Sans"])
        cambio_detectado = True
    
    if configuracion_actual.get("layout") == "LayoutB" and "sidebar_pos" not in configuracion_actual:
        configuracion_actual["sidebar_pos"] = random.choice(["left", "right"])
        cambio_detectado = True

    if "color_palette" not in configuracion_actual or "meta" not in configuracion_actual["color_palette"]:
        configuracion_actual["color_palette"] = generar_paleta_aleatoria()
        cambio_detectado = True
    
    if cambio_detectado:
        config_global["sitios"][sitio_id] = configuracion_actual
        guardar_config_global(ruta_proyecto_config, config_global)
        print(f"[!] Identidad persistida para {sitio_id}")
    
    return configuracion_actual

def procesar_sitio(sitio, config_global, config_menus, ruta_proyecto_config, ruta_base, nombre_proyecto, modo_propagar=None, input_base=None, slug_pestaña=None):
    sitio_id = sitio['id']
    print(f"\n=== Procesando {sitio_id} ===")
    
    # Limpiar dist para evitar rastro de otros sitios
    dist_path = os.path.join(sitio['ruta_astro'], 'dist')
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    
    configuracion_actual = config_global["sitios"][sitio_id].copy()
    configuracion_actual["dominio"] = sitio.get("dominio", "http://localhost:4321")
    
    configuracion_actual = preparar_identidad_sitio(sitio_id, configuracion_actual, config_global, config_menus, ruta_proyecto_config)
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
            nombre_sitio=configuracion_actual["nombre_sitio"]
        )
        guardar_markdown(sitio['ruta_astro'], contenido_ia, slug_final, modo=modo_propagar)
    else:
        # Modo generación base/bulk
        limpiar_markdowns(sitio['ruta_astro'])
        limpiar_indices(sitio['ruta_astro'])
        
        print(f"[*] Generando artículo inicial para {sitio_id}...")
        markdown_ia, slug_generado = generar_contenido_ia(sitio_id, sitio['nicho'], sitio['palabras_clave'], ruta_proyecto_config, modo="articulo")
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
    parser.add_argument("--cola", action="store_true", help="Procesa los archivos en input_cola/")
    
    args = parser.parse_args()
    
    nombre_proyecto = args.proyecto
    ruta_base = os.getcwd()
    ruta_proyecto_config = os.path.join(ruta_base, 'proyectos', nombre_proyecto)
    
    if not os.path.exists(ruta_proyecto_config):
        print(f"[-] Error: No existe la carpeta del proyecto en {ruta_proyecto_config}")
        sys.exit(1)

    peticiones = []
    
    if args.cola:
        ruta_cola = os.path.join(ruta_base, 'input_cola')
        if os.path.exists(ruta_cola):
            for f in os.listdir(ruta_cola):
                if f.endswith(".json"):
                    with open(os.path.join(ruta_cola, f), 'r', encoding='utf-8') as jf:
                        peticiones.append(json.load(jf))
            if not peticiones:
                print("[*] La cola está vacía.")
        else:
            print("[-] Error: No existe la carpeta input_cola/")
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
        for p in peticiones:
            print(f"\n[*] Procesando petición: {p.get('tema', p.get('slug', 'sin nombre'))}")
            modo_ejecucion = p.get("modo", "articulo")
            input_text = p.get("contenido") or p.get("tema") or p.get("input_base") or p.get("contenido_base")
            slug_pestaña = p.get("slug")
            
            sitios_procesados = []
            for sitio in config_sitios["sitios_espejo"]:
                resultado = procesar_sitio(
                    sitio, config_global, config_menus, 
                    ruta_proyecto_config, ruta_base, nombre_proyecto,
                    modo_propagar=modo_ejecucion,
                    input_base=input_text,
                    slug_pestaña=slug_pestaña
                )
                sitios_procesados.append(resultado)
            generar_index_dashboard(ruta_base, sitios_procesados, nombre_proyecto)

    print("\n[!!!] PROCESO COMPLETADO [!!!]")
    print(f"Dashboard: file://{os.path.join(ruta_base, 'sitios_generados', nombre_proyecto, 'index.html')}")
