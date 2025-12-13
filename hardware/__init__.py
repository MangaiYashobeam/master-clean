"""
🔧 HARDWARE MODULE - Gestión de Hardware del Sistema BIOTRACK
==============================================================
Módulos para control de cámara web, motor de altura y dispositivos físicos.

COMPONENTES:
- camera_manager: Acceso exclusivo y thread-safe a la cámara web (singleton)
- camera_controller: Control de altura de cámara (orquesta Arduino + Drillis-Contini)
- arduino_serial: Comunicación serial thread-safe con Arduino Nano
- drillis_contini: Cálculos de proporciones corporales antropométricas

USO BÁSICO:
    from hardware import (
        # Control de altura de cámara
        move_camera_for_segment,
        get_camera_status,
        set_temporary_height,
        get_effective_height,
        
        # Gestión de cámara web
        camera_manager
    )
    
    # Establecer altura temporal para pruebas
    set_temporary_height(175)  # 175 cm
    
    # Mover cámara para análisis de hombro
    result = move_camera_for_segment('shoulder', 175)
    if result.success:
        print(f"Cámara en {result.current_height_mm}mm")

Autor: BIOTRACK Team
Fecha: 2025-12-01
"""

# ============================================================================
# GESTIÓN DE CÁMARA WEB
# ============================================================================

from .camera_manager import (
    camera_manager,
    CameraManager,
    check_camera_availability,
    get_camera_info
)

# ============================================================================
# CONTROL DE ALTURA DE CÁMARA (API Principal)
# ============================================================================

from .camera_controller import (
    # Funciones principales de movimiento
    move_camera_for_segment,
    calculate_height_for_segment,
    get_camera_status,
    connect_arduino,
    disconnect_arduino,
    stop_camera_movement,
    go_to_initial_position,
    
    # Información para UI
    get_segment_info_for_ui,
    get_all_segments_info_for_ui,
    
    # Sistema de altura temporal (override sin modificar BD)
    set_temporary_height,
    get_effective_height,
    clear_temporary_height,
    has_temporary_height,
    get_temporary_height,
    
    # Clases de resultado
    CameraMoveResult
)

# ============================================================================
# CÁLCULOS DRILLIS-CONTINI (uso directo si se necesita)
# ============================================================================

from .drillis_contini import (
    # Funciones de cálculo
    calculate_segment_height,
    calculate_camera_height,
    get_all_segment_heights,
    get_segment_name_es,
    get_available_segments,
    
    # Constantes
    SEGMENT_PROPORTIONS,
    SEGMENT_NAMES_ES,
    CAMERA_MIN_HEIGHT_MM,
    CAMERA_MAX_HEIGHT_MM,
    
    # Clases
    SegmentHeightResult
)

# ============================================================================
# COMUNICACIÓN SERIAL (uso interno, pero exportado para debugging/testing)
# ============================================================================

from .arduino_serial import (
    arduino_serial,
    ArduinoSerial,
    ArduinoStatus,
    ArduinoResponse
)

# ============================================================================
# EXPORTS PÚBLICOS
# ============================================================================

__all__ = [
    # === Camera Manager (cámara web) ===
    'camera_manager',
    'CameraManager', 
    'check_camera_availability',
    'get_camera_info',
    
    # === Camera Controller (altura de cámara) ===
    'move_camera_for_segment',
    'calculate_height_for_segment',
    'get_camera_status',
    'connect_arduino',
    'disconnect_arduino',
    'stop_camera_movement',
    'go_to_initial_position',
    'get_segment_info_for_ui',
    'get_all_segments_info_for_ui',
    
    # === Altura temporal ===
    'set_temporary_height',
    'get_effective_height',
    'clear_temporary_height',
    'has_temporary_height',
    'get_temporary_height',
    'CameraMoveResult',
    
    # === Drillis-Contini ===
    'calculate_segment_height',
    'calculate_camera_height',
    'get_all_segment_heights',
    'get_segment_name_es',
    'get_available_segments',
    'SEGMENT_PROPORTIONS',
    'SEGMENT_NAMES_ES',
    'CAMERA_MIN_HEIGHT_MM',
    'CAMERA_MAX_HEIGHT_MM',
    'SegmentHeightResult',
    
    # === Arduino Serial ===
    'arduino_serial',
    'ArduinoSerial',
    'ArduinoStatus',
    'ArduinoResponse',
]
