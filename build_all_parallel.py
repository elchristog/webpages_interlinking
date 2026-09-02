#!/usr/bin/env python3
"""
Script de construcción rápida y en paralelo para los 16 sitios Astro PBN.
Aprovecha todos los núcleos del procesador disponibles.
"""
import os
import sys
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITIOS_DIR = os.path.join(BASE_DIR, "sitios_astro")

def construir_sitio(sitio):
    ruta_sitio = os.path.join(SITIOS_DIR, sitio)
    start_time = time.time()
    
    # Ejecutamos 'npm run build' directamente para evitar el overhead de 'npx'
    res = subprocess.run(
        ["npm", "run", "build"],
        cwd=ruta_sitio,
        capture_output=True,
        text=True
    )
    
    elapsed = time.time() - start_time
    if res.returncode == 0:
        return sitio, True, f"{elapsed:.1f}s", ""
    else:
        # Extraemos líneas de error principales
        err_lines = [
            l for l in res.stderr.splitlines() 
            if any(k in l for k in ["Error", "ERROR", "failed", "Expected", "Invalid", "Rollup"])
        ]
        err_summary = " | ".join(err_lines[:2]) if err_lines else res.stderr[-200:]
        return sitio, False, f"{elapsed:.1f}s", err_summary

def main():
    if not os.path.exists(SITIOS_DIR):
        print(f"❌ Error: El directorio {SITIOS_DIR} no existe.")
        sys.exit(1)
        
    sitios = sorted([
        d for d in os.listdir(SITIOS_DIR) 
        if os.path.isdir(os.path.join(SITIOS_DIR, d))
    ])
    
    num_cpus = os.cpu_count() or 4
    # Dejamos un margen razonable de workers según los núcleos disponibles
    max_workers = min(len(sitios), num_cpus)
    
    print(f"🚀 Iniciando compilación paralela para {len(sitios)} sitios PBN utilizando {max_workers} procesos simultáneos...\n")
    start_all = time.time()
    
    exitosos = 0
    fallidos = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_sitio = {executor.submit(construir_sitio, s): s for s in sitios}
        
        for future in as_completed(future_to_sitio):
            sitio, ok, tiempo, err = future.result()
            if ok:
                exitosos += 1
                print(f" ✅ [{exitosos + fallidos}/{len(sitios)}] {sitio:<25} -> ÉXITO ({tiempo})")
            else:
                fallidos += 1
                print(f" ❌ [{exitosos + fallidos}/{len(sitios)}] {sitio:<25} -> FALLÓ ({tiempo}) | {err}")
                
    total_time = time.time() - start_all
    print(f"\n==========================================")
    print(f"📊 RESUMEN DE CONSTRUCCIÓN PARALELA")
    print(f"==========================================")
    print(f"✨ Éxitos: {exitosos} / {len(sitios)}")
    print(f"⚠️  Fallos:  {fallidos} / {len(sitios)}")
    print(f"⏱️  Tiempo Total: {total_time:.1f} segundos ({total_time/60:.2f} minutos)")
    print(f"==========================================\n")

if __name__ == "__main__":
    main()
