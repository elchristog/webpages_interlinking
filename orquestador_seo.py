import os
import subprocess
import google.generativeai as genai
from datetime import datetime
import json
import random
from dotenv import load_dotenv
from generador_prompts import generar_prompt_antidetencion, inicializar_prompts
from generador_interlinking import decidir_si_enlazar, obtener_url_objetivo, obtener_anchor_text, inicializar_interlinking
import sys
import urllib.request

load_dotenv()

# Configurar API de Gemini (Vertex AI / AI Studio)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
modelo = genai.GenerativeModel('gemini-2.5-flash')

MONEY_SITE_URL = "https://enfermeraeeu.com"

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

def generar_contenido_ia(sitio_id, nicho, palabras_clave, ruta_proyecto):
    """Llama a Gemini para generar el artículo en formato Markdown."""
    
    poner_enlace = decidir_si_enlazar()
    url_destino = obtener_url_objetivo() if poner_enlace else "N/A"
    anchor = obtener_anchor_text() if poner_enlace else "N/A"

    prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor)
    
    # Generating via AI
    respuesta = modelo.generate_content(prompt)
    
    # We strip any markdown ticks if the agent returned them
    content = respuesta.text
    if content.startswith("```markdown"):
        content = content[11:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
        
    # Logic for YouTube "Trojan Horse" Strategy
    video_distraccion = random.random() <= 0.80
    config_global = cargar_config_global(ruta_proyecto)
    if video_distraccion:
        # 80% of the time append a distraction / official video
        video_url = random.choice(config_global["videos"]["distraccion"])
    else:
        # 20% of the time, append our conversion video
        video_url = random.choice(config_global["videos"]["conversion"])
        
    video_iframe = f"\n\n### Recomendación en Video\n<iframe width='560' height='315' src='{video_url}' frameborder='0' allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture' allowfullscreen></iframe>"
    
    slug_generado = f"{sitio_id}-guia-oficial-{int(datetime.now().timestamp())}"
    frontmatter = f"---\ntitulo: \"{nicho.title()}\"\ndescripcion: \"Descubre todo sobre {nicho}.\"\nslug: \"{slug_generado}\"\nfecha: \"{datetime.now().strftime('%Y-%m-%d')}\"\n---\n\n"
    
    content = frontmatter + content.strip() + video_iframe
        
    return content, slug_generado

def guardar_markdown(ruta_proyecto, contenido_md, slug):
    """Guarda el archivo generado por la IA en la carpeta de contenido de Astro."""
    ruta_dir = os.path.join(ruta_proyecto, 'src', 'content', 'articulos')
    os.makedirs(ruta_dir, exist_ok=True)
    ruta_destino = os.path.join(ruta_dir, f"{slug}.md")
    
    # Crea el archivo físico en tu computadora/servidor
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        f.write(contenido_md)
    print(f"[+] Archivo guardado: {ruta_destino}")

def limpiar_markdowns(ruta_proyecto):
    """Limpia la carpeta de artículos antes de generar para un nuevo sitio"""
    ruta_dir = os.path.join(ruta_proyecto, 'src', 'content', 'articulos')
    if os.path.exists(ruta_dir):
        for f in os.listdir(ruta_dir):
            os.remove(os.path.join(ruta_dir, f))

def escribir_robots_txt(ruta_proyecto, dominio):
    """Genera un archivo robots.txt estático que apunta al Sitemap en turno."""
    ruta_dir = os.path.join(ruta_proyecto, 'public')
    os.makedirs(ruta_dir, exist_ok=True)
    ruta_destino = os.path.join(ruta_dir, 'robots.txt')
    contenido = f"User-agent: *\nAllow: /\nSitemap: {dominio}/sitemap-index.xml\n"
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"[+] Generado robots.txt para: {dominio}")

