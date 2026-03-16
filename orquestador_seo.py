import os
import subprocess
import google.generativeai as genai
from datetime import datetime
import json
import random
import shutil
from dotenv import load_dotenv
from generador_prompts import generar_prompt_antidetencion, inicializar_prompts
from generador_interlinking import decidir_si_enlazar, obtener_url_objetivo, obtener_anchor_text, inicializar_interlinking
import sys
import urllib.request

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

def escribir_config_inyectada(ruta_proyecto, data):
    ruta_data = os.path.join(ruta_proyecto, 'src', 'data')
    os.makedirs(ruta_data, exist_ok=True)
    ruta_destino = os.path.join(ruta_data, 'config_inyectada.json')
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generar_contenido_ia(sitio_id, nicho, palabras_clave, ruta_proyecto, contenido_base=None):
    """Llama a Gemini para generar el artículo en formato Markdown basándose opcionalmente en contenido_base."""
    
    poner_enlace = decidir_si_enlazar()
    url_destino = obtener_url_objetivo() if poner_enlace else "N/A"
    anchor = obtener_anchor_text() if poner_enlace else "N/A"

    if contenido_base:
        mensaje_propago = f"Toma este contenido base y crea una versión única y expandida para el nicho '{nicho}':\n\n{contenido_base}"
        prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor)
        prompt = f"{prompt}\n\n{mensaje_propago}"
    else:
        prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor)
    
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
    
    slug_generado = f"{sitio_id}-guia-oficial-{int(datetime.now().timestamp())}"
    frontmatter = f"---\ntitulo: \"{nicho.title()}\"\ndescripcion: \"Guía definitiva sobre {nicho}.\"\nslug: \"{slug_generado}\"\nfecha: \"{datetime.now().strftime('%Y-%m-%d')}\"\n---\n\n"
    
    content = frontmatter + content.strip() + video_iframe
    return content, slug_generado

def guardar_markdown(ruta_proyecto, contenido_md, slug):
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

def compilar_y_persistir(sitio_id, ruta_proyecto, ruta_base):
    """Construye el sitio y lo mueve a una carpeta persistente para su visualización."""
    os.makedirs(os.path.join(ruta_base, 'sitios_generados'), exist_ok=True)
    ruta_persistente = os.path.join(ruta_base, 'sitios_generados', sitio_id)
    
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

def generar_index_dashboard(ruta_base, sitios):
    """Genera un archivo index.html central para navegar entre los sitios."""
    ruta_dashboard = os.path.join(ruta_base, 'sitios_generados', 'index.html')
    
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PBN Dashboard - Previsualización Local</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-zinc-50 p-8 md:p-20">
    <div class="max-w-6xl mx-auto">
        <header class="mb-12 border-b border-zinc-200 pb-8">
            <h1 class="text-4xl font-extrabold text-black tracking-tight">PBN Dashboard</h1>
            <p class="text-zinc-500 mt-2">Navega y verifica los 16 sitios generados (1 Principal + 15 Espejos).</p>
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
                   <p class="text-xs opacity-70 mt-1 line-clamp-2">{s['dominiio'] if 'dominiio' in s else s.get('dominio', '')}</p>
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python orquestador_seo.py <nombre_proyecto> [contenido_base_archivo]")
        sys.exit(1)
        
    nombre_proyecto = sys.argv[1]
    ruta_base = os.getcwd()
    ruta_proyecto_config = os.path.join(ruta_base, 'proyectos', nombre_proyecto)
    
    contenido_base = None
    if len(sys.argv) > 2:
        if os.path.exists(sys.argv[2]):
            with open(sys.argv[2], 'r', encoding='utf-8') as f:
                contenido_base = f.read()
            print("[*] Contenido base cargado para propagación.")

    inicializar_interlinking(ruta_proyecto_config)
    inicializar_prompts(ruta_proyecto_config)
    
    config_global = cargar_config_global(ruta_proyecto_config)
    config_sitios = cargar_config_sitios(ruta_proyecto_config)
    
    sitios_procesados = []

    for sitio in config_sitios["sitios_espejo"]:
        sitio_id = sitio['id']
        print(f"\n=== Procesando {sitio_id} ===")
        
        # 0. Limpiar y configurar
        limpiar_markdowns(sitio['ruta_astro'])
        
        configuracion_actual = config_global["sitios"][sitio_id].copy()
        configuracion_actual["menu_global"] = config_global["menu_global"]
        configuracion_actual["dominio"] = sitio.get("dominio", "http://localhost:4321")
        
        # Layout diversification
        if "layout" not in configuracion_actual:
            configuracion_actual["layout"] = random.choice(["LayoutA", "LayoutB", "LayoutC"])
        
        escribir_config_inyectada(sitio['ruta_astro'], configuracion_actual)
        
        # 1. Generar Contenido (Propagación si hay contenido_base)
        print(f"[*] Generando versión para {sitio_id}...")
        markdown_ia, slug_generado = generar_contenido_ia(sitio_id, sitio['nicho'], sitio['palabras_clave'], ruta_proyecto_config, contenido_base)
        
        guardar_markdown(sitio['ruta_astro'], markdown_ia, slug_generado)
        
        # 2. Compilar y Persistir localmente
        compilar_y_persistir(sitio_id, sitio['ruta_astro'], ruta_base)
        
        sitios_procesados.append({
            "id": sitio_id,
            "dominio": configuracion_actual["dominio"]
        })

    # 3. Generar Dashboard Final
    generar_index_dashboard(ruta_base, sitios_procesados)
    
    print("\n[!!!] PROCESO COMPLETADO [!!!]")
    print(f"Puedes ver todos los sitios en: file://{os.path.join(ruta_base, 'sitios_generados', 'index.html')}")
