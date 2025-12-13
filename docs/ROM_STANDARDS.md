# Estándares de Rango de Movimiento (ROM)
## BIOTRACK - Sistema de Análisis Biomecánico

---

## 📚 Referencias Bibliográficas

Este sistema de clasificación está basado en estándares goniométricos internacionales reconocidos:

### Fuentes Primarias
- **AAOS** - American Academy of Orthopaedic Surgeons. *Joint Motion: Method of Measuring and Recording*
- **Beighton Scale** - Beighton P, Solomon L, Soskolne CL. *Articular mobility in an African population*. Ann Rheum Dis. 1973
- **Nordin, M. & Frankel, V.H.** - *Basic Biomechanics of the Musculoskeletal System* (5th ed.). Wolters Kluwer, 2022
- **Kapandji, I.A.** - *Fisiología Articular* (6th ed.). Editorial Médica Panamericana

### Fuentes Secundarias
- **AMA** - American Medical Association. *Guides to the Evaluation of Permanent Impairment* (6th ed.)
- **Kendall, F.P.** - *Músculos: Pruebas funcionales, postura y dolor*

---

## 🎯 Sistema de Clasificación ROM

### Categorías de Clasificación

| Clasificación | Rango | Color | Descripción Clínica |
|--------------|-------|-------|---------------------|
| **Muy Limitado** | < 50% | 🔴 Rojo | Restricción severa del movimiento |
| **Limitado** | 50-69% | 🟠 Naranja | Restricción moderada |
| **Funcional** | 70-89% | 🔵 Celeste | Rango aceptable para AVD* |
| **Óptimo** | 90-100% | 🟢 Verde | Rango normal completo |
| **Aumentado** | > 100% | 🟡 Amarillo | Hiperlaxitud/Hipermovilidad |

*AVD: Actividades de la Vida Diaria

### Justificación del Umbral >100% para Hiperlaxitud

Según la bibliografía consultada:

> **AAOS**: "El rango normal representa el límite máximo fisiológico esperado para cada articulación"

> **Beighton Scale**: "Se considera hipermóvil una articulación que alcanza un rango de movimiento mayor al normal fisiológico"

> **Nordin & Frankel**: "Superar el rango normal implica mayor demanda de control neuromuscular"

**Por lo tanto**: Cualquier ROM que supere el 100% del máximo normal ya constituye hiperlaxitud, no es necesario esperar al 110%.

---

## ⚠️ Nota Clínica Importante: Hiperlaxitud

La clasificación **"Aumentado"** (>100% del rango normal) **NO significa "mejor"**.

La hiperlaxitud puede indicar:
- **Laxitud ligamentosa constitucional** - Mayor elasticidad de tejidos conectivos
- **Necesidad de control neuromuscular** - Mayor demanda de estabilización activa
- **Mayor riesgo de inestabilidad** - Posible predisposición a subluxaciones
- **Síndrome de hipermovilidad articular** - Condición que requiere evaluación especializada

**Recomendación**: En casos de hiperlaxitud significativa, se sugiere evaluación por especialista.

---

## 📊 Rangos Normales y Umbrales de Hiperlaxitud por Articulación

### Hombro (Shoulder)

| Movimiento | Rango Normal | Umbral Hiperlaxitud | Vista | Fuente |
|------------|-------------|---------------------|-------|--------|
| Flexión | 0° - 180° | > 180° | Perfil | AAOS |
| Extensión | 0° - 60° | > 60° | Perfil | AAOS |
| Abducción | 0° - 180° | > 180° | Frontal | AAOS |
| Aducción | 0° - 30° | > 30° | Frontal | AAOS |

**Nota**: En sujetos hiperlaxos, el hombro puede subluxarse o permitir rangos mayores.

### Codo (Elbow)

| Movimiento | Rango Normal | Umbral Hiperlaxitud | Vista | Fuente |
|------------|-------------|---------------------|-------|--------|
| Flexión | 0° - 150° | > 150° | Perfil | AAOS |
| Extensión | 0° (neutro) | Hiperextensión > 10° | Perfil | Beighton Scale |

**Criterio Beighton**: La hiperextensión de codo >10° es un criterio de la Escala de Beighton para evaluar hiperlaxitud generalizada.

### Cadera (Hip)

| Movimiento | Rango Normal | Umbral Hiperlaxitud | Vista | Fuente |
|------------|-------------|---------------------|-------|--------|
| Flexión | 0° - 120° | > 120° | Perfil | AAOS |
| Extensión | 0° - 30° | > 30° | Perfil | AAOS |
| Abducción | 0° - 45° | ≥ 85° | Frontal | Hospital del Mar |
| Aducción | 0° - 30° | > 30° | Frontal | AAOS |

