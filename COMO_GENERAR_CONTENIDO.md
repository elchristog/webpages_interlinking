# Guía: Cómo Generar Contenido en los 16 Sitios

Para facilitar la creación de contenido con alta variación y optimización SEO en toda tu red de 16 sitios, usamos un sistema de "Cola de Entrada" inteligente.

## 1. El Lugar de Entrada (Input)
Crea una carpeta o un archivo `.json` dentro de la carpeta:
`/home/elchristog/webpages_interlinking/proyectos/[nombre_del_proyecto]/input_cola/`

### Recomendación: Estructura de Carpeta (Para Imágenes SEO)
Si tu página lleva imágenes (Hero, Galería, etc.), lo ideal es crear una carpeta por cada página:
```
input_cola/
  └── mi-nueva-pagina/
      ├── contenido.json    (El JSON con el texto/instrucciones)
      ├── hero-principal.jpg (La imagen que quieres usar)
      └── captura-datos.png  (Otra imagen secundaria)
```

## 2. Gestión de Imágenes y SEO Automático
El sistema está diseñado para que **no tengas que renombrar imágenes manualmente** para cada uno de los 16 sitios:

1. **Placeholders**: En tu JSON o en el prompt, usa el nombre del archivo original (ej: `hero-principal.jpg`).
2. **Reemplazo Único**: Pon la imagen real UNA SOLA VEZ dentro de la carpeta de la página en `input_cola/`.
3. **Propagación SEO**: Al ejecutar el orquestador, el sistema:
   - Detecta la imagen en el contenido generado.
   - Crea **16 copias únicas** (una por sitio).
   - **Renombra** cada copia usando las palabras clave específicas de cada sitio (ej: `enfermeras-florida-preparacion-hero-principal.jpg`).
   - Actualiza el código de cada sitio para que apunte a su imagen optimizada.

## 3. Formato del Archivo JSON
El contenido debe seguir este formato básico:

```json
{
  "modo": "pestaña",
  "slug": "requisitos-licencia",
  "tema": "Requisitos detallados para la licencia en USA",
  "contenido": "Texto base..."
}
```

## 4. Ejecución
Ejecuta el orquestador especificando el nombre de la carpeta:

```bash
python orquestador_seo.py enfermera_en_estados_unidos --cola mi-nueva-pagina
```

## 5. Resultado
El script generará las 16 variantes, procesará las imágenes para SEO, compilará los sitios y actualizará el dashboard.

---
**Nota:** El interlinking se mantiene con la probabilidad configurada en `config_logic.json`.
