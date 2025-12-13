"""
🔌 API HARDWARE - Endpoints REST para Control de Hardware
==========================================================
Endpoints para control de altura de cámara y configuración de altura de usuario.

ENDPOINTS DISPONIBLES:
- GET  /api/hardware/user-height        → Obtener altura efectiva del usuario
- POST /api/hardware/user-height        → Establecer altura temporal
- POST /api/hardware/user-height/reset  → Restaurar altura de BD

- GET  /api/hardware/camera/status      → Estado del sistema de cámara
- POST /api/hardware/camera/connect     → Conectar con Arduino
- POST /api/hardware/camera/disconnect  → Desconectar de Arduino
- POST /api/hardware/camera/move        → Mover cámara a altura de segmento
- POST /api/hardware/camera/stop        → Detener motor
- POST /api/hardware/camera/home        → Ir a posición inicial

- GET  /api/hardware/camera/segment-info/<segment>  → Info de altura para segmento
- GET  /api/hardware/ports              → Listar puertos COM disponibles

Autor: BIOTRACK Team
Fecha: 2025-12-01
"""

from flask import Blueprint, jsonify, request, session, current_app
import logging

# Importar desde el módulo hardware
from hardware import (
    # Control de cámara
    move_camera_for_segment,
    get_camera_status,
    connect_arduino,
    disconnect_arduino,
    stop_camera_movement,
    go_to_initial_position,
    get_segment_info_for_ui,
    get_all_segments_info_for_ui,
    
    # Altura temporal
    set_temporary_height,
    get_effective_height,
    clear_temporary_height,
    has_temporary_height,
    
    # Arduino serial (para listar puertos)
    arduino_serial
)

logger = logging.getLogger(__name__)

# Crear Blueprint
api_hardware_bp = Blueprint('api_hardware', __name__, url_prefix='/api/hardware')


# ============================================================================
# DECORADOR SIMPLE DE AUTENTICACIÓN
# ============================================================================

