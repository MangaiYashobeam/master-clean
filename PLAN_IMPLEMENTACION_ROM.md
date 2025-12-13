# 📋 PLAN DE IMPLEMENTACIÓN - Sistema de Análisis ROM Preciso

**Fecha de creación**: 26 de Noviembre, 2025  
**Versión**: V10_CLEAN  
**Estado**: En progreso - Fase 0

---

## 🎯 OBJETIVO GENERAL

Implementar un sistema de análisis ROM (Rango de Movimiento) preciso, validable con goniómetro, con:
- Flujo controlado por estados
- Detección automática de meseta
- Percentil 95 para ROM máximo
- Instrucciones de voz (TTS)
- Escalable a todos los segmentos corporales

---

## 📊 FLUJO DE ANÁLISIS OBJETIVO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE ANÁLISIS ROM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 🔘 USUARIO PRESIONA "INICIAR"                                       │
│     └──► Estado: DETECTING_PERSON                                       │
│                                                                         │
│  2. 👤 DETECCIÓN DE PERSONA (máx 10s timeout)                           │
│     ├── ❌ No detecta → "No se detecta persona"                         │
│     └── ✅ Detecta → Estado: CHECKING_ORIENTATION                       │
│                                                                         │
│  3. 📐 VERIFICACIÓN DE ORIENTACIÓN (máx 5s timeout)                     │
│     ├── Perfil requerido → Verificar que esté de lado                   │
│     ├── Frontal requerido → Verificar que esté de frente                │
│     └── ✅ Correcto → Estado: CHECKING_POSTURE                          │
│                                                                         │
│  4. ✋ VERIFICACIÓN DE POSTURA (máx 5s timeout)                         │
│     ├── Verificar distancia correcta                                    │
│     ├── Verificar torso recto                                           │
│     ├── Verificar landmarks visibles                                    │
│     └── ✅ Postura OK → Estado: COUNTDOWN                               │
│                                                                         │
│  5. ⏱️ CONTEO PREPARATORIO (3 segundos)                                 │
│     └── "3... 2... 1... ¡COMIENZA!"                                     │
│                                                                         │
│  6. 🏃 FASE DE MOVIMIENTO (12 segundos máximo)                          │
│     ├── Segundos 0-9: Recolectar ángulos (ANALYZING)                    │
│     ├── Detección de MESETA: Si ángulo estable ±5° por 2s               │
│     ├── Segundos 10-11: VENTANA DE CAPTURA (CAPTURING_ROM)              │
│     └── Segundo 12: Buffer seguridad (BUFFER_ZONE)                      │
│                                                                         │
│  7. 📊 CÁLCULO Y RESULTADO (CALCULATING → COMPLETED)                    │
│     ├── ROM = percentil_95 de ventana de captura                        │
│     ├── Calidad = basada en estabilidad                                 │
│     └── Clasificación = Óptimo/Funcional/Limitado/Muy Limitado          │
│                                                                         │
│  8. 💾 MOSTRAR RESULTADO                                                │
│     └── Usuario decide si guardar en historial                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 ARQUITECTURA DE ARCHIVOS

### Estructura Actual:
```
app/
├── analyzers/                      # Analizadores por segmento
│   ├── __init__.py
│   ├── base_analyzer.py           # ✅ CORREGIDO: Usa singleton + import fix
│   ├── shoulder_profile.py        # ✅ Usa singleton
│   ├── shoulder_frontal.py        # ✅ Usa singleton
│   ├── elbow_profile.py           # ⚠️ VACÍO (pendiente implementar)
│   ├── knee_profile.py            # ⚠️ VACÍO (pendiente implementar)
│   ├── hip_profile.py             # ⚠️ Verificar
│   ├── hip_frontal.py             # ⚠️ VACÍO (pendiente implementar)
│   ├── ankle_profile.py           # ⚠️ Verificar
│   ├── ankle_frontal.py           # ⚠️ Verificar
│   └── rom_evaluator.py           # ⚠️ Verificar contenido
│
├── core/                           # Componentes base
│   ├── __init__.py
│   ├── pose_singleton.py          # ✅ Singleton MediaPipe
│   ├── orientation_detector.py    # ✅ Detector orientación
│   ├── mediapipe_config.py        # ✅ Configuración
│   ├── camera_manager.py          # ✅ Gestión cámara
│   └── (NUEVOS A CREAR):
│       ├── analysis_session.py    # 🆕 Controlador de flujo
│       ├── person_detector.py     # 🆕 Detector de persona
│       └── posture_verifier.py    # 🆕 Verificador de postura
│
├── utils/                          # Utilidades
│   ├── rom_statistics.py          # 🆕 YA CREADO - Estadísticas ROM
│   └── rom_standards.py           # ✅ Clasificaciones ROM
│
├── services/                       # 🆕 NUEVO DIRECTORIO
│   └── tts_service.py             # 🆕 Servicio Text-to-Speech
│
└── routes/
    └── api.py                      # ⚠️ Modificar para nuevo flujo
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### FASE 0: Limpieza y Corrección ✅ COMPLETADO
- [x] **0.1** Leer y analizar `base_analyzer.py` completo
- [x] **0.2** Corregir `base_analyzer.py` para usar singleton (`get_shared_pose()`)
- [x] **0.3** Corregir import de `orientation_detector` en `base_analyzer.py` (línea 178)
- [x] **0.4** Verificar qué analyzers heredan de `BaseJointAnalyzer` (ninguno actualmente)
- [x] **0.5** Verificar contenido de `rom_evaluator.py` (VACÍO)
- [x] **0.6** Corregir `app/core/__init__.py` - Import incorrecto de BaseJointAnalyzer
- [ ] **0.7** Probar que el sistema sigue funcionando
- [ ] **0.8** Commit de limpieza

**Correcciones Fase 0:**
1. `base_analyzer.py`: Usa `get_shared_pose()` en lugar de `MediaPipeConfig.create_pose_detector()`
2. `base_analyzer.py`: Import corregido `from app.core.orientation_detector`
3. `app/core/__init__.py`: Eliminado import problemático de `BaseJointAnalyzer`
4. Archivos vacíos detectados: `elbow_profile.py`, `knee_profile.py`, `hip_profile.py`, `hip_frontal.py`, `ankle_profile.py`, `ankle_frontal.py`, `rom_evaluator.py`

### FASE 1: Integrar Singleton Completamente ✅ COMPLETADO
- [x] **1.1** Buscar TODAS las instancias de `MediaPipeConfig.create_pose_detector()` - No se usa en producción
- [x] **1.2** Verificar uso de `get_shared_pose()` - Todos los analyzers lo usan
- [x] **1.3** Verificar que solo existe UNA instancia de MediaPipe - Solo en `pose_singleton.py`
- [x] **1.4** Verificar sin hilos extra problemáticos - Solo locks para sincronización

### FASE 2: Crear Módulos de Detección ✅ COMPLETADO
- [x] **2.1** Crear `app/core/person_detector.py` - PersonDetector con singleton
- [x] **2.2** Crear `app/core/posture_verifier.py` - PostureVerifier con orientación/distancia/torso
- [ ] **2.3** Probar módulos de forma aislada
- [ ] **2.4** Documentar uso de cada módulo
- [ ] **2.5** Commit de nuevos módulos

**Módulos creados Fase 2:**
- `PersonDetector`: Detecta persona, evalúa landmarks esenciales (hombros+caderas), calcula confianza
- `PostureVerifier`: Verifica orientación, distancia, alineación de torso, landmarks requeridos
- Ambos usan singleton de MediaPipe (no crean nuevas instancias)

### FASE 3: Crear AnalysisSession ✅ COMPLETADO
- [x] **3.1** Crear `app/core/analysis_session.py`
- [x] **3.2** Implementar máquina de estados
- [x] **3.3** Integrar `PersonDetector` y `PostureVerifier`
- [x] **3.4** Crear `app/utils/rom_statistics.py` con ROMStatisticsCalculator
- [x] **3.5** Integrar `ROMStatisticsCalculator` en AnalysisSession

**Módulos creados Fase 3:**
- `ROMStatisticsCalculator`: Buffer temporal 5s, percentil 95, detección de plateau
- `AnalysisSession`: Máquina de estados completa (IDLE→DETECTING→ORIENTATION→POSTURE→COUNTDOWN→ANALYZING→COMPLETED)
- Funciones singleton: `create_analysis_session()`, `get_current_session()`, `clear_current_session()`
- NO crea hilos - usa singletons existentes

### FASE 4: Integrar con API ✅ COMPLETADO
- [x] **4.1** Crear endpoint `/api/session/start` - Inicia sesión con estados
- [x] **4.2** Crear endpoint `/api/session/status` - Polling del estado actual
- [x] **4.3** Crear endpoint `/api/session/stop` - Detiene sesión
- [x] **4.4** Crear endpoint `/api/session/process_frame` - Procesa frame en máquina de estados
- [x] **4.5** Optimizar rendimiento (polling 500ms, JPEG 60%, resolución 960x540)
- [x] **4.6** Mantener endpoints antiguos funcionando (backward compatible)
- [x] **4.7** Modificar frontend para usar nuevos endpoints
- [ ] **4.8** Probar flujo completo end-to-end

**Endpoints creados Fase 4:**
- `POST /api/session/start` - Crea AnalysisSession con joint_type, movement_type, orientation
- `GET /api/session/status` - Obtiene estado completo de la sesión
- `POST /api/session/stop` - Detiene y retorna resultado parcial si aplica
- `POST /api/session/process_frame` - Avanza máquina de estados con datos del frame

**Frontend actualizado Fase 4:**
- `live_analysis.js v3.0` - Nuevo flujo con estados
- Overlay de estado con animaciones (DETECTING → ORIENTATION → POSTURE → COUNTDOWN → ANALYZING)
- Polling de sesión cada 300ms para estados
- Countdown visual con números grandes
- Manejo automático de COMPLETED y ERROR

### FASE 5: Agregar TTS
- [ ] **5.1** Crear directorio `app/services/`
- [ ] **5.2** Crear `app/services/tts_service.py`
- [ ] **5.3** Integrar TTS con AnalysisSession
- [ ] **5.4** Configurar mensajes por estado
- [ ] **5.5** Probar que la voz no se corta
- [ ] **5.6** Commit de TTS

### FASE 6: Replicar a Otros Segmentos
- [ ] **6.1** Verificar que hombro funciona 100%
- [ ] **6.2** Aplicar patrón a codo
- [ ] **6.3** Aplicar patrón a rodilla
- [ ] **6.4** Aplicar patrón a cadera
- [ ] **6.5** Aplicar patrón a tobillo
- [ ] **6.6** Probar cada segmento individualmente
- [ ] **6.7** Commit final

---

## 🔴 PROBLEMAS IDENTIFICADOS

### Problema 1: `base_analyzer.py` crea instancia MediaPipe
```python
# ACTUAL (INCORRECTO):
self.pose = MediaPipeConfig.create_pose_detector()

