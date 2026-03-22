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

## 3. Registrar en el Sistema (ui_components.json)
Para que el sistema "sepa" que existe este nuevo componente, debes agregarlo al registro central de componentes.

- **Ubicación**: `ui_components.json`
- **Sección**: `heroes`, `sections` o `utilities`.

Agrega una entrada como esta:
```json
{
  "id": "ui-mi-componente",
  "prompt": "MI NUEVO COMPONENTE (ui-mi-componente): <div class=\"ui-mi-componente {preset}\">...</div>"
}
```
*Nota: Usa `{preset}` si el componente soporta los presets de color dinámicos.*

## 4. Cómo funciona la Inyección Dinámica
El sistema ya no le da a la IA todas las opciones posibles (lo cual ensucia el prompt). Ahora:
1. El **Orquestador/Generador** elige al azar un Hero y un Preset de `ui_components.json`.
2. Inyecta **solo esa selección** en el prompt de la IA.
3. La IA recibe instrucciones estricatas de usar ese diseño específico.
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
