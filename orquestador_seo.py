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
import shutil
import argparse

load_dotenv()

# Configurar API de Gemini (Vertex AI / AI Studio)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
modelo = genai.GenerativeModel('gemini-2.0-flash')

MONEY_SITE_URL = "https://enfermeraeeu.com"

def cargar_config_global(ruta_proyecto):
    with open(os.path.join(ruta_proyecto, 'config_global.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_config_sitios(ruta_proyecto):
    with open(os.path.join(ruta_proyecto, 'config_sitios.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def escribir_config_inyectada(ruta_plantilla, data):
    ruta_data = os.path.join(ruta_plantilla, 'src', 'data')
    os.makedirs(ruta_data, exist_ok=True)
    ruta_destino = os.path.join(ruta_data, 'config_inyectada.json')
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def adaptar_contenido_usuario(contenido_base, nicho, palabras_clave, url_destino, anchor):
    """Usa Gemini para adaptar el contenido del usuario al sitio específico."""
    prompt_maestro = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor)
    
    prompt_adaptacion = f"""
    {prompt_maestro}
    
    CONTENIDO BASE DEL USUARIO PARA ADAPTAR:
    ---
    {contenido_base}
    ---
    
    INSTRUCCIÓN ADICIONAL: Toma el contenido base anterior y reescríbelo completamente usando el PERFIL y FORMATO indicados arriba. Asegúrate de que parezca un artículo único y diferente a cualquier otro, manteniendo el valor informativo del contenido base PERO cumpliendo estrictamente con las REGLAS DE REDACCIÓN y la REGLA DE ENLACE.
    """
    
    respuesta = modelo.generate_content(prompt_adaptacion)
    return respuesta.text

def generar_contenido_ia(sitio_id, nicho, palabras_clave, ruta_proyecto, contenido_usuario=None):
    """Llama a Gemini para generar o adaptar el contenido."""
    
    poner_enlace = decidir_si_enlazar()
    url_destino = obtener_url_objetivo() if poner_enlace else "N/A"
    anchor = obtener_anchor_text() if poner_enlace else "N/A"

    if contenido_usuario:
        content = adaptar_contenido_usuario(contenido_usuario, nicho, palabras_clave, url_destino, anchor)
    else:
        prompt = generar_prompt_antidetencion(nicho, palabras_clave, url_destino, anchor)
        respuesta = modelo.generate_content(prompt)
        content = respuesta.text
    
    # We strip any markdown ticks if the agent returned them
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

def guardar_markdown(ruta_plantilla, contenido_md, slug):
    """Guarda el archivo generado por la IA en la carpeta de contenido de Astro."""
    ruta_dir = os.path.join(ruta_plantilla, 'src', 'content', 'articulos')
    os.makedirs(ruta_dir, exist_ok=True)
    ruta_destino = os.path.join(ruta_dir, f"{slug}.md")
    
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        f.write(contenido_md)
    print(f"[+] Archivo guardado: {ruta_destino}")

def limpiar_markdowns(ruta_plantilla):
    """Limpia la carpeta de artículos de la plantilla."""
    ruta_dir = os.path.join(ruta_plantilla, 'src', 'content', 'articulos')
    if os.path.exists(ruta_dir):
        for f in os.listdir(ruta_dir):
            os.remove(os.path.join(ruta_dir, f))

def escribir_robots_txt(ruta_plantilla, dominio):
    """Genera un archivo robots.txt en public/."""
    ruta_dir = os.path.join(ruta_plantilla, 'public')
    os.makedirs(ruta_dir, exist_ok=True)
    ruta_destino = os.path.join(ruta_dir, 'robots.txt')
    contenido = f"User-agent: *\nAllow: /\nSitemap: {dominio}/sitemap-index.xml\n"
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"[+] Generado robots.txt para: {dominio}")

def ping_sitemap(dominio):
    """Notifica el sitemap a Bing."""
    sitemap_url = f"{dominio}/sitemap-index.xml"
    ping_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"
    print(f"[*] Haciendo Ping del sitemap a Bing: {ping_url}")
    try:
        urllib.request.urlopen(ping_url, timeout=10)
        print("[+] ¡Ping exitoso!")
    except Exception as e:
        print(f"[-] Error en Ping: {e}")

def compilar_y_mover(ruta_plantilla, sitio_id, ruta_salida_base):
    """Compila Astro y mueve el resultado a la subcarpeta del proyecto."""
    print(f"[*] Compilando Astro...")
    
    comando_build = "source ~/.config/nvm/nvm.sh && nvm use 22 && npm run build"
    subprocess.run(comando_build, cwd=ruta_plantilla, shell=True, executable='/bin/bash')
    
    ruta_dist = os.path.join(ruta_plantilla, 'dist')
    ruta_final = os.path.join(ruta_salida_base, 'webs', sitio_id)
    
    if os.path.exists(ruta_final):
        shutil.rmtree(ruta_final)
    os.makedirs(os.path.dirname(ruta_final), exist_ok=True)
    
    shutil.copytree(ruta_dist, ruta_final)
    print(f"[+] Sitio {sitio_id} movido a: {ruta_final}")

def ejecutar_deploy(ruta_final, comando_deploy, gcp_project_id):
    """Ejecuta el comando de despliegue si no es simulado."""
    if "echo 'Simulando" in comando_deploy:
        print(f"[*] {comando_deploy}")
        return

    if gcp_project_id:
        if "firebase deploy" in comando_deploy:
            comando_deploy = f"{comando_deploy} --project {gcp_project_id}"
        elif "gcloud app deploy" in comando_deploy:
            comando_deploy = f"{comando_deploy} --project {gcp_project_id}"
    
    print(f"[*] Ejecutando despliegue real en {ruta_final}...")
    subprocess.run(comando_deploy, cwd=ruta_final, shell=True)

def escribir_home_content(ruta_plantilla, titulo, cuerpo, active=True):
    """Escribe el contenido personalizado para la Home en src/data/home_content.json."""
    ruta_data = os.path.join(ruta_plantilla, 'src', 'data')
    os.makedirs(ruta_data, exist_ok=True)
    ruta_destino = os.path.join(ruta_data, 'home_content.json')
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        json.dump({"active": active, "titulo": titulo, "cuerpo": cuerpo}, f, ensure_ascii=False, indent=2)
    print(f"[*] Home page configurada como {'ACTIVA' if active else 'INACTIVA'}")

def limpiar_home_content(ruta_plantilla):
    """Desactiva el contenido personalizado de la Home."""
    escribir_home_content(ruta_plantilla, "", "", active=False)

def generar_variaciones_menu(menu_global, nicho, sitio_id):
    """Usa Gemini para generar variaciones semánticas del menú para cada sitio."""
    if sitio_id == "master_money_site":
        return menu_global # El money site mantiene el menú original
    
    prompt = f"""
    Eres un experto en SEO y Link Building. Tengo este menú de navegación global:
    {json.dumps(menu_global, ensure_ascii=False)}
    
    Necesito que generes una versión de estas etiquetas de menú para un sitio web específico cuyo nicho es: "{nicho}" e ID: "{sitio_id}".
    
    REGLAS:
    1. Mantén la misma cantidad de elementos y las mismas rutas.
    2. Cambia los NOMBRES por variaciones semánticas que incluyan palabras clave naturales pero que no sean idénticas a la versión original.
    3. El tono debe ser profesional y coherente con el nicho.
    4. Devuelve ÚNICAMENTE un objeto JSON con el formato: {{"menu_variado": [{{ "nombre": "...", "ruta": "..." }}, ...]}}
    """
    
    try:
        respuesta = modelo.generate_content(prompt)
        content = respuesta.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        return data["menu_variado"]
    except Exception as e:
        print(f"[-] Error generando variaciones de menú para {sitio_id}: {e}. Usando menú global.")
        return menu_global

# ==========================================
# EJECUCIÓN DEL FLUJO MAESTRO
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador SEO Multi-Sitio")
    parser.add_argument("proyecto", help="Nombre del proyecto en /proyectos/")
    parser.add_argument("--contenido", help="Ruta a un archivo .txt con el contenido base a propagar", default=None)
    parser.add_argument("--tipo", help="Tipo de contenido: 'blog' o 'home'", choices=['blog', 'home'], default='blog')
    
    args = parser.parse_args()
    nombre_proyecto = args.proyecto
    tipo_contenido = args.tipo
    ruta_proyecto = os.path.join(os.getcwd(), 'proyectos', nombre_proyecto)
    
    if not os.path.exists(ruta_proyecto):
        print(f"Error: El proyecto '{nombre_proyecto}' no existe.")
        sys.exit(1)
        
    contenido_usuario = None
    if args.contenido:
        if os.path.exists(args.contenido):
            with open(args.contenido, 'r', encoding='utf-8') as f:
                contenido_usuario = f.read()
            print(f"[!] Usando contenido de usuario desde: {args.contenido} (Tipo: {tipo_contenido})")
        else:
            print(f"Error: El archivo de contenido '{args.contenido}' no existe.")
            sys.exit(1)

    print(f"Cargando configuración del proyecto: {nombre_proyecto}...\n")
    
    inicializar_interlinking(ruta_proyecto)
    inicializar_prompts(ruta_proyecto)
    
    config_global = cargar_config_global(ruta_proyecto)
    config_sitios = cargar_config_sitios(ruta_proyecto)
    
    # La plantilla es compartida
    ruta_plantilla = os.path.join(os.getcwd(), 'plantilla_astro_maestra')

    # 0. Definir lista de sitios a procesar (Money Site primero si existe)
    sitios_a_procesar = []
    if "money_site" in config_sitios:
        # Marcamos que es el money site
        config_ms = config_sitios["money_site"]
        config_ms["is_money_site"] = True
        sitios_a_procesar.append(config_ms)
    
    for s_esp in config_sitios.get("sitios_espejo", []):
        s_esp["is_money_site"] = False
        sitios_a_procesar.append(s_esp)

    for sitio in sitios_a_procesar:
        sitio_id = sitio['id']
        es_money_site = sitio.get("is_money_site", False)
        
        print(f"\n=== PROCESANDO SITIO: {sitio_id} {'[MONEY SITE]' if es_money_site else ''} ===")
        
        # 0. Limpiar contenido viejo de la plantilla y preparar config
        limpiar_markdowns(ruta_plantilla)
        limpiar_home_content(ruta_plantilla)
        
        configuracion_actual = config_global["sitios"][sitio_id]
        
        # Generar variaciones de menú para este sitio
        print("[*] Generando variaciones de menú (SEO)...")
        menu_variado = generar_variaciones_menu(config_global["menu_global"], sitio['nicho'], sitio_id)
        configuracion_actual["menu_global"] = menu_variado
        
        configuracion_actual["dominio"] = sitio.get("dominio", "http://localhost:4321")
        
        escribir_config_inyectada(ruta_plantilla, configuracion_actual)
        
        # 1. Crear el contenido (IA o Adaptación)
        print("[*] Generando/Adaptando texto con IA...")
        
        # Para el Money Site, si hay contenido de usuario, lo usamos literalmente o con poca variación
        if es_money_site and contenido_usuario:
            # CMS: Literal o adaptado levemente para quitar rastro de PBN
            print("[*] Money Site: Usando contenido original.")
            markdown_ia = contenido_usuario # Podemos mejorar esto en el futuro
            slug_generado = "inicio"
        else:
            markdown_ia, slug_generado = generar_contenido_ia(sitio_id, sitio['nicho'], sitio['palabras_clave'], ruta_proyecto, contenido_usuario)
        
        # 2. Guardar en la plantilla según el TIPO
        if tipo_contenido == 'home':
            # Extraemos el título del markdown si existe o usamos el nicho
            titulo_home = sitio['nicho'].title()
            cuerpo_home = markdown_ia
            # Si tiene frontmatter, lo limpiamos para la Home
            if "---" in cuerpo_home:
                partes = cuerpo_home.split("---")
                if len(partes) >= 3:
                   cuerpo_home = "---".join(partes[2:]).strip()
            
            escribir_home_content(ruta_plantilla, titulo_home, cuerpo_home)
        else:
            # Guardamos como Blog Post
            guardar_markdown(ruta_plantilla, markdown_ia, slug_generado)
        
        # 3. Robots.txt
        escribir_robots_txt(ruta_plantilla, configuracion_actual['dominio'])
        
        # 4. Compilar y mover a la carpeta del proyecto
        compilar_y_mover(ruta_plantilla, sitio_id, ruta_proyecto)
        
        # 5. Deploy (Simulado o real desde la carpeta de salida)
        ejecutar_deploy(os.path.join(ruta_proyecto, 'webs', sitio_id), sitio['comando_deploy'], configuracion_actual.get('gcp_project_id'))
        
        # 6. Ping (opcional, solo si es real)
        if "echo 'Simulando" not in sitio['comando_deploy']:
            ping_sitemap(configuracion_actual['dominio'])

    print("\n[FIN] Todas las webs (incluyendo Principal y Espejos) han sido generadas.")
    print(f"Puedes verlas usando: python visor_webs.py {ruta_proyecto}/webs")