# CORRECTO:
from app.core.pose_singleton import get_shared_pose
self.pose = get_shared_pose()
```

### Problema 2: Import incorrecto en `base_analyzer.py`
```python
# ACTUAL (INCORRECTO):
from core.orientation_detector import AdaptiveOrientationDetector

# CORRECTO:
from app.core.orientation_detector import AdaptiveOrientationDetector
```

### Problema 3: Analyzers no heredan de BaseJointAnalyzer
Los analyzers de hombro (`shoulder_profile.py`, `shoulder_frontal.py`) son clases independientes que NO heredan de `BaseJointAnalyzer`. Esto está BIEN porque usan el singleton directamente.

---

## 📐 ESPECIFICACIONES TÉCNICAS

### Tiempos del Flujo:
| Fase | Duración | Timeout |
|------|----------|---------|
| Detección persona | Variable | 10s |
| Verificación orientación | Variable | 5s |
| Verificación postura | Variable | 5s |
| Countdown | 3s | - |
| Análisis movimiento | 9s | - |
| Captura ROM | 2s (seg 10-11) | - |
| Buffer seguridad | 1s (seg 12) | - |
| **TOTAL MÁXIMO** | **~35s** | - |

### Cálculo de ROM:
- **Método principal**: Percentil 95 de ventana de captura (segundos 10-11)
- **Método alternativo**: Detección de meseta (si ángulo estable ±5° por 2s)
- **Fallback**: Máximo de todos los valores si no hay meseta

### Calidad de Medición:
| Desv. Estándar | Muestras | Calidad | Score |
|----------------|----------|---------|-------|
| < 3° | ≥ 10 | Excelente | 95% |
| < 5° | ≥ 5 | Buena | 80% |
| < 10° | ≥ 3 | Aceptable | 60% |
| ≥ 10° | Cualquiera | Baja | 40% |

---

## 🔒 REGLAS DE SEGURIDAD

1. **Un cambio a la vez**: Modificar 1 archivo, probar, confirmar, siguiente
2. **Backward compatibility**: No eliminar endpoints/funciones existentes
3. **Probar antes de integrar**: Cada módulo nuevo se prueba aislado
4. **No duplicar lógica**: Extraer a módulos compartidos
5. **Imports explícitos**: Siempre usar `from app.xxx` no `from xxx`

---

## 🛡️ REGLAS DE ORO - NO ROMPER LA ARQUITECTURA

> ⚠️ **CRÍTICO**: Estas reglas garantizan la estabilidad del sistema al agregar nuevos segmentos.
> **SIEMPRE** leer esta sección antes de implementar un nuevo segmento (codo, rodilla, cadera, tobillo).

### 🔴 ARCHIVOS QUE NUNCA SE DEBEN MODIFICAR

| Archivo | Razón | Consecuencia si se modifica |
|---------|-------|----------------------------|
| `app/core/pose_singleton.py` | Singleton de MediaPipe - TODOS los analyzers dependen de él | Sistema completo falla |
| `app/core/analysis_session.py` | Máquina de estados del flujo de análisis | Rompe flujo de TODOS los ejercicios |
| `app/core/person_detector.py` | Detección de persona compartida | Afecta detección en todos los segmentos |
| `app/core/posture_verifier.py` | Verificación de postura compartida | Afecta verificación en todos los segmentos |
| `app/utils/rom_statistics.py` | Cálculos estadísticos de ROM | Rompe cálculos de todos los ejercicios |

### 🟡 ARCHIVOS QUE SE PUEDEN IGNORAR (NO AFECTAN PRODUCCIÓN)

| Archivo | Estado | Razón |
|---------|--------|-------|
| `app/core/exercise_guide_base.py` | 🟡 No usado | Código experimental, NO está integrado |
| `app/analyzers/base_analyzer.py` | 🟡 No usado | Los analyzers actuales NO heredan de él |
| `app/core/fixed_references.py` | 🟡 Parcial | Solo para visualización de ejes |
| Archivos en `tests/` | 🟢 OK | Son pruebas standalone |

### ✅ REGLAS PARA CREAR NUEVO ANALYZER

#### Regla 1: SIEMPRE usar el Singleton de MediaPipe
```python
# ❌ NUNCA HACER ESTO:
import mediapipe as mp
self.pose = mp.solutions.pose.Pose()  # Crea instancia NUEVA = problemas

# ✅ SIEMPRE HACER ESTO:
from app.core.pose_singleton import get_shared_pose
self.pose = get_shared_pose()  # Reutiliza instancia EXISTENTE
```

#### Regla 2: NUNCA cerrar el singleton en cleanup()
```python
# ❌ NUNCA HACER ESTO:
def cleanup(self):
    self.pose.close()  # ¡¡ROMPE TODOS LOS ANALYZERS!!

# ✅ SIEMPRE HACER ESTO:
def cleanup(self):
    self.pose = None  # Solo liberar referencia, NO cerrar
