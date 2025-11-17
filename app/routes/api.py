"""
🔌 BLUEPRINT DE API - BIOTRACK
===============================
Endpoints JSON para comunicación AJAX y REST

ENDPOINTS:
- /api/user/stats: Estadísticas del usuario
- /api/sessions/<id>: Obtener sesión ROM
- /api/subjects: CRUD de sujetos
- /api/rom-session: Crear/actualizar sesión ROM
- /api/video_feed: Stream MJPEG de video procesado (NUEVO)
- /api/analysis/start: Iniciar análisis (NUEVO)
- /api/analysis/stop: Detener análisis (NUEVO)
- /api/analysis/current_data: Obtener datos actuales (NUEVO)

Autor: BIOTRACK Team
Fecha: 2025-11-14
"""

from flask import (
    Blueprint, jsonify, request, session, current_app, Response
)
from app.routes.auth import login_required
from app.analyzers import ShoulderProfileAnalyzer, ShoulderFrontalAnalyzer
from app.core.client_frame_receiver import client_frame_receiver
import os
import cv2
import numpy as np
import logging
import time

# Crear blueprint
api_bp = Blueprint('api', __name__)

# Logger para uso fuera del contexto de Flask
logger = logging.getLogger(__name__)

# Variable global para el analyzer actual (compartida entre requests)
current_analyzer = None
last_processed_frame = None

ANALYZER_CLASS_MAP = {
    'shoulder_profile': ShoulderProfileAnalyzer,
    'shoulder_frontal': ShoulderFrontalAnalyzer,
}


def _ensure_analyzer(analyzer_type=None):
    """Crea (si es necesario) y retorna el analyzer activo."""
    global current_analyzer

    if analyzer_type is None:
        analyzer_type = session.get('analyzer_type')

    if not analyzer_type:
        raise ValueError('No hay analyzer asignado a la sesión')

    analyzer_class = ANALYZER_CLASS_MAP.get(analyzer_type)
    if analyzer_class is None:
        raise ValueError(f"Analyzer '{analyzer_type}' no implementado aún")

    if current_analyzer is None or type(current_analyzer) is not analyzer_class:
        if current_analyzer is not None:
            current_analyzer.cleanup()
        current_analyzer = analyzer_class(
            processing_width=640,
            processing_height=480,
            show_skeleton=False
        )
        logger.info("Analyzer '%s' inicializado", analyzer_type)

    return current_analyzer


def _process_frame_with_analyzer(frame, analyzer=None):
    """Procesa un frame con el analyzer activo y almacena referencia."""
    global last_processed_frame

    if frame is None:
        return

    analyzer = analyzer or _ensure_analyzer()
    try:
        processed_frame = analyzer.process_frame(frame)
        last_processed_frame = processed_frame
    except Exception as exc:  # pragma: no cover - solo logging
        current_app.logger.error('Error al procesar frame del cliente: %s', exc, exc_info=True)