def ping_sitemap(dominio):
    """Envía silenciosamente la actualización del sitemap a Bing (Google descontinuó este endpoint, pero lee el robots.txt)."""
    sitemap_url = f"{dominio}/sitemap-index.xml"
    ping_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"
    print(f"[*] Haciendo Ping del sitemap a Bing: {ping_url}")
    try:
        urllib.request.urlopen(ping_url, timeout=10)
        print("[+] ¡Ping exitoso! Bing ha sido notificado del nuevo sitemap orgánicamente.")
    except Exception as e:
        print(f"[-] Ocurrió un error (silencioso) enviando el Ping: {e}")

def compilar_y_desplegar(ruta_proyecto, comando_deploy):
    """Ejecuta los comandos de terminal para Astro y Google Cloud."""
    print(f"[*] Compilando Astro en {ruta_proyecto}...")
    
    # 1. Construir el sitio estático (Genera la carpeta /dist)
    subprocess.run("npm run build", cwd=ruta_proyecto, shell=True)
    
    print(f"[*] Desplegando en Google Cloud Platform...")
    
    # 2. Ejecutar el comando de subida (Firebase o App Engine)
    subprocess.run(comando_deploy, cwd=ruta_proyecto, shell=True)
    print("[+] Despliegue completado con éxito.\n")

# ==========================================
# EJECUCIÓN DEL FLUJO MAESTRO
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python orquestador_seo.py <nombre_proyecto>")
        proyectos_dir = os.path.join(os.getcwd(), 'proyectos')
        if os.path.exists(proyectos_dir):
            proyectos = [d for d in os.listdir(proyectos_dir) if os.path.isdir(os.path.join(proyectos_dir, d))]
            print("Proyectos disponibles:")
            for p in proyectos:
                print(f" - {p}")
        else:
            print("No se encontró la carpeta /proyectos/")
        sys.exit(1)
        
    nombre_proyecto = sys.argv[1]
    ruta_proyecto = os.path.join(os.getcwd(), 'proyectos', nombre_proyecto)
    
    if not os.path.exists(ruta_proyecto):
        print(f"Error: El proyecto '{nombre_proyecto}' no existe.")
        sys.exit(1)
        
    print(f"Cargando configuración del proyecto: {nombre_proyecto}...\n")
    print("Iniciando Orquestador de Red PBN...\n")
    
    inicializar_interlinking(ruta_proyecto)
    inicializar_prompts(ruta_proyecto)
    
    config_global = cargar_config_global(ruta_proyecto)
    config_sitios = cargar_config_sitios(ruta_proyecto)
    
    for sitio in config_sitios["sitios_espejo"]:
        sitio_id = sitio['id']
        print(f"=== Procesando {sitio_id} ===")
        
        # 0. Limpiar contenido viejo e inyectar configuracion
        limpiar_markdowns(sitio['ruta_astro'])
        
        configuracion_actual = config_global["sitios"][sitio_id]
        # Adjuntamos el menú global y el dominio
        configuracion_actual["menu_global"] = config_global["menu_global"]
        configuracion_actual["dominio"] = sitio.get("dominio", "http://localhost:4321")
        escribir_config_inyectada(sitio['ruta_astro'], configuracion_actual)
        
        # 1. Crear el contenido
        print("[*] Generando texto con IA...")
        markdown_ia, slug_generado = generar_contenido_ia(sitio_id, sitio['nicho'], sitio['palabras_clave'], ruta_proyecto)
        
        # 2. Guardar en la carpeta del proyecto Astro correspondiente
        guardar_markdown(sitio['ruta_astro'], markdown_ia, slug_generado)
        
        # 3. Preparar robots.txt con el dominio dinámico
        escribir_robots_txt(sitio['ruta_astro'], configuracion_actual['dominio'])
        
        # 4. Compilar a HTML puro y subir a Google Cloud
        compilar_y_desplegar(sitio['ruta_astro'], sitio['comando_deploy'])
        
        # 5. Notificar silenciosamente al crawler de Google
        ping_sitemap(configuracion_actual['dominio'])

    print("¡Todos los sitios espejo han sido actualizados y simulados de desplegar!")
