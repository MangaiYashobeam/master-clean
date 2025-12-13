# 🎓 Presentación de Defensa - BIOTRACK

## Sistema de Análisis Biomecánico de Rangos de Movimiento Articular

**Postulante:** Mariana Zenobia Camacho Orgaz  
**Tutor:** Ing. Elias Prudencio Chavez Jaldin  
**Fecha de Defensa:** 15 de Diciembre, 2025  
**Universidad:** Privada del Valle - Cochabamba, Bolivia

---

## 🚀 Cómo Ejecutar la Presentación

### Opción 1: Servidor Python (Recomendado)

```bash
# Navegar a la carpeta de presentación
cd "c:\Users\mariz\Documents\PROYECTO DE GRADO - BIOMECANICA\SOFTWARE\CLEAN_VERSION_FUNCIONANDO\V10_CLEAN\CLEAN_VERSION_BIOTRACK\presentation"

# Iniciar servidor HTTP
python -m http.server 8080
```

Luego abre en tu navegador: **http://localhost:8080**

### Opción 2: Live Server (VS Code)

1. Instala la extensión "Live Server" en VS Code.
2. Haz clic derecho en `index.html`.
3. Selecciona "Open with Live Server".

### Opción 3: Abrir Directamente

Simplemente abre `index.html` en tu navegador (Chrome, Firefox, Edge).

> ⚠️ **Nota:** Algunas funciones pueden requerir un servidor local para funcionar correctamente.

---

## ⌨️ Controles de la Presentación

| Tecla | Acción |
|-------|--------|
| `→` o `ESPACIO` | Siguiente slide |
| `←` | Slide anterior |
| `↑` / `↓` | Navegar verticalmente |
| `ESC` | Vista general (Overview) |
| `F` | Pantalla completa |
| `S` | Notas del presentador |
| `B` o `.` | Pausar/Pantalla negra |
| `?` | Ayuda de atajos |
| `HOME` | Ir al inicio |
| `END` | Ir al final |

---

## 📁 Estructura de Archivos

```
presentation/
├── index.html              # Presentación principal
├── css/
│   └── biotrack-theme.css  # Tema personalizado
├── images/                 # Imágenes y capturas (placeholders)
└── README.md               # Este archivo
```

---

## 🎨 Personalización

### Cambiar el Tema (Claro/Oscuro)

Si necesitas un fondo claro para mejor visualización en el proyector:

1. Abre `index.html`
2. Busca la línea:
   ```html
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.0.4/dist/theme/black.css">
   ```
3. Cámbiala por:
   ```html
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.0.4/dist/theme/white.css">
   ```

### Agregar Imágenes

Reemplaza los `<div class="image-placeholder">` con tus imágenes reales:

```html
<!-- Antes (placeholder) -->
<div class="image-placeholder">
    <div class="image-placeholder-text">INSERTAR: Captura de pantalla</div>
</div>

<!-- Después (imagen real) -->
<img src="images/tu-imagen.png" alt="Descripción">
```

### Agregar el Video Demo

Busca el `<div class="video-placeholder">` y reemplázalo con:

```html
<video controls width="100%" style="border-radius: 12px;">
    <source src="videos/demo-biotrack.mp4" type="video/mp4">
    Tu navegador no soporta video HTML5.
</video>
```

---

## 📋 Checklist Pre-Defensa

### Contenido
- [ ] Revisar que todos los datos estadísticos sean correctos
- [ ] Verificar ortografía y gramática
- [ ] Confirmar que los objetivos coinciden con las conclusiones

### Imágenes (Reemplazar Placeholders)
- [ ] Logo de la universidad
- [ ] Diagrama de planos anatómicos
- [ ] Skeleton de MediaPipe (33 landmarks)
- [ ] Capturas de la interfaz (Dashboard, Análisis en Vivo)
- [ ] Foto del prototipo de hardware (ESP32 + trípode)
- [ ] Gráficos de resultados (Bland-Altman, Error por articulación)
- [ ] Fotos de las pruebas de campo

### Video
- [ ] Grabar video demo del sistema (30-60 segundos)
- [ ] Preparar backup de demostración en vivo

### Técnico
- [ ] Probar presentación en el proyector del auditorio
- [ ] Verificar que los colores se vean bien
- [ ] Tener backup en USB y nube
- [ ] Probar controles de teclado

---

## ⏱️ Distribución de Tiempo (35 minutos)

| Sección | Tiempo | Slides |
|---------|--------|--------|
| Introducción | 3 min | 3 |
| Planteamiento del Problema | 2 min | 2 |
| Justificación | 2 min | 1 |
| Objetivos | 3 min | 2 |
| Marco Teórico | 3 min | 2 |
| Diagnóstico Situacional | 2 min | 1 |
| **Ingeniería del Proyecto** | **8 min** | **6** |
| **Resultados y Discusión** | **7 min** | **6** |
| Conclusiones y Recomendaciones | 4 min | 3 |
| Demostración | 1 min | 1 |
| **TOTAL** | **35 min** | **27 slides** |

---

## 🛠️ Tecnología Utilizada

- **Reveal.js 5.0.4** - Framework de presentaciones HTML
- **CSS personalizado** - Tema BIOTRACK con colores oscuros y turquesa
- **Highlight.js** - Resaltado de código
- **Fuentes**: Segoe UI, Fira Code (monospace)

---

## 📞 Soporte

Si tienes problemas técnicos con la presentación:

1. Verifica que tengas conexión a internet (CDN de Reveal.js)
2. Prueba en otro navegador (Chrome recomendado)
3. Asegúrate de que JavaScript está habilitado

---

**¡Éxito en tu defensa!** 🎓✨
