# Guía Técnica: Cómo Agregar Nuevos Elementos al Sistema

Esta guía explica el flujo para expandir la biblioteca de componentes visuales (Heros, Cards, Grids, etc.) y asegurar que el sistema de IA pueda utilizarlos automáticamente.

## 1. Crear el Componente en Astro
Los componentes deben ser "átomos de diseño" que reciban propiedades (props) para ser dinámicos.

- **Ubicación**: `plantilla_astro_maestra/src/components/fundations/containers/`
- **Regla**: Usa etiquetas semánticas y asegúrate de que sea responsive.

Ejemplo `MiNuevoComponente.astro`:
```astro
---
const { titulo, subtitulo, imagen } = Astro.props;
---
<section class="ui-mi-componente">
  <div class="container">
    <h2>{titulo}</h2>
    <p>{subtitulo}</p>
    <img src={imagen} alt={titulo} />
  </div>
</section>
```

## 2. Definir Estilos Globales
Para que los componentes funcionen incluso si la IA genera el HTML puro (sin pasar por el componente Astro directamente), los estilos deben estar en el CSS global.

- **Ubicación**: `plantilla_astro_maestra/src/styles/global.css`
- **Estándar**: Usa Vanilla CSS para evitar dependencias de compilación complejas.

```css
.ui-mi-componente {
  padding: 4rem 2rem;
  background: var(--primary);
  /* ... tus estilos ... */
}
```

## 3. Registrar en el Generador de Prompts
Para que la IA "sepa" que existe este nuevo componente, debes agregarlo a la lista de componentes permitidos.

- **Ubicación**: `generador_prompts.py`
- **Función**: `generar_prompt_antidetencion` -> `REGLAS_COMPONENTES_UI`

Agrega una entrada como esta:
```python
    16. MI NUEVO COMPONENTE (ui-mi-componente): Úsalo para resaltar X cosa.
        Formato: <div class="ui-mi-componente"><h2>Título</h2><p>Texto...</p><img src="URL_IMAGEN" alt="..."></div>
```

## 4. Instrucciones sobre Imágenes
Si tu componente requiere imágenes:
1. Usa el placeholder `URL_IMAGEN` en la definición del prompt.
2. La IA generará el código con el nombre del archivo sugerido.
3. El **Orquestador SEO** se encargará de:
   - Buscar la imagen real en la carpeta de `input_cola/`.
   - Copiarla 16 veces (una por sitio).
   - Renombrarla con palabras clave SEO.
   - Actualizar el HTML generado.

## 5. Verificación
Antes de darlo por terminado:
1. Crea una página de prueba (ej: `src/pages/test-nuevo.astro`).
2. Verifica el diseño en desktop y mobile.
3. Ejecuta una generación pequeña con `--cola` para ver si la IA lo elige correctamente.
