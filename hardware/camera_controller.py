"""
📹 CAMERA CONTROLLER - Control de Altura de Cámara
===================================================
Controlador de alto nivel que orquesta:
- Cálculos de altura con Drillis-Contini
- Comunicación con Arduino vía serial
- Sistema de altura temporal (override sin modificar BD)

Este es el módulo que deben usar las rutas de Flask y los templates.
Proporciona una API simple y segura para el control de altura de cámara.

CARACTERÍSTICAS:
- Integra cálculos antropométricos con control de hardware
- Sistema de altura temporal que prevalece sobre la BD (por sesión)
- No modifica la base de datos (la altura temporal se pierde al cerrar sesión)
- Thread-safe gracias al módulo arduino_serial subyacente
- Manejo robusto de errores y estados del Arduino

Autor: BIOTRACK Team
Fecha: 2025-12-01
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from flask import session

from .drillis_contini import (
    calculate_camera_height,
    calculate_segment_height,
    get_segment_name_es,
    get_all_segment_heights,
    SEGMENT_PROPORTIONS,
    SEGMENT_NAMES_ES,
    CAMERA_MIN_HEIGHT_MM,
    CAMERA_MAX_HEIGHT_MM
)
from .arduino_serial import arduino_serial, ArduinoResponse, ArduinoStatus

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES PARA SESIÓN
# ============================================================================

# Clave para guardar altura temporal en session de Flask
SESSION_HEIGHT_OVERRIDE_KEY = 'user_height_override_cm'


# ============================================================================
# RESULTADO DEL MOVIMIENTO DE CÁMARA
# ============================================================================

@dataclass
class CameraMoveResult:
    """Resultado completo de una operación de movimiento de cámara"""
    success: bool
    target_height_mm: int
    current_height_mm: int
    segment: str
    segment_name_es: str
    user_height_cm: float
    message: str
    arduino_connected: bool
    is_height_temporary: bool = False


# ============================================================================
# SISTEMA DE ALTURA TEMPORAL
# ============================================================================
# Permite al usuario especificar una altura diferente a la guardada en BD
# para las pruebas, sin modificar permanentemente su perfil.

def set_temporary_height(height_cm: float) -> bool:
    """
    Establece una altura temporal que prevalece sobre la de la BD.
    Esta altura se mantiene solo durante la sesión actual.
    
    IMPORTANTE: No modifica la base de datos.
    
    Args:
        height_cm: Altura en centímetros (100-250)
        
    Returns:
        bool: True si se guardó correctamente, False si está fuera de rango
        
    Example:
        >>> set_temporary_height(180.5)
        True
        >>> # Ahora todas las operaciones usarán 180.5cm en vez de la altura de BD
    """
    if not (100 <= height_cm <= 250):
        logger.warning(f"Altura temporal rechazada (fuera de rango 100-250): {height_cm}cm")
        return False
    
    session[SESSION_HEIGHT_OVERRIDE_KEY] = float(height_cm)
    logger.info(f"Altura temporal establecida: {height_cm}cm")
    return True


def get_effective_height(db_height_cm: float) -> Tuple[float, bool]:
    """
    Obtiene la altura efectiva a usar (temporal si existe, sino de BD).
    
    Args:
        db_height_cm: Altura almacenada en la base de datos
        
    Returns:
        tuple: (altura_efectiva_cm, es_temporal)
        
    Example:
        >>> set_temporary_height(175)
        >>> height, is_temp = get_effective_height(170)
        >>> print(height, is_temp)
        175.0 True
    """
    temp_height = session.get(SESSION_HEIGHT_OVERRIDE_KEY)
    
    if temp_height is not None:
        logger.debug(f"Usando altura temporal: {temp_height}cm (BD: {db_height_cm}cm)")
        return float(temp_height), True
    
    return float(db_height_cm) if db_height_cm else 170.0, False


def clear_temporary_height() -> None:
    """
    Elimina la altura temporal, volviendo a usar la de BD.
    
    Example:
        >>> clear_temporary_height()
        >>> # Próximas operaciones usarán la altura de la BD
    """
    if SESSION_HEIGHT_OVERRIDE_KEY in session:
        del session[SESSION_HEIGHT_OVERRIDE_KEY]
        logger.info("Altura temporal eliminada - usando altura de BD")


def has_temporary_height() -> bool:
    """
    Verifica si hay una altura temporal establecida.
    
    Returns:
        bool: True si existe altura temporal
    """
    return SESSION_HEIGHT_OVERRIDE_KEY in session


def get_temporary_height() -> Optional[float]:
    """
    Obtiene la altura temporal si existe.
    
    Returns:
        float o None: Altura temporal en cm o None si no hay
    """
    return session.get(SESSION_HEIGHT_OVERRIDE_KEY)


# ============================================================================
# CÁLCULO DE ALTURA
# ============================================================================

def calculate_height_for_segment(
    segment: str,
    user_height_cm: float
) -> Tuple[int, bool, str]:
    """
    Calcula la altura de cámara necesaria para un segmento.
    
    Wrapper simple sobre drillis_contini.calculate_camera_height
    
    Args:
        segment: Identificador del segmento ('shoulder', 'elbow', etc.)
        user_height_cm: Altura del usuario en cm
        
    Returns:
        tuple: (altura_mm, es_alcanzable, mensaje)
    """
    return calculate_camera_height(segment, user_height_cm)


# ============================================================================
# CONTROL DE CÁMARA
# ============================================================================

def move_camera_for_segment(
    segment: str,
    user_height_cm: float,
    auto_connect: bool = False
) -> CameraMoveResult:
    """
    Mueve la cámara a la altura apropiada para analizar un segmento.
    
    Esta es la función principal que combina:
    1. Cálculo de altura con Drillis-Contini
    2. Validación de límites del sistema
    3. Comunicación con Arduino para mover el motor
    
    Args:
        segment: Segmento a analizar ('shoulder', 'elbow', 'hip', 'knee', 'ankle')
        user_height_cm: Altura del usuario en cm
        auto_connect: Si True, intenta conectar con Arduino si no está conectado
        
    Returns:
        CameraMoveResult con toda la información del resultado
        
    Example:
        >>> result = move_camera_for_segment('shoulder', 175)
        >>> if result.success:
        ...     print(f"Cámara en {result.current_height_mm}mm")
        >>> else:
        ...     print(f"Error: {result.message}")
    """
    segment_lower = segment.lower().strip()
    segment_name = get_segment_name_es(segment_lower)
    
    # 1. Calcular altura objetivo
    target_height_mm, is_reachable, calc_message = calculate_camera_height(segment_lower, user_height_cm)
    
    # Error en cálculo (segmento inválido, altura de usuario inválida, etc.)
    if target_height_mm == 0:
        return CameraMoveResult(
            success=False,
            target_height_mm=0,
            current_height_mm=0,
            segment=segment_lower,
            segment_name_es=segment_name,
            user_height_cm=user_height_cm,
            message=calc_message,
            arduino_connected=False
        )
    
    # 2. Verificar/establecer conexión con Arduino
    if not arduino_serial.is_connected():
        if auto_connect:
            connected, conn_message = arduino_serial.connect()
            if not connected:
                # No se pudo conectar - retornar info de cálculo sin movimiento
                return CameraMoveResult(
                    success=False,
                    target_height_mm=target_height_mm,
                    current_height_mm=0,
                    segment=segment_lower,
                    segment_name_es=segment_name,
                    user_height_cm=user_height_cm,
                    message=f"No se pudo conectar con Arduino: {conn_message}. Altura calculada: {target_height_mm}mm ({target_height_mm/10:.1f}cm)",
                    arduino_connected=False
                )
        else:
            return CameraMoveResult(
                success=False,
                target_height_mm=target_height_mm,
                current_height_mm=0,
                segment=segment_lower,
                segment_name_es=segment_name,
                user_height_cm=user_height_cm,
                message=f"Arduino no conectado. Altura calculada: {target_height_mm}mm ({target_height_mm/10:.1f}cm)",
                arduino_connected=False
            )
    
    # 3. Mover la cámara
    response = arduino_serial.move_to_height(target_height_mm)
    
    # 4. Construir mensaje de resultado
    if response.success:
        # Verificar si fue interrumpido por STOP
        if response.raw_response == "INTERRUPTED":
            message = f"Movimiento detenido en {response.current_height_mm}mm ({response.current_height_mm/10:.1f}cm)"
        else:
            message = f"Cámara posicionada a {response.current_height_mm}mm ({response.current_height_mm/10:.1f}cm) para análisis de {segment_name}"
            if not is_reachable:
                message += f" (ajustada desde {target_height_mm}mm ideal)"
    else:
        # Mensajes específicos según el código de error
        status_messages = {
            ArduinoStatus.HEIGHT_ERROR: "Error: altura fuera de rango del sistema",
            ArduinoStatus.LIMIT_SWITCH_ERROR: "Error: fin de carrera desconectado - verificar hardware",
            ArduinoStatus.TIMEOUT: "Error: timeout durante movimiento - motor puede estar trabado"
        }
        message = status_messages.get(
            response.status, 
            f"Error moviendo cámara: {response.error_message or 'desconocido'}"
        )
    
    return CameraMoveResult(
        success=response.success,
        target_height_mm=target_height_mm,
        current_height_mm=response.current_height_mm,
        segment=segment_lower,
        segment_name_es=segment_name,
        user_height_cm=user_height_cm,
        message=message,
        arduino_connected=True
    )


def get_camera_status() -> dict:
    """
    Obtiene el estado actual del sistema de cámara.
    
    Returns:
        dict con información completa del estado:
        - arduino_connected: bool
        - current_height_mm: int (0 si no conectado)
        - current_height_cm: float
        - status: str ('ok', 'moving', 'error', 'disconnected')
        - status_code: int (código del Arduino)
        - available_ports: list de puertos COM disponibles
    """
    is_connected = arduino_serial.is_connected()
    
    result = {
        'arduino_connected': is_connected,
        'current_height_mm': 0,
        'current_height_cm': 0.0,
        'status': 'disconnected',
        'status_code': -1,
        'available_ports': arduino_serial.list_available_ports()
    }
    
    if is_connected:
        response = arduino_serial.get_status()
        result['current_height_mm'] = response.current_height_mm
        result['current_height_cm'] = round(response.current_height_mm / 10, 1)
        result['status_code'] = response.status.value
        
        # Mapear código a estado legible
        status_map = {
            ArduinoStatus.OK: 'ok',
            ArduinoStatus.MOVING: 'moving',
            ArduinoStatus.HEIGHT_ERROR: 'error',
            ArduinoStatus.LIMIT_SWITCH_ERROR: 'error',
            ArduinoStatus.TIMEOUT: 'error'
        }
        result['status'] = status_map.get(response.status, 'unknown')
    
    return result


def connect_arduino(port: Optional[str] = None) -> Tuple[bool, str]:
    """
    Conecta con el Arduino.
    
    Args:
        port: Puerto COM (opcional, usa COM5 por defecto)
        
    Returns:
        tuple: (éxito, mensaje)
    """
    return arduino_serial.connect(port)


def disconnect_arduino() -> Tuple[bool, str]:
    """
    Desconecta del Arduino.
    
    Returns:
        tuple: (éxito, mensaje)
    """
    return arduino_serial.disconnect()


def stop_camera_movement() -> bool:
    """
    Detiene el movimiento de la cámara inmediatamente.
    
    Returns:
        bool: True si se detuvo correctamente
    """
    if not arduino_serial.is_connected():
        logger.warning("stop_camera_movement: Arduino no conectado")
        return False
    
    response = arduino_serial.stop()
    return response.success


def go_to_initial_position() -> CameraMoveResult:
    """
    Mueve la cámara a la posición inicial (altura mínima del sistema).
    
    Returns:
        CameraMoveResult con el resultado de la operación
    """
    if not arduino_serial.is_connected():
        return CameraMoveResult(
            success=False,
            target_height_mm=CAMERA_MIN_HEIGHT_MM,
            current_height_mm=0,
            segment='initial',
            segment_name_es='Posición Inicial',
            user_height_cm=0,
            message="Arduino no conectado",
            arduino_connected=False
        )
    
    response = arduino_serial.go_to_initial_position()
    
    return CameraMoveResult(
        success=response.success,
        target_height_mm=CAMERA_MIN_HEIGHT_MM,
        current_height_mm=response.current_height_mm,
        segment='initial',
        segment_name_es='Posición Inicial',
        user_height_cm=0,
        message="Cámara en posición inicial" if response.success else f"Error: {response.error_message}",
        arduino_connected=True
    )


# ============================================================================
# INFORMACIÓN PARA UI
# ============================================================================

def get_segment_info_for_ui(segment: str, user_height_cm: float) -> dict:
    """
    Obtiene información completa del segmento formateada para mostrar en UI.
    
    Esta función es la que debe usar el template para mostrar la información
    de altura calculada en el panel de control de cámara.
    
    Args:
        segment: Identificador del segmento
        user_height_cm: Altura del usuario en cm
        
    Returns:
        dict con información lista para templates:
        - segment: str (key)
        - segment_name: str (nombre en español)
        - user_height_cm: float
        - calculated_height_mm: int
        - calculated_height_cm: float
        - is_reachable: bool (si está dentro del rango del sistema)
        - min_height_cm: float (mínimo del sistema)
        - max_height_cm: float (máximo del sistema)
        - message: str (mensaje descriptivo o de advertencia)
        - proportion_ratio: float (proporción Drillis-Contini usada)
    """
    height_mm, is_reachable, message = calculate_camera_height(segment, user_height_cm)
    segment_result = calculate_segment_height(segment, user_height_cm)
    
    return {
        'segment': segment.lower().strip(),
        'segment_name': get_segment_name_es(segment),
        'user_height_cm': user_height_cm,
        'calculated_height_mm': height_mm,
        'calculated_height_cm': round(height_mm / 10, 1),
        'ideal_height_mm': segment_result.calculated_height_mm,
        'ideal_height_cm': segment_result.calculated_height_cm,
        'is_reachable': is_reachable,
        'min_height_cm': CAMERA_MIN_HEIGHT_MM / 10,
        'max_height_cm': CAMERA_MAX_HEIGHT_MM / 10,
        'message': message if message != "OK" else "",
        'proportion_ratio': segment_result.proportion_ratio
    }


def get_all_segments_info_for_ui(user_height_cm: float) -> dict:
    """
    Obtiene información de todos los segmentos para un usuario.
    
    Útil para mostrar una tabla comparativa de alturas de cámara.
    
    Args:
        user_height_cm: Altura del usuario en cm
        
    Returns:
        dict con información de cada segmento
    """
    return get_all_segment_heights(user_height_cm)