def login_required_api(f):
    """
    Decorador para verificar autenticación en endpoints de API.
    Retorna JSON 401 si no está autenticado.
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Autenticación requerida'
            }), 401
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# HELPER PARA OBTENER ALTURA DEL USUARIO
# ============================================================================

def get_user_height_from_db():
    """
    Obtiene la altura del usuario actual desde la base de datos.
    Retorna 170 cm como valor por defecto si no se encuentra.
    """
    try:
        db_manager = current_app.config.get('DB_MANAGER')
        if db_manager:
            user_id = session.get('user_id')
            if user_id:
                user = db_manager.get_user_by_id(user_id)
                if user and user.height:
                    return float(user.height)
        return 170.0  # Valor por defecto
    except Exception as e:
        logger.error(f"Error obteniendo altura de usuario: {e}")
        return 170.0


# ============================================================================
# ENDPOINTS DE ALTURA DE USUARIO
# ============================================================================

@api_hardware_bp.route('/user-height', methods=['GET'])
@login_required_api
def get_user_height():
    """
    Obtiene la altura efectiva del usuario (temporal o de BD).
    
    Response:
        {
            "success": true,
            "height_cm": 175.0,
            "is_temporary": true,
            "db_height_cm": 170.0
        }
    """
    try:
        db_height = get_user_height_from_db()
        effective_height, is_temporary = get_effective_height(db_height)
        
        return jsonify({
            'success': True,
            'height_cm': effective_height,
            'is_temporary': is_temporary,
            'db_height_cm': db_height
        })
    except Exception as e:
        logger.error(f"Error en get_user_height: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/user-height', methods=['POST'])
@login_required_api
def set_user_height():
    """
    Establece una altura temporal para la sesión actual.
    No modifica la base de datos.
    
    Request Body:
        {"height_cm": 175.0}
        
    Response:
        {
            "success": true,
            "message": "Altura temporal establecida: 175.0cm",
            "height_cm": 175.0,
            "is_temporary": true
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'height_cm' not in data:
            return jsonify({
                'success': False,
                'message': 'Se requiere height_cm en el body'
            }), 400
        
        try:
            height_cm = float(data['height_cm'])
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'height_cm debe ser un número'
            }), 400
        
        if set_temporary_height(height_cm):
            logger.info(f"Usuario {session.get('user_id')} estableció altura temporal: {height_cm}cm")
            return jsonify({
                'success': True,
                'message': f'Altura temporal establecida: {height_cm}cm',
                'height_cm': height_cm,
                'is_temporary': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Altura fuera de rango válido (100-250 cm)'
            }), 400
            
    except Exception as e:
        logger.error(f"Error en set_user_height: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/user-height/reset', methods=['POST'])
@login_required_api
def reset_user_height():
    """
    Elimina la altura temporal, volviendo a usar la de BD.
    
    Response:
        {
            "success": true,
            "message": "Altura restaurada al valor de la base de datos",
            "height_cm": 170.0,
            "is_temporary": false
        }
    """
    try:
        clear_temporary_height()
        db_height = get_user_height_from_db()
        
        logger.info(f"Usuario {session.get('user_id')} restauró altura de BD: {db_height}cm")
        return jsonify({
            'success': True,
            'message': 'Altura restaurada al valor de la base de datos',
            'height_cm': db_height,
            'is_temporary': False
        })
    except Exception as e:
        logger.error(f"Error en reset_user_height: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# ENDPOINTS DE CONTROL DE CÁMARA
# ============================================================================

@api_hardware_bp.route('/camera/status', methods=['GET'])
@login_required_api
def camera_status():
    """
    Obtiene el estado actual del sistema de cámara.
    
    Response:
        {
            "success": true,
            "arduino_connected": true,
            "current_height_mm": 1200,
            "current_height_cm": 120.0,
            "status": "ok",
            "status_code": 0,
            "available_ports": [{"port": "COM5", "description": "..."}]
        }
    """
    try:
        status = get_camera_status()
        return jsonify({
            'success': True,
            **status
        })
    except Exception as e:
        logger.error(f"Error en camera_status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/camera/connect', methods=['POST'])
@login_required_api
def camera_connect():
    """
    Conecta con el Arduino.
    
    Request Body (opcional):
        {"port": "COM5"}
        
    Response:
        {
            "success": true,
            "message": "Conectado en COM5"
        }
    """
    try:
        data = request.get_json() or {}
        port = data.get('port')
        
        success, message = connect_arduino(port)
        
        if success:
            logger.info(f"Usuario {session.get('user_id')} conectó Arduino: {message}")
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Error en camera_connect: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/camera/disconnect', methods=['POST'])
@login_required_api
def camera_disconnect():
    """
    Desconecta del Arduino.
    
    Response:
        {
            "success": true,
            "message": "Desconectado correctamente"
        }
    """
    try:
        success, message = disconnect_arduino()
        
        if success:
            logger.info(f"Usuario {session.get('user_id')} desconectó Arduino")
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Error en camera_disconnect: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/camera/move', methods=['POST'])
@login_required_api
def camera_move():
    """
    Mueve la cámara a la altura apropiada para un segmento.
    Usa la altura efectiva del usuario (temporal o BD).
    
    Request Body:
        {"segment": "shoulder"}
        
    Response:
        {
            "success": true,
            "message": "Cámara posicionada a 1432mm para análisis de Hombro",
            "target_height_mm": 1432,
            "current_height_mm": 1432,
            "segment": "shoulder",
            "segment_name": "Hombro",
            "user_height_cm": 175.0,
            "is_height_temporary": false,
            "arduino_connected": true
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'segment' not in data:
            return jsonify({
                'success': False,
                'message': 'Se requiere segment en el body'
            }), 400
        
        segment = data['segment']
        
        # Obtener altura efectiva
        db_height = get_user_height_from_db()
        user_height, is_temporary = get_effective_height(db_height)
        
        # Mover cámara (auto_connect=False para NO reconectar automáticamente,
        # el usuario debe conectar manualmente primero)
        result = move_camera_for_segment(segment, user_height, auto_connect=False)
        
        logger.info(
            f"Usuario {session.get('user_id')} movió cámara para {segment}: "
            f"target={result.target_height_mm}mm, actual={result.current_height_mm}mm, "
            f"success={result.success}"
        )
        
        return jsonify({
            'success': result.success,
            'message': result.message,
            'target_height_mm': result.target_height_mm,
            'current_height_mm': result.current_height_mm,
            'segment': result.segment,
            'segment_name': result.segment_name_es,
            'user_height_cm': result.user_height_cm,
            'is_height_temporary': is_temporary,
            'arduino_connected': result.arduino_connected
        })
        
    except Exception as e:
        logger.error(f"Error en camera_move: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/camera/stop', methods=['POST'])
@login_required_api
def camera_stop():
    """
    Detiene el movimiento de la cámara INMEDIATAMENTE.
    
    CRÍTICO: No usa verificaciones que bloqueen - envía STOP directo.
    """
    try:
        # Enviar STOP directamente - sin verificar conexión con lock
        response = arduino_serial.stop()
        
        logger.info(f"Usuario {session.get('user_id')} - STOP: success={response.success}")
        
        return jsonify({
            'success': response.success,
            'message': 'Motor detenido' if response.success else (response.error_message or 'Error'),
            'current_height_mm': response.current_height_mm
        })
    except Exception as e:
        logger.error(f"Error en camera_stop: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/camera/home', methods=['POST'])
@login_required_api
def camera_home():
    """
    Mueve la cámara a la posición inicial (mínima).
    
    Response:
        {
            "success": true,
            "message": "Cámara en posición inicial",
            "current_height_mm": 200
        }
    """
    try:
        result = go_to_initial_position()
        
        if result.success:
            logger.info(f"Usuario {session.get('user_id')} envió cámara a posición inicial")
        
        return jsonify({
            'success': result.success,
            'message': result.message,
            'current_height_mm': result.current_height_mm
        })
    except Exception as e:
        logger.error(f"Error en camera_home: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# ENDPOINTS DE INFORMACIÓN
# ============================================================================

@api_hardware_bp.route('/camera/segment-info/<segment>', methods=['GET'])
@login_required_api
def segment_info(segment):
    """
    Obtiene información de altura calculada para un segmento sin mover la cámara.
    
    Response:
        {
            "success": true,
            "segment": "shoulder",
            "segment_name": "Hombro",
            "user_height_cm": 175.0,
            "calculated_height_mm": 1432,
            "calculated_height_cm": 143.2,
            "is_reachable": true,
            "is_height_temporary": false,
            "db_height_cm": 175.0
        }
    """
    try:
        db_height = get_user_height_from_db()
        user_height, is_temporary = get_effective_height(db_height)
        
        info = get_segment_info_for_ui(segment, user_height)
        info['is_height_temporary'] = is_temporary
        info['db_height_cm'] = db_height
        
        return jsonify({
            'success': True,
            **info
        })
    except Exception as e:
        logger.error(f"Error en segment_info: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/camera/all-segments', methods=['GET'])
@login_required_api
def all_segments_info():
    """
    Obtiene información de todos los segmentos para el usuario actual.
    
    Response:
        {
            "success": true,
            "user_height_cm": 175.0,
            "is_temporary": false,
            "segments": {
                "shoulder": {"name_es": "Hombro", "height_mm": 1432, ...},
                ...
            }
        }
    """
    try:
        db_height = get_user_height_from_db()
        user_height, is_temporary = get_effective_height(db_height)
        
        segments = get_all_segments_info_for_ui(user_height)
        
        return jsonify({
            'success': True,
            'user_height_cm': user_height,
            'is_temporary': is_temporary,
            'segments': segments
        })
    except Exception as e:
        logger.error(f"Error en all_segments_info: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_hardware_bp.route('/ports', methods=['GET'])
@login_required_api
def list_ports():
    """
    Lista los puertos COM disponibles en el sistema.
    
    Response:
        {
            "success": true,
            "ports": [
                {"port": "COM5", "description": "Arduino Nano", "manufacturer": "..."}
            ]
        }
    """
    try:
        ports = arduino_serial.list_available_ports()
        
        return jsonify({
            'success': True,
            'ports': ports
        })
    except Exception as e:
        logger.error(f"Error en list_ports: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