```

#### Regla 3: Mantener interfaz CONSISTENTE
```python
# Todo analyzer DEBE tener estos métodos con estas firmas:
class NuevoSegmentoAnalyzer:
    def __init__(self, processing_width=640, processing_height=480, show_skeleton=False):
        ...
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Procesa frame y retorna imagen anotada"""
        ...
    
    def get_current_data(self) -> Dict[str, Any]:
        """Retorna datos actuales para polling"""
        ...
    
    def reset(self) -> None:
        """Resetea estadísticas"""
        ...
    
    def cleanup(self) -> None:
        """Libera recursos (NO cerrar singleton)"""
        ...
```

#### Regla 4: get_current_data() DEBE retornar estos campos mínimos
```python
def get_current_data(self) -> Dict[str, Any]:
    return {
        'angle': self.current_angle,           # Ángulo actual
        'max_rom': self.max_rom,               # ROM máximo
        'side': self.current_side,             # 'left', 'right', o 'unknown'
        'movement': self.movement_type,        # 'FLEX', 'EXT', etc.
        'is_valid_position': self.is_valid,    # Si posición es correcta
        'orientation': self.orientation,       # 'SAGITAL', 'FRONTAL'
        # Para bilateral agregar:
        'left_angle': ...,
        'right_angle': ...,
        'left_max_rom': ...,
        'right_max_rom': ...,
    }
```

#### Regla 5: Registrar analyzer en api.py
```python
# Archivo: app/routes/api.py
# Buscar el diccionario analyzer_classes y AGREGAR (no modificar existentes):

from app.analyzers.nuevo_segmento import NuevoSegmentoAnalyzer

analyzer_classes = {
    'shoulder_profile': ShoulderProfileAnalyzer,    # ← NO TOCAR
    'shoulder_frontal': ShoulderFrontalAnalyzer,    # ← NO TOCAR
    'elbow_profile': ElbowProfileAnalyzer,          # ← NO TOCAR (si ya existe)
    'nuevo_segmento': NuevoSegmentoAnalyzer,        # ← AGREGAR AQUÍ
}
```

#### Regla 6: Registrar ejercicio en main.py
```python
# Archivo: app/routes/main.py
# En exercises_db, AGREGAR (no modificar existentes):

exercises_db = {
    'shoulder': { ... },  # ← NO TOCAR
    'elbow': { ... },     # ← NO TOCAR (si ya existe)
    'nuevo_segmento': {
        'ejercicio_tipo': {
            'name': 'Nombre Visible',
            'analyzer_type': 'nuevo_segmento',  # Debe coincidir con key en api.py
            'camera_view': 'profile',           # 'profile' o 'frontal'
            # ... resto de configuración
        }
    }
}
```

### 🎯 PATRÓN DE COPIA SEGURA

Para crear un nuevo analyzer, **COPIAR** uno existente y modificar solo lo necesario:

```
1. Copiar: shoulder_profile.py → nuevo_profile.py
2. Cambiar: Nombre de clase
3. Cambiar: Landmarks usados (índices de MediaPipe)
4. Cambiar: Cálculo de ángulo específico
5. Cambiar: Lógica de detección de lado (si difiere)
6. Mantener: Estructura, interfaz, uso de singleton
```

### 🧪 CHECKLIST DE VERIFICACIÓN ANTES DE COMMIT

Antes de hacer commit de un nuevo analyzer:

- [ ] ¿Usa `get_shared_pose()` y NO `mp.solutions.pose.Pose()`?
- [ ] ¿`cleanup()` hace `self.pose = None` y NO `self.pose.close()`?
- [ ] ¿Tiene TODOS los métodos requeridos (`process_frame`, `get_current_data`, `reset`, `cleanup`)?
- [ ] ¿`get_current_data()` retorna todos los campos mínimos?
- [ ] ¿Está registrado en `api.py` → `analyzer_classes`?
- [ ] ¿Está configurado en `main.py` → `exercises_db`?
- [ ] ¿El ejercicio de HOMBRO sigue funcionando después del cambio?
- [ ] ¿No hay errores en consola del navegador?
- [ ] ¿No hay errores en terminal de Flask?

### 📊 ARQUITECTURA VISUAL - REFERENCIA RÁPIDA

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA ESTABLE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           pose_singleton.py (INTOCABLE)              │   │
│   │         UNA SOLA instancia de MediaPipe              │   │
│   │         ⚠️ NUNCA MODIFICAR ESTE ARCHIVO              │   │
│   └──────────────────────┬──────────────────────────────┘   │
│                          │                                   │
│          ┌───────────────┼───────────────┬───────────────┐  │
│          ▼               ▼               ▼               ▼  │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────┐  │
│   │  shoulder   │ │  shoulder   │ │   elbow     │ │ ... │  │
│   │  _profile   │ │  _frontal   │ │  _profile   │ │     │  │
│   │  ✅ ESTABLE │ │  ✅ ESTABLE │ │  🔧 NUEVO   │ │     │  │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────┘  │
│                                                              │
│   Cada analyzer:                                            │
│   ✅ Independiente (no hereda de otros)                     │
│   ✅ Usa singleton compartido                               │
│   ✅ Misma interfaz (process_frame, get_current_data, etc.) │
│   ✅ Cálculos de ángulo PROPIOS                             │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 LANDMARKS DE MEDIAPIPE - REFERENCIA RÁPIDA

| Índice | Nombre | Segmentos que lo usan |
|--------|--------|----------------------|
| 11 | left_shoulder | Hombro, Codo |
| 12 | right_shoulder | Hombro, Codo |
| 13 | left_elbow | Codo |
| 14 | right_elbow | Codo |
| 15 | left_wrist | Codo |
| 16 | right_wrist | Codo |
| 23 | left_hip | Hombro, Cadera, Rodilla |
| 24 | right_hip | Hombro, Cadera, Rodilla |
| 25 | left_knee | Rodilla, Tobillo |
| 26 | right_knee | Rodilla, Tobillo |
| 27 | left_ankle | Tobillo |
| 28 | right_ankle | Tobillo |

### Combinaciones de 3 Puntos por Segmento

| Segmento | Punto Superior | Punto Medio (articulación) | Punto Inferior |
|----------|----------------|---------------------------|----------------|
| Hombro | Cadera (23/24) | Hombro (11/12) | Codo (13/14) |
| Codo | Hombro (11/12) | Codo (13/14) | Muñeca (15/16) |
| Cadera | Hombro (11/12) | Cadera (23/24) | Rodilla (25/26) |
| Rodilla | Cadera (23/24) | Rodilla (25/26) | Tobillo (27/28) |
| Tobillo | Rodilla (25/26) | Tobillo (27/28) | Punta pie (31/32) |

---

## 🔐 AUDITORÍA DE SEGURIDAD Y PREVENCIÓN DE CONFLICTOS

> **Fecha de última auditoría:** 2025-12-06  
> **Estado:** ✅ Sistema estable - No hay conflictos de hilos ni sesiones

### 🧵 Gestión de Hilos y Procesos

| Componente | Tipo | Protección | Estado |
|------------|------|------------|--------|
| MediaPipe Pose | Singleton | `_pose_lock = threading.Lock()` | ✅ Seguro |
| TTS Service | Thread único | Cola de mensajes thread-safe | ✅ Seguro |
| Camera Manager | Singleton | Un solo stream activo | ✅ Seguro |
| MJPEG Stream | Generador síncrono | No crea hilos | ✅ Seguro |
| Analysis Session | Singleton | `_current_session` global | ✅ Seguro |

### 🔄 Ciclo de Vida de Sesiones de Análisis

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PUNTOS DE LIMPIEZA DE SESIÓN                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Usuario cambia de ejercicio (changeExercise en JS)               │
│     └──► JS llama: /api/camera/release                               │
│         └──► Backend: clear_current_session() ✅                     │
│                                                                      │
│  2. Usuario vuelve atrás (navigateBack en JS)                        │
│     └──► JS llama: /api/camera/release                               │
│         └──► Backend: clear_current_session() ✅                     │
│                                                                      │
│  3. Usuario detiene análisis manualmente                             │
│     └──► JS llama: /api/session/stop                                 │
│         └──► Backend: clear_current_session() ✅                     │
│                                                                      │
│  4. Se inicia nueva sesión (create_analysis_session)                 │
│     └──► Backend: Detiene sesión anterior automáticamente ✅         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### ⚠️ CASOS ESPECIALES EN ROM_STANDARDS

> **Importante:** Algunos ejercicios tienen lógica de clasificación especial.

| Ejercicio | Caso Especial | Razón |
|-----------|---------------|-------|
| Extensión de Codo | NO usa porcentaje >100% para "Aumentado" | Un ángulo alto (ej: 75°) indica LIMITACIÓN, no hiperlaxitud |
| Extensión de Rodilla | NO usa porcentaje >100% para "Aumentado" | Misma razón que codo |
| Hiperextensión de Codo | Ángulos negativos clasifican como "Aumentado" | Negativo = pasó de 0° (recto) |

**Código relevante en `rom_standards.py`:**
```python
# La verificación de porcentaje >100% NO aplica para extensión de codo/rodilla
is_extension_exercise = (
    (segment == "elbow" and exercise == "extension") or
    (segment == "knee" and exercise == "extension")
)

if percentage > 100.5 and not is_extension_exercise:
    # Solo entonces clasificar como "Aumentado"
```

### 🛡️ MEDICIONES SOSPECHOSAS

El sistema detecta mediciones potencialmente erróneas:

| Condición | Severidad | Mensaje |
|-----------|-----------|---------|
| Clasificación "muy_limitado" | ⚠️ Warning | "Verifique posicionamiento" |
| Ángulo fuera de rango físico | 🔴 Error | "Probablemente error de medición" |

**Límites físicos razonables por segmento:**
| Segmento | Ejercicio | Mín Razonable | Máx Razonable |
|----------|-----------|---------------|---------------|
| Codo | Flexión | 0° | 160° |
| Codo | Extensión | -20° | 30° |
| Hombro | Flexión | 0° | 200° |
| Hombro | Extensión | 0° | 80° |
| Rodilla | Flexión | 0° | 160° |

### ✅ VERIFICACIÓN POST-CAMBIOS

Después de agregar un nuevo segmento o modificar código:

1. **Probar HOMBRO FLEXIÓN** (segmento de referencia)
   - [ ] ¿Detecta persona?
   - [ ] ¿Detecta orientación perfil?
   - [ ] ¿Cuenta regresiva funciona?
   - [ ] ¿Captura ROM?
   - [ ] ¿Muestra resultado?
   - [ ] ¿Guarda en historial?

2. **Verificar consola del navegador (F12)**
   - [ ] ¿Sin errores JavaScript?
   - [ ] ¿Sin warnings de "sesión activa"?

3. **Verificar terminal Flask**
   - [ ] ¿Sin errores de importación?
   - [ ] ¿Sin errores de threading?

4. **Probar navegación**
   - [ ] Ir a hombro → codo → hombro
   - [ ] ¿La cámara se libera correctamente?
   - [ ] ¿No hay "fantasmas" de sesiones anteriores?

---

## 📝 NOTAS DE IMPLEMENTACIÓN

### Singleton de MediaPipe:
```python
# Archivo: app/core/pose_singleton.py
# USO CORRECTO en cualquier analyzer:
from app.core.pose_singleton import get_shared_pose

class MiAnalyzer:
    def __init__(self):
        self.pose = get_shared_pose()  # Reutiliza instancia existente
```

### Estados de AnalysisSession:
```python
class AnalysisState(Enum):
    IDLE = "idle"                    # Esperando inicio
    DETECTING_PERSON = "detecting"   # Buscando persona
    CHECKING_ORIENTATION = "orientation"  # Verificando perfil/frontal
    CHECKING_POSTURE = "posture"     # Verificando postura
    COUNTDOWN = "countdown"          # 3, 2, 1...
    ANALYZING = "analyzing"          # Capturando movimiento (0-9s)
    CAPTURING_ROM = "capturing"      # Ventana de captura (10-11s)
    BUFFER_ZONE = "buffer"           # Segundo 12 (no guardar)
    CALCULATING = "calculating"      # Calculando resultado
    COMPLETED = "completed"          # Mostrando resultado
    ERROR = "error"                  # Algo falló
```

---

## 📚 REFERENCIAS

- **MediaPipe Pose**: https://google.github.io/mediapipe/solutions/pose.html
- **ROM Standards**: AAOS, AMA Guides 6th ed., Kapandji
- **Percentil 95**: Robusto contra outliers, validable con goniómetro

---

## 🔄 HISTORIAL DE CAMBIOS

| Fecha | Fase | Cambio | Estado |
|-------|------|--------|--------|
| 2025-11-26 | - | Documento creado | ✅ |
| 2025-11-26 | 0 | Limpieza y correcciones base | ✅ |
| 2025-11-27 | 1-4 | Singleton, módulos core, API, frontend | ✅ |
| 2025-11-30 | - | Historial de usuario, detección de lado, UI | ✅ |
| 2025-11-30 | - | Dropdown navegación ejercicios, liberación cámara | ✅ |
| 2025-11-30 | - | Documentación arquitectura MJPEG streaming | ✅ |
| 2025-11-30 | - | **Guía completa de replicación para otros segmentos** | ✅ |
| 2025-12-01 | - | Overlays de video deshabilitados (info en panel web) | ✅ |
| 2025-12-01 | - | Símbolo de grados corregido (° → o superíndice) | ✅ |
| 2025-12-01 | - | Asimetría en modal bilateral y clasificación por lado | ✅ |
| 2025-12-05 | - | **🛡️ REGLAS DE ORO agregadas** - Protección arquitectura | ✅ |

---

## 👤 RESPONSABLES

- **Desarrollo**: Mariana (MarianaCO7)
- **Asistencia**: GitHub Copilot (Claude Opus 4.5)

---

## 🎥 ARQUITECTURA DE STREAMING DE VIDEO

### Tecnología: MJPEG (Motion JPEG) sobre HTTP

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FLUJO DE VIDEO ACTUAL                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  NAVEGADOR                              SERVIDOR FLASK                  │
│  ┌────────────────┐                     ┌─────────────────────────┐     │
│  │ <img src=      │◄── HTTP Stream ─────│ /api/video_feed         │     │
│  │  "/api/video   │   (MJPEG continuo)  │  │                      │     │
│  │   _feed">      │                     │  ▼                      │     │
│  └────────────────┘                     │ generate_frames():      │     │
│                                         │  └─ while True:         │     │
│  ┌────────────────┐                     │      ├─ cap.read()      │     │
│  │ Polling 500ms  │◄── AJAX (JSON) ─────│      ├─ process_frame() │     │
│  │ /api/analysis/ │                     │      ├─ imencode JPEG   │     │
│  │  current_data  │                     │      └─ yield bytes     │     │
│  └────────────────┘                     └─────────────────────────┘     │
│                                                                         │
│  IMPORTANTE:                                                            │
│  - UN solo stream continuo (no múltiples requests por frame)            │
│  - El procesamiento MediaPipe ocurre en el SERVIDOR                     │
│  - Los datos numéricos (ángulo, ROM) se obtienen por polling separado   │
└─────────────────────────────────────────────────────────────────────────┘
```

### ¿Por qué MJPEG y no WebRTC?

| Aspecto | MJPEG (Actual) | WebRTC |
|---------|----------------|--------|
| **Procesamiento servidor** | ✅ Ideal (MediaPipe en backend) | ❌ Requiere reenvío |
| **Complejidad** | Baja (solo HTTP) | Alta (STUN/TURN/ICE) |
| **Latencia** | ~100-200ms | ~50-100ms |
| **Justificación** | Procesamiento en servidor es requisito | No aporta valor |

### Optimizaciones Aplicadas

```python
# camera_manager.py
self._camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo = menos latencia
self._camera.set(cv2.CAP_PROP_FPS, 30)        # 30 FPS

# api.py - video_feed
jpeg_quality = 60                              # Balance calidad/velocidad
processing_width, processing_height = 960, 540 # Resolución procesamiento
```

### Sin Múltiples Hilos Problemáticos

- Flask maneja cada request en un worker
- El generador `generate_frames()` es síncrono
- Solo UN stream activo por usuario (camera_manager singleton)
- MediaPipe singleton evita conflictos de recursos

---

## 📋 IMPLEMENTACIONES COMPLETADAS (REPLICAR EN OTROS SEGMENTOS)

### 1. Analyzer Profile (ej: `shoulder_profile.py`)

**Estructura base:**
```python
from app.core.pose_singleton import get_shared_pose

class ShoulderProfileAnalyzer:
    def __init__(self, processing_width=640, processing_height=480, show_skeleton=False):
        # ⚡ USAR SINGLETON - NO crear nueva instancia
        self.pose = get_shared_pose()
        
        # Variables de tracking
        self.current_angle = 0.0
        self.max_angle = 0.0
        self.side = "Detectando..."      # 'left', 'right', 'Detectando...'
        self.orientation = "Detectando..." 
        self.confidence = 0.0
        
        # Estado de postura
        self.posture_valid = False
        self.landmarks_detected = False
        self.is_profile_position = False
        self.orientation_quality = 0.0
    
    def detect_side(self, landmarks) -> Tuple[str, float, str]:
        """
        Detecta qué lado del cuerpo está visible.
        
        LÓGICA CORREGIDA (considera efecto espejo de webcam):
        - nose.x > centro_hombros → usuario mirando a su DERECHA → lado DERECHO visible
        - nose.x < centro_hombros → usuario mirando a su IZQUIERDA → lado IZQUIERDO visible
        
        Returns:
            (side, confidence, orientation)
        """
        nose = landmarks[0]
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        nose_offset = nose.x - shoulder_center_x
        
        if nose_offset > 0.03:
            return ('right', visibility, "mirando izquierda")
        elif nose_offset < -0.03:
            return ('left', visibility, "mirando derecha")
        else:
            return (self.side if self.side != "Detectando..." else 'right', 
                    visibility, "frontal/transición")
    
    def process_frame(self, frame) -> np.ndarray:
        """Procesa un frame y retorna imagen anotada."""
        # 1. Convertir BGR→RGB
        # 2. self.pose.process(rgb_frame)
        # 3. Detectar lado y orientación
        # 4. Calcular ángulo
        # 5. Actualizar max_angle
        # 6. Dibujar anotaciones
        # 7. Retornar frame anotado
    
    def get_current_data(self) -> Dict[str, Any]:
        """Retorna datos actuales para el polling."""
        return {
            'angle': round(self.current_angle, 1),
            'max_rom': round(self.max_angle, 1),
            'side': self.side,
            'orientation': self.orientation,
            'confidence': round(self.confidence, 2),
            'landmarks_detected': self.landmarks_detected,
            'posture_valid': self.posture_valid,
            'is_profile': self.is_profile_position,
            'orientation_quality': round(self.orientation_quality, 2)
        }
    
    def reset(self):
        """Resetea estadísticas."""
        self.max_angle = 0.0
        self.current_angle = 0.0
```

### 2. Analyzer Frontal (ej: `shoulder_frontal.py`)

**Diferencias clave:**
```python
class ShoulderFrontalAnalyzer:
    def __init__(self, ...):
        # Variables BILATERALES
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_max_rom = 0.0
        self.right_max_rom = 0.0
        self.asymmetry = 0.0
        
        # Orientación frontal
        self.orientation_frontal = False
        self.is_frontal_position = False
    
    def get_current_data(self) -> Dict[str, Any]:
        return {
            'left_angle': round(self.left_angle, 1),
            'right_angle': round(self.right_angle, 1),
            'left_max_rom': round(self.left_max_rom, 1),
            'right_max_rom': round(self.right_max_rom, 1),
            'asymmetry': round(self.asymmetry, 1),
            'is_bilateral': True,
            'side': 'bilateral',  # SIEMPRE bilateral
            # ... resto igual
        }
```

### 3. Base de Datos - Historial de Usuario

**Tabla `user_analysis_history`:**
```sql
CREATE TABLE user_analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    segment VARCHAR(50) NOT NULL,           -- 'shoulder', 'elbow', 'knee'...
    exercise_type VARCHAR(50) NOT NULL,     -- 'flexion', 'extension', 'abduction'...
    body_side VARCHAR(20),                  -- 'left', 'right', 'bilateral'
    camera_view VARCHAR(20),                -- 'profile', 'frontal'
    rom_value FLOAT,                        -- Valor ROM principal
    left_rom FLOAT,                         -- Solo para bilateral
    right_rom FLOAT,                        -- Solo para bilateral
    classification VARCHAR(50),             -- 'Normal', 'Limitado', etc.
    quality_score FLOAT,
    duration FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Modelo en `database_manager.py`:**
```python
import pytz

def get_bolivia_time():
    """Retorna hora actual en zona horaria de Bolivia (GMT-4)."""
    bolivia_tz = pytz.timezone('America/La_Paz')
    return datetime.now(bolivia_tz)

class UserAnalysisHistory(db.Model):
    __tablename__ = 'user_analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    segment = db.Column(db.String(50), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    body_side = db.Column(db.String(20))
    camera_view = db.Column(db.String(20))
    rom_value = db.Column(db.Float)
    left_rom = db.Column(db.Float)
    right_rom = db.Column(db.Float)
    classification = db.Column(db.String(50))
    quality_score = db.Column(db.Float)
    duration = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_bolivia_time)
```

### 4. Endpoints API para Historial

```python
# api.py

@api_bp.route('/analysis/save', methods=['POST'])
@login_required
def save_analysis_to_history():
    """Guarda resultado de análisis en historial del usuario."""
    data = request.get_json()
    user_id = session.get('user_id')
    
    result = db_manager.save_analysis_to_history(
        user_id=user_id,
        segment=data['segment'],
        exercise_type=data['exercise_type'],
        body_side=data.get('side'),
        camera_view=data.get('camera_view'),
        rom_value=data.get('rom_value'),
        left_rom=data.get('left_rom'),
        right_rom=data.get('right_rom'),
        classification=data.get('classification'),
        quality_score=data.get('quality_score'),
        duration=data.get('duration'),
        notes=data.get('notes')
    )
    return jsonify({'success': True, 'id': result['id']})

@api_bp.route('/analysis/recent', methods=['GET'])
@login_required
def get_recent_analysis():
    """Obtiene últimos 5 análisis de un ejercicio."""
    segment = request.args.get('segment')
    exercise_type = request.args.get('exercise_type')
    
    history = db_manager.get_recent_history_for_exercise(
        user_id=session['user_id'],
        segment=segment,
        exercise_type=exercise_type,
        limit=5
    )
    return jsonify({'success': True, 'history': history})
```

### 5. JavaScript - Guardar con Lado Correcto

**Problema resuelto:** El lado mostrado en UI no coincidía con el guardado.

**Solución:** Capturar lado del polling (mismo que UI):
```javascript
class LiveAnalysisController {
    constructor(config) {
        // ...
        this.lastDetectedSide = null;  // Lado del polling
    }
    
    updateUI(data) {
        // Actualizar UI...
        
        // GUARDAR lado del polling (es el que se muestra en UI)
        this.lastDetectedSide = data.side;
    }
    
    async saveResults() {
        // USAR lado del polling, no de finalData
        const sideToSave = this.lastDetectedSide || finalData.side || 'unknown';
        
        const saveData = {
            // ...
            side: sideToSave,  // ✅ Mismo lado que se ve en UI
        };
    }
}
```

### 6. Dropdown de Navegación entre Ejercicios

**Template (`live_analysis.html`):**
```html
<div class="exercise-dropdown-container">
    <button class="exercise-dropdown-btn" onclick="toggleExerciseDropdown()">
        <i class="bi bi-camera-video-fill me-2"></i>
        <span>{{ exercise_name }}</span>
        <i class="bi bi-chevron-down ms-2 dropdown-arrow"></i>
    </button>
    
    <div class="exercise-dropdown-menu" id="exerciseDropdownMenu">
        {% for segment in all_exercises_menu %}
        <div class="dropdown-segment">
            <div class="dropdown-segment-title">{{ segment.name }}</div>
            {% for ex in segment.exercises %}
            <a href="#" class="dropdown-exercise-item {% if ex.is_current %}current{% endif %}"
               onclick="changeExercise('{{ segment.key }}', '{{ ex.key }}'); return false;">
                {{ ex.name }}
                {% if ex.is_current %}<i class="bi bi-check-lg"></i>{% endif %}
            </a>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
</div>
```

**JavaScript (liberación de cámara antes de navegar):**
```javascript
async function changeExercise(segmentKey, exerciseKey) {
    // 1. Cerrar dropdown
    document.getElementById('exerciseDropdownMenu').classList.remove('show');
    
    // 2. Detener video feed
    document.getElementById('videoFeed').src = '';
    
    // 3. Detener polling
    if (liveAnalysisController) {
        liveAnalysisController.stopDataPolling();
        liveAnalysisController.stopSessionPolling();
    }
    
    // 4. Liberar cámara
    await fetch('/api/camera/release', { method: 'POST' });
    
    // 5. Pequeña pausa
    await new Promise(r => setTimeout(r, 100));
    
    // 6. Navegar
    window.location.href = `/segments/${segmentKey}/exercises/${exerciseKey}`;
}
```

**Backend (`main.py`):**
```python
# Preparar lista de ejercicios para dropdown
all_exercises_menu = []
segment_names = {'shoulder': 'Hombro', 'elbow': 'Codo', ...}

for seg_key, seg_exercises in exercises_db.items():
    segment_info = {
        'key': seg_key,
        'name': segment_names.get(seg_key, seg_key.capitalize()),
        'exercises': []
    }
    for ex_key, ex_data in seg_exercises.items():
        segment_info['exercises'].append({
            'key': ex_key,
            'name': ex_data['name'],
            'view': ex_data['camera_view_label'],
            'is_current': (seg_key == segment_type and ex_key == exercise_key)
        })
    all_exercises_menu.append(segment_info)

return render_template('...', all_exercises_menu=all_exercises_menu)
```

---

## 🎯 IMPLEMENTACIÓN COMPLETA DEL SEGMENTO HOMBRO (REFERENCIAR PARA OTROS)

Esta sección documenta **EXACTAMENTE** cómo está implementado el segmento "Hombro" para que sirva como plantilla al implementar otros segmentos (Codo, Rodilla, Cadera, Tobillo).

---

### 📁 ARCHIVO 1: Analyzer Profile (`app/analyzers/shoulder_profile.py`)

**Propósito:** Analizar movimientos de perfil (Flexión/Extensión)

```python
"""
ESTRUCTURA COMPLETA DE UN ANALYZER DE PERFIL
=============================================
Este es el código real de shoulder_profile.py simplificado para referencia.
"""

import cv2
import numpy as np
import math
from typing import Dict, Any, Optional, Tuple, List
from app.core.pose_singleton import get_shared_pose  # ⚡ CRÍTICO

class ShoulderProfileAnalyzer:
    """Analizador de hombro en vista de perfil (Flexión/Extensión)."""
    
    def __init__(self, processing_width: int = 640, processing_height: int = 480, show_skeleton: bool = False):
        # ============ MEDIAPIPE SINGLETON ============
        # ⚠️ NUNCA crear mp.solutions.pose.Pose() directamente
        self.pose = get_shared_pose()
        
        # ============ DIMENSIONES ============
        self.processing_width = processing_width
        self.processing_height = processing_height
        self.show_skeleton = show_skeleton
        
        # ============ VARIABLES DE TRACKING ============
        self.current_angle = 0.0
        self.max_angle = 0.0
        self.side = "Detectando..."        # 'left', 'right', 'Detectando...'
        self.orientation = "Detectando..."  # 'mirando izquierda', 'mirando derecha'
        self.confidence = 0.0
        
        # ============ ESTADO DE POSTURA ============
        self.posture_valid = False
        self.landmarks_detected = False
        self.is_profile_position = False
        self.orientation_quality = 0.0
        
        # ============ CALIBRACIÓN ============
        self.is_calibrated = False
        self.calibration_angle = None
        
        # ============ HISTÉRESIS (para estabilidad) ============
        self._side_history = []
        self._side_history_size = 5  # Número de frames para promediar
        
        # ============ COLORES PARA DIBUJO ============
        self.COLOR_PRIMARY = (0, 200, 255)    # Amarillo/Naranja
        self.COLOR_SUCCESS = (0, 255, 0)       # Verde
        self.COLOR_WARNING = (0, 165, 255)     # Naranja
        self.COLOR_ERROR = (0, 0, 255)         # Rojo
        self.COLOR_INFO = (255, 255, 255)      # Blanco
        
        print(f"[ShoulderProfileAnalyzer] Inicializado con resolución {processing_width}x{processing_height}")

    # ============ DETECCIÓN DE LADO ============
    def detect_side(self, landmarks) -> Tuple[str, float, str]:
        """
        Detecta qué lado del cuerpo está visible en vista de perfil.
        
        LÓGICA (considerando efecto espejo de webcam):
        - Si nariz.x > centro_hombros → usuario mirando a SU DERECHA → lado DERECHO visible
        - Si nariz.x < centro_hombros → usuario mirando a SU IZQUIERDA → lado IZQUIERDO visible
        
        La webcam invierte la imagen como un espejo, entonces:
        - Lo que parece "izquierda" en pantalla es realmente el lado derecho del usuario
        
        Returns:
            Tuple[str, float, str]: (lado, confianza, descripción_orientación)
        """
        try:
            nose = landmarks[0]
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            
            # Calcular centro de hombros
            shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
            
            # Visibilidad como indicador de confianza
            visibility = min(nose.visibility, left_shoulder.visibility, right_shoulder.visibility)
            
            # Offset de la nariz respecto al centro
            nose_offset = nose.x - shoulder_center_x
            
            # Umbral para detección (0.03 = 3% del ancho de imagen)
            threshold = 0.03
            
            if nose_offset > threshold:
                # Nariz a la derecha del centro → mirando hacia izquierda de pantalla
                # → En realidad mirando a SU derecha → Lado DERECHO visible
                detected_side = 'right'
                orientation = "mirando izquierda (lado der.)"
            elif nose_offset < -threshold:
                # Nariz a la izquierda del centro → mirando hacia derecha de pantalla
                # → En realidad mirando a SU izquierda → Lado IZQUIERDO visible
                detected_side = 'left'
                orientation = "mirando derecha (lado izq.)"
            else:
                # Zona de transición - mantener lado actual
                detected_side = self.side if self.side != "Detectando..." else 'right'
                orientation = "frontal/transición"
            
            # Aplicar histéresis para estabilidad
            self._side_history.append(detected_side)
            if len(self._side_history) > self._side_history_size:
                self._side_history.pop(0)
            
            # Usar lado más frecuente en historial
            if len(self._side_history) >= 3:
                from collections import Counter
                side_counts = Counter(self._side_history)
                stable_side = side_counts.most_common(1)[0][0]
                return (stable_side, visibility, orientation)
            
            return (detected_side, visibility, orientation)
            
        except Exception as e:
            print(f"[detect_side] Error: {e}")
            return (self.side if self.side != "Detectando..." else 'right', 0.5, "error")

    # ============ VERIFICAR POSICIÓN DE PERFIL ============
    def verify_profile_position(self, landmarks) -> Tuple[bool, float]:
        """
        Verifica si el usuario está en posición de perfil adecuada.
        
        Criterios:
        1. Diferencia de profundidad (Z) entre hombros
        2. Visibilidad de landmarks clave
        3. Alineación vertical del torso
        
        Returns:
            Tuple[bool, float]: (es_perfil_válido, calidad_0_a_1)
        """
        try:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            
            # Criterio 1: Diferencia de Z (profundidad)
            z_diff = abs(left_shoulder.z - right_shoulder.z)
            
            # Criterio 2: Visibilidad mínima
            min_visibility = min(left_shoulder.visibility, right_shoulder.visibility)
            
            # Umbrales relajados para mejor UX
            is_profile = z_diff > 0.05  # Diferencia mínima de profundidad
            quality = min(1.0, z_diff * 5)  # Escalar a 0-1
            
            if min_visibility < 0.5:
                quality *= 0.5  # Penalizar baja visibilidad
            
            return (is_profile and min_visibility > 0.3, quality)
            
        except Exception as e:
            print(f"[verify_profile_position] Error: {e}")
            return (False, 0.0)

    # ============ CÁLCULO DE ÁNGULO ============
    def calculate_extension_angle(self, landmarks, side: str) -> float:
        """
        Calcula el ángulo de flexión/extensión del hombro.
        
        Puntos utilizados:
        - Hombro (11 izq, 12 der)
        - Codo (13 izq, 14 der)
        - Cadera (23 izq, 24 der)
        
        El ángulo se mide entre:
        - Vector hombro→codo
        - Vector vertical (perpendicular al suelo)
        
        Returns:
            float: Ángulo en grados (0° = brazo abajo, 180° = brazo arriba)
        """
        try:
            if side == 'left':
                shoulder_idx, elbow_idx, hip_idx = 11, 13, 23
            else:
                shoulder_idx, elbow_idx, hip_idx = 12, 14, 24
            
            shoulder = landmarks[shoulder_idx]
            elbow = landmarks[elbow_idx]
            hip = landmarks[hip_idx]
            
            # Convertir a coordenadas de píxel
            sh_x = shoulder.x * self.processing_width
            sh_y = shoulder.y * self.processing_height
            el_x = elbow.x * self.processing_width
            el_y = elbow.y * self.processing_height
            hp_x = hip.x * self.processing_width
            hp_y = hip.y * self.processing_height
            
            # Vector del brazo (hombro a codo)
            arm_vector = (el_x - sh_x, el_y - sh_y)
            
            # Vector vertical (hacia abajo, como el torso)
            vertical_vector = (hp_x - sh_x, hp_y - sh_y)
            
            # Calcular ángulo usando producto punto
            dot = arm_vector[0] * vertical_vector[0] + arm_vector[1] * vertical_vector[1]
            mag_arm = math.sqrt(arm_vector[0]**2 + arm_vector[1]**2)
            mag_vert = math.sqrt(vertical_vector[0]**2 + vertical_vector[1]**2)
            
            if mag_arm == 0 or mag_vert == 0:
                return 0.0
            
            cos_angle = dot / (mag_arm * mag_vert)
            cos_angle = max(-1, min(1, cos_angle))  # Clamp para evitar errores de acos
            
            angle = math.degrees(math.acos(cos_angle))
            
            return angle
            
        except Exception as e:
            print(f"[calculate_extension_angle] Error: {e}")
            return 0.0

    # ============ PROCESAR FRAME ============
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un frame de video y retorna imagen anotada.
        
        Flujo:
        1. Convertir BGR→RGB (MediaPipe requiere RGB)
        2. Procesar con MediaPipe
        3. Detectar lado visible
        4. Verificar posición de perfil
        5. Calcular ángulo
        6. Actualizar máximos
        7. Dibujar anotaciones
        8. Retornar frame anotado
        """
        if frame is None:
            return np.zeros((self.processing_height, self.processing_width, 3), dtype=np.uint8)
        
        # Redimensionar si es necesario
        if frame.shape[1] != self.processing_width or frame.shape[0] != self.processing_height:
            frame = cv2.resize(frame, (self.processing_width, self.processing_height))
        
        # Copiar frame para anotaciones
        annotated_frame = frame.copy()
        
        # Convertir a RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Procesar con MediaPipe
        results = self.pose.process(rgb_frame)
        
        if results.pose_landmarks:
            self.landmarks_detected = True
            landmarks = results.pose_landmarks.landmark
            
            # 1. Detectar lado
            self.side, self.confidence, self.orientation = self.detect_side(landmarks)
            
            # 2. Verificar posición de perfil
            self.is_profile_position, self.orientation_quality = self.verify_profile_position(landmarks)
            
            # 3. Calcular ángulo
            if self.is_profile_position:
                self.current_angle = self.calculate_extension_angle(landmarks, self.side)
                
                # Aplicar calibración si existe
                if self.is_calibrated and self.calibration_angle is not None:
                    self.current_angle = abs(self.current_angle - self.calibration_angle)
                
                # Actualizar máximo
                if self.current_angle > self.max_angle:
                    self.max_angle = self.current_angle
                
                self.posture_valid = True
            else:
                self.posture_valid = False
            
            # 4. Dibujar skeleton si está habilitado
            if self.show_skeleton:
                self._draw_skeleton(annotated_frame, landmarks)
            
            # 5. Dibujar información de ángulo
            self._draw_angle_info(annotated_frame)
            
            # 6. Dibujar indicador de lado
            self._draw_side_indicator(annotated_frame)
            
        else:
            self.landmarks_detected = False
            self.posture_valid = False
            self._draw_no_detection_warning(annotated_frame)
        
        return annotated_frame

    # ============ GET CURRENT DATA (CRÍTICO PARA FRONTEND) ============
    def get_current_data(self) -> Dict[str, Any]:
        """
        Retorna datos actuales para el polling del frontend.
        
        ⚠️ IMPORTANTE: El frontend (live_analysis.js) espera EXACTAMENTE estos campos.
        Si falta alguno, la UI puede fallar.
        
        Returns:
            Dict con todos los campos necesarios para la UI
        """
        # Determinar lado para mostrar en español
        side_display = {
            'left': 'IZQ',
            'right': 'DER',
            'Detectando...': 'Detectando...'
        }.get(self.side, self.side)
        
        return {
            # === DATOS DE ÁNGULO ===
            'angle': round(self.current_angle, 1),
            'max_rom': round(self.max_angle, 1),
            
            # === DATOS DE LADO/ORIENTACIÓN ===
            'side': self.side,              # 'left', 'right' (para lógica)
            'side_display': side_display,   # 'IZQ', 'DER' (para mostrar)
            'orientation': self.orientation,
            'confidence': round(self.confidence, 2),
            
            # === ESTADO DE DETECCIÓN ===
            'landmarks_detected': self.landmarks_detected,
            'posture_valid': self.posture_valid,
            'is_profile': self.is_profile_position,
            'orientation_quality': round(self.orientation_quality, 2),
            
            # === CALIBRACIÓN ===
            'is_calibrated': self.is_calibrated,
            
            # === PARA ANÁLISIS BILATERAL (compatibilidad) ===
            'is_bilateral': False,
            
            # === TIMESTAMP ===
            'timestamp': None  # Se puede agregar si es necesario
        }

    # ============ RESET (NUEVA MEDICIÓN) ============
    def reset(self):
        """Resetea todas las estadísticas para nueva medición."""
        self.current_angle = 0.0
        self.max_angle = 0.0
        self.is_calibrated = False
        self.calibration_angle = None
        self._side_history.clear()
        print("[ShoulderProfileAnalyzer] Reset completado")

    # ============ CLEANUP (LIBERAR RECURSOS) ============
    def cleanup(self):
        """
        Limpia recursos.
        
        ⚠️ NO cerrar self.pose porque es singleton compartido.
        Solo limpiar recursos propios del analyzer.
        """
        self._side_history.clear()
        # NO hacer: self.pose.close()  ← Esto rompería otros analyzers
        print("[ShoulderProfileAnalyzer] Cleanup completado")

    # ============ CALIBRACIÓN ============
    def calibrate(self):
        """Calibra tomando ángulo actual como referencia (0°)."""
        if self.posture_valid and self.current_angle > 0:
            self.calibration_angle = self.current_angle
            self.is_calibrated = True
            print(f"[ShoulderProfileAnalyzer] Calibrado en {self.calibration_angle}°")
            return True
        return False
    
    # ============ MÉTODOS AUXILIARES DE DIBUJO ============
    def _draw_skeleton(self, frame, landmarks):
        """Dibuja skeleton completo."""
        # Implementar según necesidad
        pass
    
    def _draw_angle_info(self, frame):
        """Dibuja información de ángulo en pantalla."""
        color = self.COLOR_SUCCESS if self.posture_valid else self.COLOR_WARNING
        cv2.putText(frame, f"Angulo: {self.current_angle:.1f}°", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"Max ROM: {self.max_angle:.1f}°", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_INFO, 2)
    
    def _draw_side_indicator(self, frame):
        """Dibuja indicador de lado detectado."""
        side_text = "IZQ" if self.side == 'left' else "DER" if self.side == 'right' else "?"
        cv2.putText(frame, f"Lado: {side_text}", 
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_INFO, 2)
    
    def _draw_no_detection_warning(self, frame):
        """Dibuja advertencia cuando no hay detección."""
        cv2.putText(frame, "No se detecta persona", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.COLOR_ERROR, 2)
