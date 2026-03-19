# Guía: Cómo Generar Contenido en los 16 Sitios

Para facilitar la creación de contenido con alta variación en toda tu red de 16 sitios, hemos implementado un sistema de "Cola de Entrada".

## 1. El Lugar de Entrada (Input)
Crea un archivo `.json` dentro de la carpeta:
`/home/elchristog/webpages_interlinking/proyectos/[nombre_del_proyecto]/input_cola/`

## 2. Formato del Archivo
Puedes nombrar el archivo como quieras (ej. `mi_articulo.json`). El contenido debe seguir este formato:

### Para un Artículo de Blog:
```json
{
  "modo": "blog",
  "tema": "Cómo prepararse para el NCLEX en tiempo record",
  "contenido": "Aquí pones el texto base que quieres que se use para generar las 16 variantes..."
}
```

### Para una Página Nueva (Pestaña):
```json
{
  "modo": "pestaña",
  "slug": "requisitos-licencia-miami",
  "tema": "Requisitos detallados para la licencia en Miami",
  "contenido": "Aquí pones el texto o puntos clave que quieres que se expandan en cada sitio..."
}
```

## 3. Ejecución
Una vez que hayas puesto uno o varios archivos JSON en la carpeta, ejecuta el siguiente comando en tu terminal (con el entorno `venv` activado):

```bash
python orquestador_seo.py enfermera_en_estados_unidos --cola
```

## 4. Resultado
El script hará lo siguiente:
1. Leerá cada archivo JSON de la carpeta `input_cola/`.
2. Para cada petición, generará **16 variantes diferentes** (una para cada sitio en tu red).
3. Usará personas, formatos y nichos locales distintos para asegurar que el contenido cumpla con la `guia.txt`.
4. Guardará los archivos Markdown en las carpetas correspondientes de `plantilla_astro_maestra`.
5. Compilará y actualizará el dashboard de previsualización.

---
**Nota:** El interlinking se mantendrá en una probabilidad del **50%** por cada artículo generado, tal como solicitaste.