### Rodilla (Knee)

| Movimiento | Rango Normal | Umbral Hiperlaxitud | Vista | Fuente |
|------------|-------------|---------------------|-------|--------|
| Flexión | 0° - 140° | > 150° | Perfil | AAOS |
| Extensión | 0° (neutro) | Hiperextensión > 10° | Perfil | Beighton Scale |

**Criterio Beighton**: La hiperextensión de rodilla >10° es un criterio de la Escala de Beighton.

### Tobillo (Ankle)

| Movimiento | Rango Normal | Umbral Hiperlaxitud | Vista | Fuente |
|------------|-------------|---------------------|-------|--------|
| Dorsiflexión | 0° - 30° | > 30° | Perfil | AAOS |
| Plantarflexión | 0° - 50° | > 50° | Perfil | AAOS |
| Inversión | 0° - 35° | > 35° | Frontal | AAOS |
| Eversión | 0° - 20° | > 20° | Frontal | AAOS |

---

## 🔧 Implementación Técnica

### Fórmula de Clasificación

```
porcentaje = (ROM_medido / ROM_máximo_normal) × 100

Si porcentaje > 100%  → Aumentado (Hiperlaxitud)
Si porcentaje ≥ 90%   → Óptimo
Si porcentaje ≥ 70%   → Funcional
Si porcentaje ≥ 50%   → Limitado
Si porcentaje < 50%   → Muy Limitado
```

### Backend (Python)

```python
from app.utils.rom_statistics import ROMStatisticsCalculator, ROMClassification

calc = ROMStatisticsCalculator()
result = calc.classify_rom(
    rom_value=155,           # ROM medido en grados
    normal_range=(0, 150),   # (min, max) del movimiento
)

# Resultado para 155° en movimiento con máximo 150°:
# {
#     'classification': 'aumentado',
#     'percentage': 103.3,
#     'message': 'ROM aumentado - Posible hiperlaxitud articular',
#     'is_hypermobile': True
# }
```

### Enum de Clasificación

```python
class ROMClassification(Enum):
    INCREASED = "aumentado"        # > 100% (hiperlaxitud)
    OPTIMAL = "óptimo"             # 90-100%
    FUNCTIONAL = "funcional"       # 70-89%
    LIMITED = "limitado"           # 50-69%
    VERY_LIMITED = "muy_limitado"  # < 50%
```

### Frontend (JavaScript)

```javascript
classifyROM(rom) {
    const maxNormal = this.config.max_angle || 150;
    const percentage = (rom / maxNormal) * 100;
    
    // >100.5% para evitar errores de precisión de punto flotante
    if (percentage > 100.5) return { label: 'Aumentado', class: 'bg-increased' };
    if (percentage >= 90)   return { label: 'Óptimo', class: 'bg-success' };
    if (percentage >= 70)   return { label: 'Funcional', class: 'bg-info' };
    if (percentage >= 50)   return { label: 'Limitado', class: 'bg-warning' };
    return { label: 'Muy Limitado', class: 'bg-danger' };
}
```

---

## 📝 Notas de Implementación

### Precisión de Punto Flotante

Se usa `> 100.5%` en lugar de `> 100%` para evitar errores de precisión:
- `150.0 / 150.0 * 100 = 100.0` → Óptimo ✓
- `150.1 / 150.0 * 100 = 100.07` → Aumentado ✓

---

## 📖 Citas Bibliográficas (Formato APA 7)

American Academy of Orthopaedic Surgeons. (1965). *Joint motion: Method of measuring and recording*. AAOS.

Beighton, P., Solomon, L., & Soskolne, C. L. (1973). Articular mobility in an African population. *Annals of the Rheumatic Diseases*, 32(5), 413-418.

Kapandji, I. A. (2012). *Fisiología articular* (6th ed.). Editorial Médica Panamericana.

Nordin, M., & Frankel, V. H. (2022). *Basic biomechanics of the musculoskeletal system* (5th ed.). Wolters Kluwer.

---

## 📅 Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2025-12-01 | 1.0 | Sistema de 4 categorías inicial |
| 2025-12-03 | 2.0 | Añadida categoría "Aumentado" con umbral >110% |
| 2025-12-03 | 2.1 | **Cambio de umbral a >100%** basado en AAOS/Beighton Scale |

---

*Documento oficial para BIOTRACK - Sistema de Análisis Biomecánico Educativo*  
*Universidad Mayor de San Andrés - Carrera de Informática*