```

---

### 📁 ARCHIVO 2: Analyzer Frontal (`app/analyzers/shoulder_frontal.py`)

**Propósito:** Analizar movimientos frontales bilaterales (Abducción)

```python
"""
ESTRUCTURA COMPLETA DE UN ANALYZER FRONTAL/BILATERAL
====================================================
"""

class ShoulderFrontalAnalyzer:
    """Analizador de hombro en vista frontal (Abducción bilateral)."""
    
    def __init__(self, processing_width: int = 640, processing_height: int = 480, show_skeleton: bool = False):
        self.pose = get_shared_pose()  # ⚡ SINGLETON
        
        # === VARIABLES BILATERALES ===
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_max_rom = 0.0
        self.right_max_rom = 0.0
        self.asymmetry = 0.0  # Diferencia entre lados
        
        # === ORIENTACIÓN FRONTAL ===
        self.is_frontal_position = False
        self.frontal_quality = 0.0
        
        # === HISTÉRESIS PARA ORIENTACIÓN ===
        self._frontal_history = []
        self._frontal_history_size = 10
        self._frontal_threshold_enter = 0.7  # Umbral para entrar a frontal
        self._frontal_threshold_exit = 0.5   # Umbral para salir de frontal

    def detect_frontal_orientation(self, landmarks) -> Tuple[bool, float]:
        """
        Detecta si el usuario está en orientación frontal.
        
        Usa HISTÉRESIS para evitar oscilaciones:
        - Para ENTRAR a estado frontal: calidad > 0.7
        - Para SALIR de estado frontal: calidad < 0.5
        
        Esto evita que pequeños movimientos cambien el estado constantemente.
        """
        try:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            
            # Calcular diferencia de Z (profundidad)
            z_diff = abs(left_shoulder.z - right_shoulder.z)
            
            # Calcular ancho de hombros en X
            shoulder_width = abs(left_shoulder.x - right_shoulder.x)
            
            # Calidad frontal: baja diferencia Z + buen ancho
            if shoulder_width > 0.1:  # Hombros visibles
                quality = 1.0 - min(1.0, z_diff * 5)
            else:
                quality = 0.0
            
            # Agregar a historial
            self._frontal_history.append(quality)
            if len(self._frontal_history) > self._frontal_history_size:
                self._frontal_history.pop(0)
            
            # Promedio de historial
            avg_quality = sum(self._frontal_history) / len(self._frontal_history)
            
            # Aplicar histéresis
            if self.is_frontal_position:
                # Ya estamos en frontal, necesita bajar mucho para salir
                is_frontal = avg_quality > self._frontal_threshold_exit
            else:
                # No estamos en frontal, necesita subir mucho para entrar
                is_frontal = avg_quality > self._frontal_threshold_enter
            
            return (is_frontal, avg_quality)
            
        except Exception as e:
            return (False, 0.0)

    def calculate_abduction_angle(self, landmarks, side: str) -> float:
        """
        Calcula ángulo de abducción para un lado.
        
        Abducción = elevación lateral del brazo
        - 0° = brazo pegado al cuerpo
        - 90° = brazo horizontal
        - 180° = brazo vertical arriba
        """
        if side == 'left':
            shoulder_idx, elbow_idx, hip_idx = 11, 13, 23
        else:
            shoulder_idx, elbow_idx, hip_idx = 12, 14, 24
        
        shoulder = landmarks[shoulder_idx]
        elbow = landmarks[elbow_idx]
        hip = landmarks[hip_idx]
        
        # Vector brazo
        arm_x = elbow.x - shoulder.x
        arm_y = elbow.y - shoulder.y
        
        # Vector torso (vertical)
        torso_x = hip.x - shoulder.x
        torso_y = hip.y - shoulder.y
        
        # Ángulo entre vectores
        dot = arm_x * torso_x + arm_y * torso_y
        mag_arm = math.sqrt(arm_x**2 + arm_y**2)
        mag_torso = math.sqrt(torso_x**2 + torso_y**2)
        
        if mag_arm == 0 or mag_torso == 0:
            return 0.0
        
        cos_angle = max(-1, min(1, dot / (mag_arm * mag_torso)))
        angle = math.degrees(math.acos(cos_angle))
        
        return angle

    def get_current_data(self) -> Dict[str, Any]:
        """
        Retorna datos BILATERALES para el frontend.
        
        ⚠️ IMPORTANTE: Debe incluir TANTO campos bilaterales como campos
        unificados para compatibilidad con analysis_session.py
        """
        return {
            # === DATOS BILATERALES ===
            'left_angle': round(self.left_angle, 1),
            'right_angle': round(self.right_angle, 1),
            'left_max_rom': round(self.left_max_rom, 1),
            'right_max_rom': round(self.right_max_rom, 1),
            'asymmetry': round(self.asymmetry, 1),
            
            # === CAMPOS UNIFICADOS (compatibilidad) ===
            # Usar promedio o lado dominante
            'angle': round((self.left_angle + self.right_angle) / 2, 1),
            'max_rom': round(max(self.left_max_rom, self.right_max_rom), 1),
            
            # === IDENTIFICADORES ===
            'side': 'bilateral',  # SIEMPRE bilateral
            'is_bilateral': True,
            
            # === ESTADO ===
            'is_frontal': self.is_frontal_position,
            'frontal_quality': round(self.frontal_quality, 2),
            'landmarks_detected': self.landmarks_detected,
            'posture_valid': self.posture_valid,
        }

    def reset(self):
        """Reset para nueva medición."""
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_max_rom = 0.0
        self.right_max_rom = 0.0
        self.asymmetry = 0.0
        self._frontal_history.clear()
