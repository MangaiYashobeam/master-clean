"""
📐 DRILLIS-CONTINI - Cálculo de Proporciones Corporales
========================================================
Implementación de las proporciones antropométricas de Drillis y Contini
para calcular la altura de segmentos corporales.

PROPÓSITO:
Este módulo calcula a qué altura debe posicionarse la cámara para que
esté perpendicular al segmento corporal que se va a medir, eliminando
así el error de perspectiva en la medición de ángulos.

Referencia: Drillis, R., & Contini, R. (1966). Body Segment Parameters.
            Technical Report 1166.03, School of Engineering and Science,
            New York University.

Autor: BIOTRACK Team
Fecha: 2025-12-01
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# RESULTADO DEL CÁLCULO
# ============================================================================

@dataclass(frozen=True)
class SegmentHeightResult:
    """Resultado del cálculo de altura de segmento"""
    segment_name: str
    user_height_cm: float
    proportion_ratio: float
    calculated_height_cm: float
    calculated_height_mm: int
    is_valid: bool
    error_message: Optional[str] = None


# ============================================================================
# CONSTANTES DE PROPORCIONES DRILLIS-CONTINI
# ============================================================================

# Proporciones de altura de articulación respecto a la estatura total
# Valores expresados como fracción de la altura total del sujeto de pie
# Medidos desde el suelo hasta el centro de la articulación
SEGMENT_PROPORTIONS = {
    'shoulder': 0.818,   # Altura del hombro (acromion) - ~81.8% de la estatura
    'elbow': 0.630,      # Altura del codo (olécranon) - ~63% de la estatura
    'hip': 0.530,        # Altura de la cadera (trocánter mayor) - ~53% de la estatura
    'knee': 0.285,       # Altura de la rodilla (línea articular) - ~28.5% de la estatura
    'ankle': 0.039,      # Altura del tobillo (maléolo lateral) - ~3.9% de la estatura
}

# Nombres en español para mostrar en la UI
SEGMENT_NAMES_ES = {
    'shoulder': 'Hombro',
    'elbow': 'Codo',
    'hip': 'Cadera',
    'knee': 'Rodilla',
    'ankle': 'Tobillo',
}

# Límites físicos del sistema de cámara motorizada (en mm)
CAMERA_MIN_HEIGHT_MM = 375   # 37.5 cm - Altura mínima del sistema (posición inicial)
CAMERA_MAX_HEIGHT_MM = 1700  # 170 cm - Altura máxima del sistema


# ============================================================================
# FUNCIONES DE CÁLCULO
# ============================================================================

def calculate_segment_height(
    segment: str, 
    user_height_cm: float
) -> SegmentHeightResult:
    """
    Calcula la altura del segmento corporal usando proporciones Drillis-Contini.
    
    La altura calculada representa la distancia desde el suelo hasta el centro
    de la articulación cuando la persona está de pie.
    
    Args:
        segment: Identificador del segmento ('shoulder', 'elbow', 'hip', 'knee', 'ankle')
        user_height_cm: Altura del usuario en centímetros
        
    Returns:
        SegmentHeightResult con todos los datos del cálculo
        
    Example:
        >>> result = calculate_segment_height('shoulder', 175)
        >>> print(result.calculated_height_cm)  # 143.15
        >>> print(result.calculated_height_mm)  # 1432
    """
    # Normalizar nombre del segmento
    segment_lower = segment.lower().strip()
    
    # Validar segmento reconocido
    if segment_lower not in SEGMENT_PROPORTIONS:
        return SegmentHeightResult(
            segment_name=segment,
            user_height_cm=user_height_cm,
            proportion_ratio=0.0,
            calculated_height_cm=0.0,
            calculated_height_mm=0,
            is_valid=False,
            error_message=f"Segmento '{segment}' no reconocido. Válidos: {list(SEGMENT_PROPORTIONS.keys())}"
        )
    
    # Validar altura del usuario (rango razonable: 100-250 cm)
    if not (100 <= user_height_cm <= 250):
        return SegmentHeightResult(
            segment_name=segment_lower,
            user_height_cm=user_height_cm,
            proportion_ratio=SEGMENT_PROPORTIONS[segment_lower],
            calculated_height_cm=0.0,
            calculated_height_mm=0,
            is_valid=False,
            error_message=f"Altura de usuario fuera de rango válido (100-250 cm): {user_height_cm}"
        )
    
    # Calcular altura del segmento
    ratio = SEGMENT_PROPORTIONS[segment_lower]
    height_cm = user_height_cm * ratio
    height_mm = int(round(height_cm * 10))  # Convertir cm a mm
    
    logger.debug(
        f"Cálculo Drillis-Contini: {segment_lower} = "
        f"{user_height_cm}cm × {ratio} = {height_cm:.2f}cm ({height_mm}mm)"
    )
    
    return SegmentHeightResult(
        segment_name=segment_lower,
        user_height_cm=user_height_cm,
        proportion_ratio=ratio,
        calculated_height_cm=round(height_cm, 2),
        calculated_height_mm=height_mm,
        is_valid=True
    )


def calculate_camera_height(
    segment: str, 
    user_height_cm: float
) -> tuple[int, bool, str]:
    """
    Calcula la altura de cámara necesaria, ajustada a los límites del sistema.
    
    Esta función toma en cuenta los límites físicos del sistema motorizado
    (200mm mínimo, 1700mm máximo) y retorna la altura alcanzable.
    
    Args:
        segment: Identificador del segmento
        user_height_cm: Altura del usuario en cm
        
    Returns:
        tuple: (altura_mm, es_alcanzable, mensaje)
        - altura_mm: Altura objetivo en milímetros
        - es_alcanzable: True si la altura está dentro del rango del sistema
        - mensaje: Descripción del resultado o error
        
    Example:
        >>> height, ok, msg = calculate_camera_height('shoulder', 180)
        >>> if ok:
        ...     print(f"Mover cámara a {height}mm")
        >>> else:
        ...     print(f"Advertencia: {msg}")
    """
    result = calculate_segment_height(segment, user_height_cm)
    
    if not result.is_valid:
        return 0, False, result.error_message or "Error desconocido en el cálculo"
    
    target_height_mm = result.calculated_height_mm
    
    # Verificar límites del sistema
    if target_height_mm < CAMERA_MIN_HEIGHT_MM:
        # El tobillo típicamente cae por debajo del mínimo
        logger.info(
            f"Altura calculada ({target_height_mm}mm) ajustada al mínimo del sistema ({CAMERA_MIN_HEIGHT_MM}mm)"
        )
        return CAMERA_MIN_HEIGHT_MM, True, (
            f"Altura ajustada al mínimo del sistema ({CAMERA_MIN_HEIGHT_MM}mm). "
            f"Altura ideal: {target_height_mm}mm"
        )
    
    if target_height_mm > CAMERA_MAX_HEIGHT_MM:
        # Hombro de personas muy altas puede exceder el máximo
        logger.warning(
            f"Altura requerida ({target_height_mm}mm) excede máximo del sistema ({CAMERA_MAX_HEIGHT_MM}mm)"
        )
        return CAMERA_MAX_HEIGHT_MM, False, (
            f"⚠️ Altura requerida ({target_height_mm}mm) excede el máximo del sistema ({CAMERA_MAX_HEIGHT_MM}mm). "
            f"Se usará la altura máxima disponible."
        )
    
    # Altura dentro del rango - todo OK
    return target_height_mm, True, "OK"


def get_all_segment_heights(user_height_cm: float) -> dict:
    """
    Calcula las alturas de todos los segmentos para un usuario.
    
    Útil para mostrar una tabla completa de alturas de cámara
    según el segmento que se vaya a analizar.
    
    Args:
        user_height_cm: Altura del usuario en cm
        
    Returns:
        dict: Diccionario con resultados para cada segmento
        
    Example:
        >>> heights = get_all_segment_heights(175)
        >>> for seg, info in heights.items():
        ...     print(f"{info['name_es']}: {info['height_cm']}cm")
    """
    results = {}
    
    for segment in SEGMENT_PROPORTIONS.keys():
        result = calculate_segment_height(segment, user_height_cm)
        camera_height, is_reachable, message = calculate_camera_height(segment, user_height_cm)
        
        results[segment] = {
            'name_es': SEGMENT_NAMES_ES[segment],
            'height_cm': result.calculated_height_cm,
            'height_mm': result.calculated_height_mm,
            'ratio': result.proportion_ratio,
            'camera_height_mm': camera_height,
            'is_reachable': is_reachable,
            'is_valid': result.is_valid,
            'message': message
        }
    
    return results


def get_segment_name_es(segment: str) -> str:
    """
    Obtiene el nombre en español del segmento.
    
    Args:
        segment: Identificador del segmento en inglés
        
    Returns:
        Nombre en español o el mismo nombre si no se encuentra
    """
    return SEGMENT_NAMES_ES.get(segment.lower().strip(), segment)


def get_available_segments() -> list[dict]:
    """
    Retorna lista de segmentos disponibles con su información.
    
    Returns:
        Lista de diccionarios con información de cada segmento
    """
    return [
        {
            'key': key,
            'name_es': SEGMENT_NAMES_ES[key],
            'ratio': ratio,
            'description': f"Altura: {ratio*100:.1f}% de la estatura"
        }
        for key, ratio in SEGMENT_PROPORTIONS.items()
    ]