@api_bp.route('/environment_info', methods=['GET'])
def environment_info():
    """Devuelve información del entorno para configurar la cámara del cliente"""
    try:
        is_remote = str(os.getenv('IS_REMOTE_SERVER', '')).lower() in ('1', 'true', 'yes')

        request_host = (request.host or '').split(':')[0].lower()
        is_local_host = request_host in ('localhost', '127.0.0.1') or request_host.endswith('.local')

        override = os.getenv('CAMERA_MODE', '').strip().lower()

        # Detectar si existe una cámara física accesible (Linux /dev/videoX)
        video_devices = ['/dev/video0', '/dev/video1']
        has_physical_camera = any(os.path.exists(dev) for dev in video_devices)

        if override in ('client_side', 'server_side'):
            camera_mode = override
        else:
            # Default: si estamos sirviendo desde localhost con cámara física disponible,
            # usamos modo servidor. En dominios remotos forzamos cámara del navegador.
            if is_local_host and has_physical_camera and not is_remote:
                camera_mode = 'server_side'
            else:
                camera_mode = 'client_side'

        environment = {
            'platform': 'remote_server' if is_remote else 'local',
            'camera_mode': camera_mode,
            'has_physical_camera': has_physical_camera,
            'timestamp': time.time()
        }
        return jsonify({'success': True, 'environment': environment}), 200
    except Exception as e:
        current_app.logger.error(f"Error al obtener environment info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ESTADÍSTICAS
# ============================================================================

@api_bp.route('/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """
    Obtiene estadísticas del usuario actual
    
    Returns:
        JSON con estadísticas
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    
    try:
        stats = db_manager.get_user_statistics(user_id)
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error al obtener estadísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# SESIONES ROM
# ============================================================================

@api_bp.route('/sessions/<int:session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """
    Obtiene detalles de una sesión ROM
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        JSON con datos de la sesión
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    
    try:
        rom_session = db_manager.get_rom_session_by_id(session_id)
        
        if not rom_session:
            return jsonify({
                'success': False,
                'error': 'Sesión no encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'data': rom_session.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error al obtener sesión: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/rom-session', methods=['POST'])
@login_required
def create_rom_session():
    """
    Crea una nueva sesión ROM
    
    Request JSON:
        {
            "subject_id": int,
            "segment": str,
            "exercise_type": str,
            "camera_view": str,
            "side": str,
            "max_angle": float,
            "min_angle": float,
            "rom_value": float,
            "quality_score": float,
            "notes": str
        }
    
    Returns:
        JSON con sesión creada
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['subject_id', 'segment', 'exercise_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo requerido: {field}'
                }), 400
        
        # Crear sesión
        rom_session = db_manager.create_rom_session(
            subject_id=data['subject_id'],
            user_id=user_id,
            segment=data['segment'],
            exercise_type=data['exercise_type'],
            camera_view=data.get('camera_view'),
            side=data.get('side'),
            max_angle=data.get('max_angle'),
            min_angle=data.get('min_angle'),
            rom_value=data.get('rom_value'),
            repetitions=data.get('repetitions', 0),
            duration=data.get('duration'),
            quality_score=data.get('quality_score'),
            notes=data.get('notes')
        )
        
        # Log de actividad
        db_manager.log_action(
            action='create_rom_session',
            user_id=user_id,
            details=f"Sesión ROM creada: {data['segment']} - {data['exercise_type']}",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'data': rom_session.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error al crear sesión ROM: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# INFO DEL SISTEMA
# ============================================================================

@api_bp.route('/system/info', methods=['GET'])
def system_info():
    """
    Información del sistema (no requiere auth)
    
    Returns:
        JSON con info del sistema
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    
    try:
        db_info = db_manager.get_database_info()
        
        return jsonify({
            'success': True,
            'data': {
                'app_name': current_app.config['APP_NAME'],
                'version': current_app.config['VERSION'],
                'database': db_info
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# VIDEO STREAMING Y ANÁLISIS EN VIVO (NUEVO)
# ============================================================================

@api_bp.route('/video_feed')
@login_required
def video_feed():
    """
    Stream MJPEG de video procesado con MediaPipe
    
    Este endpoint genera un stream continuo de frames procesados
    por el analyzer correspondiente al ejercicio activo.
    
    Returns:
        Response: Stream MJPEG multipart
    """
    from hardware.camera_manager import camera_manager
    
    # ⚠️ CRÍTICO: Capturar valores de session ANTES del generador
    # (el generador se ejecuta fuera del request context)
    analyzer_type = session.get('analyzer_type')
    user_id = session.get('user_id')
    
    def generate_frames():
        if not analyzer_type or not user_id:
            error_frame = _create_error_frame("No hay ejercicio activo. Selecciona un ejercicio primero.")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
            return

        try:
            analyzer_instance = _ensure_analyzer(analyzer_type)
        except ValueError as setup_error:
            error_frame = _create_error_frame(str(setup_error))
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
            return

        # Adquirir cámara (context manager automático)
        try:
            with camera_manager.acquire_camera(user_id=user_id, width=1280, height=720) as cap:
                logger.info(f"Cámara adquirida por '{user_id}' - Iniciando stream")
                
                while True:
                    ret, frame = cap.read()
                    
                    if not ret:
                        logger.warning("No se pudo leer frame de la cámara")
                        break
                    
                    # Procesar frame con analyzer
                    try:
                        processed_frame = analyzer_instance.process_frame(frame)
                    except Exception as e:
                        logger.error(f"Error al procesar frame: {e}")
                        processed_frame = _create_error_frame(f"Error en procesamiento: {str(e)}")
                    
                    # Codificar frame como JPEG
                    try:
                        ret_encode, buffer = cv2.imencode(
                            '.jpg', 
                            processed_frame, 
                            [cv2.IMWRITE_JPEG_QUALITY, 85]  # 85% calidad (balance velocidad/calidad)
                        )
                        
                        if not ret_encode:
                            logger.error("Error al codificar frame")
                            continue
                        
                        frame_bytes = buffer.tobytes()
                        
                        # Yield del frame en formato MJPEG
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    except Exception as e:
                        logger.error(f"Error al codificar/enviar frame: {e}")
                        continue
        
        except GeneratorExit:
            # Usuario cerró el navegador/tab
            logger.info(f"Stream cerrado por usuario '{user_id}' (GeneratorExit)")
        
        except RuntimeError as e:
            # Cámara en uso o no disponible
            logger.error(f"RuntimeError en video_feed: {e}")
            error_frame = _create_error_frame(str(e))
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
        
        except Exception as e:
            # Error inesperado
            logger.error(f"Error inesperado en video_feed: {e}", exc_info=True)
            error_frame = _create_error_frame(f"Error inesperado: {str(e)}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
        
        finally:
            # Cleanup siempre se ejecuta
            logger.info(f"Finalizando stream para usuario '{user_id}'")
    
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@api_bp.route('/analysis/start', methods=['POST'])
@login_required
def start_analysis():
    """
    Marca el inicio de una sesión de análisis
    
    Body JSON:
        {
            "segment_type": "shoulder",
            "exercise_key": "flexion"
        }
    
    Returns:
        JSON con estado
    """
    try:
        data = request.get_json() or {}
        
        segment_type = data.get('segment_type')
        exercise_key = data.get('exercise_key')
        
        if not segment_type or not exercise_key:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros: segment_type y exercise_key'
            }), 400

        try:
            _ensure_analyzer()
        except ValueError as analyzer_error:
            return jsonify({
                'success': False,
                'error': str(analyzer_error)
            }), 400
        
        # Guardar en sesión
        session['analysis_active'] = True
        session['analysis_start_time'] = time.time()
        
        current_app.logger.info(
            f"Análisis iniciado: {segment_type}/{exercise_key} "
            f"por usuario {session.get('user_id')}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Análisis iniciado correctamente',
            'segment_type': segment_type,
            'exercise_key': exercise_key
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error al iniciar análisis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/stop', methods=['POST'])
@login_required
def stop_analysis():
    """
    Detiene la sesión de análisis actual
    
    Returns:
        JSON con estado y datos finales
    """
    global current_analyzer
    
    try:
        # Obtener datos finales del analyzer
        final_data = {}
        if current_analyzer:
            final_data = current_analyzer.get_current_data()
        
        # Limpiar sesión
        session['analysis_active'] = False
        session.pop('analysis_start_time', None)

        if client_frame_receiver.is_active:
            client_frame_receiver.stop_receiving()
        
        current_app.logger.info(
            f"Análisis detenido por usuario {session.get('user_id')} | "
            f"ROM final: {final_data.get('max_rom', 'N/A')}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Análisis detenido correctamente',
            'final_data': final_data
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error al detener análisis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/current_data', methods=['GET'])
@login_required
def get_current_data():
    """
    Obtiene los datos actuales del análisis en tiempo real
    
    Polling endpoint - el frontend puede llamar cada 100-200ms
    
    Returns:
        JSON con datos actuales del analyzer
    """
    global current_analyzer
    
    try:
        analyzer = current_analyzer
        if analyzer is None:
            try:
                analyzer = _ensure_analyzer()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'No hay analyzer activo',
                    'data': {}
                }), 200

        data = analyzer.get_current_data()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': time.time()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error al obtener datos actuales: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500


@api_bp.route('/analysis/reset', methods=['POST'])
@login_required
def reset_analysis():
    """
    Reinicia las estadísticas del analyzer (ROM máximo, ángulos, etc.)
    sin recrear el analyzer completo
    
    Returns:
        JSON con estado
    """
    global current_analyzer
    
    try:
        if current_analyzer is None:
            return jsonify({
                'success': True,
                'message': 'No hay analyzer activo, nada que resetear'
            }), 200
        
        # Resetear analyzer
        current_analyzer.reset()
        
        current_app.logger.info(f"Analyzer reseteado por usuario {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Estadísticas reiniciadas correctamente'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error al resetear analyzer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CLIENT CAMERA ENDPOINTS
# ============================================================================

@api_bp.route('/prepare_client_receiver/<segment>/<exercise>', methods=['POST'])
@login_required
def prepare_client_receiver(segment, exercise):
    """Activa el receptor de frames del cliente antes de iniciar uploads."""
    try:
        _ensure_analyzer()
        if not client_frame_receiver.is_active:
            client_frame_receiver.start_receiving()
        stats = client_frame_receiver.get_stats()
        return jsonify({
            'success': True,
            'message': 'Receiver listo',
            'stats': stats,
            'segment': segment,
            'exercise': exercise
        }), 200
    except ValueError as analyzer_error:
        return jsonify({'success': False, 'error': str(analyzer_error)}), 400
    except Exception as exc:
        current_app.logger.error(f"Error al preparar receiver: {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


@api_bp.route('/upload_frame/<segment>/<exercise>', methods=['POST'])
@login_required
def upload_frame(segment, exercise):
    """Recibe frames desde el navegador (modo cámara cliente)."""
    try:
        payload = request.get_json(silent=True)
        if not payload or 'frame' not in payload:
            return jsonify({'success': False, 'error': 'Payload inválido'}), 400

        metadata = {
            'width': payload.get('width') or 0,
            'height': payload.get('height') or 0,
            'device_label': payload.get('device_label', ''),
        }

        analyzer = _ensure_analyzer()

        if not client_frame_receiver.is_active:
            client_frame_receiver.start_receiving()

        received = client_frame_receiver.receive_frame(
            payload['frame'],
            payload.get('timestamp'),
            metadata
        )

        if not received:
            return jsonify({'success': False, 'error': 'Frame descartado'}), 500

        frame, _ = client_frame_receiver.get_current_frame()
        if frame is not None:
            _process_frame_with_analyzer(frame, analyzer)

        stats = client_frame_receiver.get_stats()
        return jsonify({
            'success': True,
            'frame_count': stats['frame_count'],
            'segment': segment,
            'exercise': exercise
        }), 200

    except ValueError as analyzer_error:
        return jsonify({'success': False, 'error': str(analyzer_error)}), 400
    except Exception as exc:
        current_app.logger.error(f"Error subiendo frame: {exc}", exc_info=True)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _create_error_frame(message: str) -> bytes:
    """
    Crea un frame de error con mensaje
    
    Args:
        message: Mensaje de error a mostrar
    
    Returns:
        bytes: Frame codificado como JPEG
    """
    # Crear frame negro con texto
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Agregar texto (dividir en líneas si es muy largo)
    words = message.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) > 35:  # ~35 caracteres por línea
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line)
    
    # Dibujar líneas centradas
    y_start = 240 - (len(lines) * 15)  # Centrar verticalmente
    for i, line in enumerate(lines):
        y_pos = y_start + (i * 30)
        cv2.putText(
            frame, 
            line, 
            (50, y_pos), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (0, 0, 255),  # Rojo
            2
        )
    
    # Codificar como JPEG
    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buffer.tobytes()