```

---

### 📁 ARCHIVO 3: Configuración de Ejercicios (`app/routes/main.py`)

**Propósito:** Definir TODOS los ejercicios disponibles con su configuración completa

```python
# exercises_db - Base de datos de ejercicios
exercises_db = {
    'shoulder': {
        'flexion': {
            'name': 'Flexión de Hombro',
            'description': 'Evalúa la capacidad de elevar el brazo hacia adelante',
            'camera_view': 'profile',           # 'profile' o 'frontal'
            'camera_view_label': 'Perfil',      # Para mostrar en UI
            'min_angle': 0,
            'max_angle': 180,
            'analyzer_type': 'shoulder_profile', # Clave para video_feed
            'instructions': [
                'Colócate de lado a la cámara',
                'Mantén el brazo extendido',
                'Eleva el brazo hacia adelante lentamente'
            ],
            'setup': {
                'initial_position': 'Brazo al costado del cuerpo',
                'movement': 'Elevación anterior del brazo',
                'final_position': 'Brazo apuntando hacia arriba'
            }
        },
        'extension': {
            'name': 'Extensión de Hombro',
            'description': 'Evalúa la capacidad de mover el brazo hacia atrás',
            'camera_view': 'profile',
            'camera_view_label': 'Perfil',
            'min_angle': 0,
            'max_angle': 60,
            'analyzer_type': 'shoulder_profile',
            'instructions': [
                'Colócate de lado a la cámara',
                'Mantén el brazo extendido',
                'Lleva el brazo hacia atrás'
            ],
            'setup': {
                'initial_position': 'Brazo al costado del cuerpo',
                'movement': 'Extensión posterior del brazo',
                'final_position': 'Brazo extendido hacia atrás'
            }
        },
        'abduction': {
            'name': 'Abducción de Hombro',
            'description': 'Evalúa la capacidad de elevar el brazo lateralmente',
            'camera_view': 'frontal',
            'camera_view_label': 'Frontal',
            'min_angle': 0,
            'max_angle': 180,
            'analyzer_type': 'shoulder_frontal',  # Analyzer frontal/bilateral
            'instructions': [
                'Colócate de frente a la cámara',
                'Brazos a los costados',
                'Eleva ambos brazos lateralmente'
            ],
            'setup': {
                'initial_position': 'Brazos pegados al cuerpo',
                'movement': 'Elevación lateral de ambos brazos',
                'final_position': 'Brazos en posición de T o más arriba'
            }
        }
    },
    
    # === OTROS SEGMENTOS (IMPLEMENTAR) ===
    'elbow': {
        'flexion': {
            'name': 'Flexión de Codo',
            'description': 'Evalúa la capacidad de doblar el codo',
            'camera_view': 'profile',
            'camera_view_label': 'Perfil',
            'min_angle': 0,
            'max_angle': 145,
            'analyzer_type': 'elbow_profile',  # Crear este analyzer
            'instructions': ['...'],
            'setup': {'...'}
        }
    },
    
    'knee': {
        'flexion': {
            'name': 'Flexión de Rodilla',
            'description': 'Evalúa la capacidad de doblar la rodilla',
            'camera_view': 'profile',
            'camera_view_label': 'Perfil',
            'min_angle': 0,
            'max_angle': 135,
            'analyzer_type': 'knee_profile',  # Crear este analyzer
            'instructions': ['...'],
            'setup': {'...'}
        }
    },
    
    # ... más segmentos
}
```

---

### 📁 ARCHIVO 4: Video Feed (`app/routes/api.py`)

**Propósito:** Registrar analyzers y servir stream MJPEG

```python
# Diccionario de clases de analyzers disponibles
analyzer_classes = {
    'shoulder_profile': ShoulderProfileAnalyzer,
    'shoulder_frontal': ShoulderFrontalAnalyzer,
    # === AGREGAR NUEVOS AQUÍ ===
    # 'elbow_profile': ElbowProfileAnalyzer,
    # 'knee_profile': KneeProfileAnalyzer,
    # 'hip_profile': HipProfileAnalyzer,
    # 'hip_frontal': HipFrontalAnalyzer,
    # 'ankle_profile': AnkleProfileAnalyzer,
    # 'ankle_frontal': AnkleFrontalAnalyzer,
}

@api_bp.route('/video_feed')
def video_feed():
    """Stream MJPEG con procesamiento de frame."""
    analyzer_type = request.args.get('analyzer', 'shoulder_profile')
    
    # Obtener clase del analyzer
    AnalyzerClass = analyzer_classes.get(analyzer_type, ShoulderProfileAnalyzer)
    
    # Crear instancia
    analyzer = AnalyzerClass(processing_width=960, processing_height=540)
    
    # Guardar referencia para polling
    analysis_session.set_current_analyzer(analyzer)
    
    def generate_frames():
        with camera_manager.get_camera() as camera:
            while True:
                success, frame = camera.read()
                if not success:
                    continue
                
                # Procesar frame con analyzer
                processed_frame = analyzer.process_frame(frame)
                
                # Codificar a JPEG
                _, buffer = cv2.imencode('.jpg', processed_frame, 
                                        [cv2.IMWRITE_JPEG_QUALITY, 60])
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + 
                       buffer.tobytes() + b'\r\n')
    
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/analysis/current_data')
def get_current_data():
    """Endpoint de polling para datos actuales."""
    analyzer = analysis_session.get_current_analyzer()
    if analyzer:
        return jsonify(analyzer.get_current_data())
    return jsonify({'error': 'No analyzer active'})
```

---

### 📁 ARCHIVO 5: Frontend JavaScript (`app/static/js/live_analysis.js`)

**Fragmentos clave que manejan los datos:**

```javascript
class LiveAnalysisController {
    constructor(config) {
        this.config = config;
        this.isAnalyzing = false;
        this.pollingInterval = null;
        
        // ⚠️ CRÍTICO: Guardar lado del polling (no del session stop)
        this.lastDetectedSide = null;
    }
    
    // Actualizar UI con datos del polling
    updateUI(data) {
        // Actualizar displays de ángulo
        if (data.is_bilateral) {
            // UI bilateral
            this.updateBilateralDisplay(data);
        } else {
            // UI unilateral
            document.getElementById('currentAngle').textContent = 
                `${data.angle.toFixed(1)}°`;
            document.getElementById('maxRom').textContent = 
                `${data.max_rom.toFixed(1)}°`;
            
            // Mostrar lado
            if (data.side_display) {
                document.getElementById('sideIndicator').textContent = 
                    data.side_display;
            }
        }
        
        // ⚠️ GUARDAR LADO DEL POLLING (mismo que se muestra en UI)
        this.lastDetectedSide = data.side;
    }
    
    // Guardar resultados
    async saveResults() {
        const sessionData = this.sessionData;
        const finalData = this.finalData;
        
        // ⚠️ USAR LADO DEL POLLING, no del finalData
        const sideToSave = this.lastDetectedSide || finalData.side || 'unknown';
        
        const saveData = {
            segment: this.config.segment,
            exercise_type: this.config.exerciseType,
            camera_view: this.config.cameraView,
            side: sideToSave,  // ✅ Lado correcto
            rom_value: finalData.max_rom,
            left_rom: finalData.left_max_rom || null,
            right_rom: finalData.right_max_rom || null,
            classification: this.classifyROM(finalData.max_rom),
            quality_score: finalData.orientation_quality || 1.0,
            duration: sessionData.duration,
            notes: ''
        };
        
        const response = await fetch('/api/analysis/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(saveData)
        });
        
        // Actualizar historial en UI
        if (response.ok) {
            this.loadRecentHistory();
        }
    }
}
```

---

## 📌 CHECKLIST PARA IMPLEMENTAR NUEVO SEGMENTO

### Ejemplo: Implementar segmento "Codo"

#### 1. Crear Analyzer
**Archivo:** `app/analyzers/elbow_profile.py`

- [ ] Copiar estructura de `shoulder_profile.py`
- [ ] Cambiar nombre de clase a `ElbowProfileAnalyzer`
- [ ] Usar `self.pose = get_shared_pose()` (NO crear instancia nueva)
- [ ] Modificar `calculate_extension_angle()` para usar landmarks de codo:
  - Hombro (11/12) → punto superior
  - Codo (13/14) → punto central (vértice del ángulo)
  - Muñeca (15/16) → punto inferior
- [ ] Adaptar `detect_side()` si la lógica de detección es diferente
- [ ] Implementar `get_current_data()` con TODOS los campos requeridos

#### 2. Registrar en Imports
**Archivo:** `app/analyzers/__init__.py`

```python
from .elbow_profile import ElbowProfileAnalyzer
```

#### 3. Agregar a Video Feed
**Archivo:** `app/routes/api.py`

```python
analyzer_classes = {
    'shoulder_profile': ShoulderProfileAnalyzer,
    'shoulder_frontal': ShoulderFrontalAnalyzer,
    'elbow_profile': ElbowProfileAnalyzer,  # ← AGREGAR
}
```

#### 4. Agregar Configuración de Ejercicio
**Archivo:** `app/routes/main.py`

```python
exercises_db = {
    # ... existentes ...
    'elbow': {
        'flexion': {
            'name': 'Flexión de Codo',
            'description': 'Evalúa rango de movimiento al doblar el codo',
            'camera_view': 'profile',
            'camera_view_label': 'Perfil',
            'min_angle': 0,
            'max_angle': 145,
            'analyzer_type': 'elbow_profile',
            'instructions': [
                'Colócate de lado a la cámara',
                'Mantén el brazo extendido',
                'Dobla el codo lentamente'
            ],
            'setup': {
                'initial_position': 'Brazo extendido',
                'movement': 'Flexión del codo',
                'final_position': 'Codo completamente doblado'
            }
        },
        'extension': {
            'name': 'Extensión de Codo',
            'description': 'Evalúa capacidad de extender el codo',
            'camera_view': 'profile',
            'camera_view_label': 'Perfil',
            'min_angle': 0,
            'max_angle': 0,  # Normalmente 0° es extensión completa
            'analyzer_type': 'elbow_profile',
            'instructions': ['...'],
            'setup': {'...'}
        }
    }
}
```

#### 5. Verificar
- [ ] Navegar al ejercicio desde el dropdown
- [ ] Verificar que el video feed funciona
- [ ] Verificar que el ángulo se calcula correctamente
- [ ] Verificar detección de lado (si aplica)
- [ ] Guardar en historial y verificar que se guarda correcto
- [ ] Cargar historial y verificar que se muestra

---

## 🔧 LANDMARKS DE MEDIAPIPE (REFERENCIA RÁPIDA)

```
Índice | Nombre           | Uso común
-------|------------------|----------------------------------
0      | nose             | Detección de orientación
11     | left_shoulder    | Hombro izquierdo
12     | right_shoulder   | Hombro derecho
13     | left_elbow       | Codo izquierdo
14     | right_elbow      | Codo derecho
15     | left_wrist       | Muñeca izquierda
16     | right_wrist      | Muñeca derecha
23     | left_hip         | Cadera izquierda
24     | right_hip        | Cadera derecha
25     | left_knee        | Rodilla izquierda
26     | right_knee       | Rodilla derecha
27     | left_ankle       | Tobillo izquierdo
28     | right_ankle      | Tobillo derecho
29     | left_heel        | Talón izquierdo
30     | right_heel       | Talón derecho
31     | left_foot_index  | Punta pie izquierdo
32     | right_foot_index | Punta pie derecho
```

### Combinaciones por Segmento

| Segmento | Perfil (3 puntos) | Comentario |
|----------|-------------------|------------|
| Hombro | Cadera→Hombro→Codo | Ángulo hombro vs vertical |
| Codo | Hombro→Codo→Muñeca | Ángulo flexión codo |
| Cadera | Hombro→Cadera→Rodilla | Ángulo flexión cadera |
| Rodilla | Cadera→Rodilla→Tobillo | Ángulo flexión rodilla |
| Tobillo | Rodilla→Tobillo→Punta | Ángulo dorsiflexión |

---

## 🎨 VISUALIZACIÓN EN VIDEO - DETALLES CRÍTICOS

### 1. Símbolo de Grados (° → o superíndice)

**Problema:** OpenCV no puede renderizar el símbolo `°` correctamente con las fuentes por defecto. Aparece como `?`.

**Solución:** Dibujar el número y luego una `o` pequeña en posición elevada (superíndice simulado).

```python
# ❌ INCORRECTO - No funciona en OpenCV
angle_text = f"{angle:.1f}°"
cv2.putText(image, angle_text, ...)  # Muestra "45.2?"

# ✅ CORRECTO - Simular superíndice con 'o'
angle_text = f"{angle:.1f}"
cv2.putText(image, angle_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

# Calcular posición para la 'o' (después del número, más arriba)
(text_width, _), _ = cv2.getTextSize(angle_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
cv2.putText(
    image,
    "o",
    (x + text_width + 2, y - 15),  # Desplazado arriba
    cv2.FONT_HERSHEY_SIMPLEX,
    0.5,  # Tamaño más pequeño
    color,
    2
)
```

**Ejemplo completo en analyzer:**
```python
def _draw_angle_on_frame(self, image, angle, position, color):
    """Dibuja ángulo con símbolo de grados correcto."""
    x, y = position
    angle_text = f"{abs(angle):.1f}"
    
    # Dibujar número
    cv2.putText(
        image, angle_text, (x, y),
        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3, cv2.LINE_4
    )
    
    # Dibujar 'o' como símbolo de grados (superíndice)
    (text_width, _), _ = cv2.getTextSize(
        angle_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3
    )
    cv2.putText(
        image, "o",
        (x + text_width + 2, y - 15),  # Posición elevada
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_4
    )
```

### 2. Overlays de Información - DESHABILITADOS

Los analyzers tienen métodos para dibujar paneles de información sobre el video, pero están **DESHABILITADOS** porque la información ya se muestra en el panel web "Datos en Tiempo Real".

**Métodos comentados (NO eliminar, solo comentar la llamada):**

```python
# En _process_profile_view() o _process_frontal_view():

# Panel de información en video (DESHABILITADO - info ya visible en panel web)
# self._draw_info_panel(image, orientation, confidence, w, h)

# Barras de progreso para cada lado (DESHABILITADO - info ya visible en panel web)
# self._draw_rom_bars(image, w, h)

# Mostrar métricas en video (DESHABILITADO - info ya visible en panel web)
# self._draw_performance_metrics(image, fps, processing_time)
```

**⚠️ IMPORTANTE:** 
- Las funciones `_draw_info_panel()`, `_draw_rom_bars()`, `_draw_performance_metrics()` siguen existiendo
- Solo se comentan las **llamadas** a estas funciones
- Esto permite reactivarlas fácilmente si se necesitan en el futuro
- NO hay riesgo de hilos o procesos abiertos - son solo funciones de renderizado

### 3. Qué SÍ se dibuja en el video

Elementos que **SÍ** permanecen activos en el video:

| Elemento | Propósito | Ubicación |
|----------|-----------|-----------|
| Puntos clave (círculos) | Mostrar landmarks detectados | Sobre articulaciones |
| Líneas de referencia | Mostrar ejes del ángulo | Entre landmarks |
| Ángulo actual (número + °) | Feedback en tiempo real | Cerca del hombro |
| Indicador FLEX/EXT | Dirección del movimiento | Debajo del ángulo |
| Mensajes de estado | "Colocate de PERFIL", etc. | Centro superior |

### 4. Colores Estándar

```python
# Colores definidos en analyzer (BGR para OpenCV)
self.color_cache = {
    'white': (255, 255, 255),      # Texto general
    'yellow': (0, 255, 255),        # Ángulo actual
    'orange': (0, 165, 255),        # Advertencias
    'green': (0, 255, 0),           # Éxito/Válido
    'red': (0, 0, 255),             # Error
    'cyan': (255, 255, 0),          # Lado izquierdo (bilateral)
    'purple': (255, 0, 127),        # Lado derecho (bilateral)
    'blue': (255, 0, 0),            # Líneas del brazo
    'magenta': (255, 0, 255),       # Puntos cadera
}
```

---

## 📊 MODAL DE RESULTADOS - BILATERAL

### Estructura del Modal para Análisis Frontal (Bilateral)

El modal muestra información diferente según si es análisis unilateral o bilateral:

**Unilateral (perfil):**
- ROM Máximo: X°
- Lado: Izquierdo/Derecho
- Clasificación: Normal/Limitado/etc.

**Bilateral (frontal):**
- ROM Máximo Izquierdo: X° [clasificación]
- ROM Máximo Derecho: X° [clasificación]
- Asimetría: X° [Normal/Leve/Significativa]
- Clasificación general: (basada en el mayor)

### Código del Modal (HTML)

```html
<!-- ROM para análisis bilateral (frontal) - oculto por defecto -->
<div id="bilateralResult" class="bilateral-results" style="display: none;">
    <div class="result-item highlight-item">
        <span class="result-label">ROM Máximo Izquierdo:</span>
        <span id="leftROM" class="result-value highlight" style="color: #00d4ff;">0°</span>
        <span id="leftClassification" class="badge bg-secondary ms-2">-</span>
    </div>
    <div class="result-item highlight-item">
        <span class="result-label">ROM Máximo Derecho:</span>
        <span id="rightROM" class="result-value highlight" style="color: #ff00ff;">0°</span>
        <span id="rightClassification" class="badge bg-secondary ms-2">-</span>
    </div>
    <div class="result-item">
        <span class="result-label">Asimetría:</span>
        <span id="asymmetryValue" class="result-value">0°</span>
        <span id="asymmetryBadge" class="badge bg-success ms-2">Normal</span>
    </div>
</div>
```

### Lógica de Asimetría (JavaScript)

```javascript
// En showResults() de LiveAnalysisController
if (isBilateral && finalData.left_max_rom !== null && finalData.right_max_rom !== null) {
    // Mostrar resultados bilaterales
    unilateralResult.style.display = 'none';
    bilateralResult.style.display = 'block';
    
    // ROM de cada lado
    document.getElementById('leftROM').textContent = `${finalData.left_max_rom.toFixed(1)}°`;
    document.getElementById('rightROM').textContent = `${finalData.right_max_rom.toFixed(1)}°`;
    
    // Clasificación INDIVIDUAL para cada lado
    const leftClass = this.classifyROM(finalData.left_max_rom);
    const rightClass = this.classifyROM(finalData.right_max_rom);
    
    document.getElementById('leftClassification').textContent = leftClass.label;
    document.getElementById('leftClassification').className = 'badge ms-2 ' + leftClass.class;
    
    document.getElementById('rightClassification').textContent = rightClass.label;
    document.getElementById('rightClassification').className = 'badge ms-2 ' + rightClass.class;
    
    // Calcular y mostrar asimetría
    const asymmetry = Math.abs(finalData.left_max_rom - finalData.right_max_rom);
    document.getElementById('asymmetryValue').textContent = `${asymmetry.toFixed(1)}°`;
    
    // Clasificar asimetría
    const asymmetryBadge = document.getElementById('asymmetryBadge');
    if (asymmetry < 10) {
        asymmetryBadge.textContent = 'Normal';
        asymmetryBadge.className = 'badge ms-2 bg-success';
    } else if (asymmetry < 20) {
        asymmetryBadge.textContent = 'Leve';
        asymmetryBadge.className = 'badge ms-2 bg-warning';
    } else {
        asymmetryBadge.textContent = 'Significativa';
        asymmetryBadge.className = 'badge ms-2 bg-danger';
    }
}
```

### Umbrales de Asimetría

| Diferencia | Clasificación | Color | Significado Clínico |
|------------|---------------|-------|---------------------|
| < 10° | Normal | 🟢 Verde | Dentro de variabilidad normal |
| 10-20° | Leve | 🟡 Amarillo | Monitorear, posible compensación |
| > 20° | Significativa | 🔴 Rojo | Requiere evaluación detallada |

---

## 🔄 VERSIONADO DE JAVASCRIPT

Para forzar que el navegador recargue el JavaScript después de cambios:

```html
<!-- En live_analysis.html -->
<!-- Actualizar versión cada vez que se modifica live_analysis.js -->
<script src="{{ url_for('static', filename='js/live_analysis.js') }}?v=3.2"></script>
```

**Historial de versiones:**
| Versión | Cambios |
|---------|---------|
| v3.0 | Sistema de estados, overlay dinámico |
| v3.1 | Protección anti-duplicados toast, blur removido |
| v3.2 | Asimetría en modal bilateral, clasificación por lado |


