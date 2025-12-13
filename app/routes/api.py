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
- /api/camera/*: Control de cámara (NUEVO)
- /api/session/*: Sesión de análisis con estados (NUEVO)

Autor: BIOTRACK Team
Fecha: 2025-11-14
"""

from flask import (
    Blueprint, jsonify, request, session, current_app, Response
)
from app.routes.auth import login_required
import cv2
import numpy as np
import logging
import time

# Import de camera_manager a nivel de módulo para evitar problemas con closures
from hardware.camera_manager import camera_manager

# Crear blueprint
api_bp = Blueprint('api', __name__)

# Logger para uso fuera del contexto de Flask
logger = logging.getLogger(__name__)

# ============================================================================
# CACHE GLOBAL DE ANALYZERS
# ============================================================================
# Diccionario para cachear analyzers por tipo (evita re-inicialización de 25s)
_ANALYZER_CACHE = {}

# Variable global para el tipo de analyzer actual en uso
_current_analyzer_type = None

def get_cached_analyzer(analyzer_type: str, analyzer_class):
    """
    Obtiene analyzer cacheado o crea uno nuevo
    
    Primera llamada: Inicializa MediaPipe (~25 segundos)
    Siguientes llamadas: Reutiliza analyzer cacheado (0 segundos)
    
    Args:
        analyzer_type: Tipo de analyzer ('shoulder_profile', 'shoulder_frontal', etc.)
        analyzer_class: Clase del analyzer a instanciar
    
    Returns:
        Analyzer inicializado y listo para usar
    """
    global _current_analyzer_type
    import time
    
    if analyzer_type not in _ANALYZER_CACHE:
        logger.info(f"🔧 Creando NUEVO analyzer '{analyzer_type}'...")
        start_time = time.time()
        
        _ANALYZER_CACHE[analyzer_type] = analyzer_class(
            processing_width=640,
            processing_height=480,
            show_skeleton=False
        )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Analyzer '{analyzer_type}' creado en {elapsed:.2f}s y cacheado")
    else:
        logger.info(f"⚡ Reutilizando analyzer cacheado '{analyzer_type}'")
    
    # Actualizar tipo actual
    _current_analyzer_type = analyzer_type
    
    return _ANALYZER_CACHE[analyzer_type]


def get_current_analyzer():
    """
    Obtiene el analyzer actual en uso.
    
    Returns:
        Analyzer actual o None si no hay ninguno activo
    """
    if _current_analyzer_type and _current_analyzer_type in _ANALYZER_CACHE:
        return _ANALYZER_CACHE[_current_analyzer_type]
    return None


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
# CONTROL DE CÁMARA
# ============================================================================

@api_bp.route('/camera/status', methods=['GET'])
@login_required
def camera_status():
    """
    Obtiene el estado actual de la cámara
    
    Returns:
        JSON con estado de cámara
    """
    from hardware.camera_manager import camera_manager
    
    try:
        status = camera_manager.get_status()
        return jsonify({
            'success': True,
            'camera': status
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# 🔊 ENDPOINTS DE TTS (Text-to-Speech)
# ============================================================================

@api_bp.route('/tts/toggle', methods=['POST'])
@login_required
def tts_toggle():
    """
    Activa/desactiva la guía de voz
    
    Returns:
        JSON con nuevo estado de la voz
    """
    try:
        from app.services.tts_service import get_tts_service
        
        tts = get_tts_service()
        new_state = tts.toggle_voice()
        
        return jsonify({
            'success': True,
            'voice_enabled': new_state,
            'message': 'Voz activada' if new_state else 'Voz desactivada'
        }), 200
    except Exception as e:
        logger.error(f"[TTS] Error en toggle: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/tts/status', methods=['GET'])
@login_required
def tts_status():
    """
    Obtiene el estado actual del servicio TTS
    
    Returns:
        JSON con estado del servicio
    """
    try:
        from app.services.tts_service import get_tts_service
        
        tts = get_tts_service()
        status = tts.get_status()
        
        return jsonify({
            'success': True,
            **status
        }), 200
    except Exception as e:
        logger.error(f"[TTS] Error obteniendo status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/tts/speak', methods=['POST'])
@login_required
def tts_speak():
    """
    Reproduce un mensaje de voz personalizado
    
    Body:
        message: Texto a reproducir
    
    Returns:
        JSON con resultado
    """
    try:
        from app.services.tts_service import get_tts_service
        
        data = request.get_json() or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó mensaje'
            }), 400
        
        tts = get_tts_service()
        tts.speak(message)
        
        return jsonify({
            'success': True,
            'message': 'Mensaje enviado a reproducción'
        }), 200
    except Exception as e:
        logger.error(f"[TTS] Error en speak: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/tts/speak_result', methods=['POST'])
@login_required
def tts_speak_result():
    """
    Reproduce el mensaje de resultado ROM (usado por análisis bilateral secuencial)
    
    Body:
        rom_value: float - Valor ROM principal
        classification: str - Clasificación del resultado
        is_bilateral: bool - Si es resultado bilateral
        left_rom: float - ROM izquierdo (opcional, para bilateral)
        right_rom: float - ROM derecho (opcional, para bilateral)
    
    Returns:
        JSON con resultado
    """
    try:
        from app.services.tts_service import get_tts_service, TTSMessages
        
        data = request.get_json() or {}
        rom_value = data.get('rom_value', 0)
        classification = data.get('classification', 'Normal')
        is_bilateral = data.get('is_bilateral', False)
        left_rom = data.get('left_rom')
        right_rom = data.get('right_rom')
        
        tts = get_tts_service()
        
        # Construir mensaje según si es bilateral o no
        if is_bilateral and left_rom is not None and right_rom is not None:
            message = TTSMessages.completed_result(
                rom_value, 
                classification,
                left_rom=left_rom,
                right_rom=right_rom
            )
        else:
            message = TTSMessages.completed_result(rom_value, classification)
        
        current_app.logger.info(f"[TTS] Hablando resultado: {message}")
        tts.speak(message)
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
    except Exception as e:
        logger.error(f"[TTS] Error en speak_result: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/tts/stop', methods=['POST'])
@login_required
def tts_stop():
    """
    Detiene el mensaje actual de voz
    
    Returns:
        JSON con resultado
    """
    try:
        from app.services.tts_service import get_tts_service
        
        tts = get_tts_service()
        tts.stop_current()
        
        return jsonify({
            'success': True,
            'message': 'Mensaje detenido'
        }), 200
    except Exception as e:
        logger.error(f"[TTS] Error deteniendo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/camera/release', methods=['POST'])
@login_required
def camera_release():
    """
    Libera la cámara forzadamente
    
    Usar solo si la cámara se quedó bloqueada.
    También limpia la sesión de análisis activa.
    
    Returns:
        JSON con resultado
    """
    from hardware.camera_manager import camera_manager
    from app.core.analysis_session import clear_current_session
    
    try:
        # Limpiar sesión de análisis primero
        clear_current_session()
        
        # Luego liberar cámara
        was_released = camera_manager.force_release()
        return jsonify({
            'success': True,
            'released': was_released,
            'message': 'Cámara liberada' if was_released else 'La cámara ya estaba libre'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Cache de cámaras disponibles (evita re-escanear mientras hay stream activo)
_camera_list_cache = None
_camera_list_cache_time = 0

@api_bp.route('/camera/list', methods=['GET'])
@login_required
def camera_list():
    """
    Lista las cámaras disponibles en el sistema
    
    SEGURIDAD:
    - Si hay cámara en uso, retorna lista cacheada (no re-escanea)
    - El escaneo de cámaras puede interferir con streams activos
    
    Query params:
        force: bool - Forzar re-escaneo (invalida caché, solo si cámara libre)
    
    Returns:
        JSON con lista de cámaras detectadas
    """
    global _camera_list_cache, _camera_list_cache_time
    import time as time_mod
    
    try:
        force_scan = request.args.get('force', 'false').lower() == 'true'
        
        # Verificar si la cámara está en uso por el stream
        camera_in_use = not camera_manager.is_available()
        
        # Si la cámara está en uso Y hay caché válido, usar caché
        if camera_in_use and _camera_list_cache:
            logger.info("[camera/list] Cámara en uso - retornando lista cacheada")
            return jsonify({
                'success': True,
                'cameras': _camera_list_cache,
                'count': len(_camera_list_cache),
                'current': session.get('camera_index', 0),
                'cached': True,
                'camera_in_use': True
            }), 200
        
        # Si force_scan, invalidar caché
        if force_scan:
            _camera_list_cache = None
            _camera_list_cache_time = 0
            logger.info("[camera/list] Caché invalidado por force_scan")
        
        # Si hay caché válido (menos de 60 segundos) y no es force, usarlo
        cache_age = time_mod.time() - _camera_list_cache_time
        if _camera_list_cache and cache_age < 60 and not force_scan:
            logger.info(f"[camera/list] Usando caché (edad: {cache_age:.1f}s)")
            return jsonify({
                'success': True,
                'cameras': _camera_list_cache,
                'count': len(_camera_list_cache),
                'current': session.get('camera_index', 0),
                'cached': True,
                'cache_age': round(cache_age, 1)
            }), 200
        
        # Si la cámara está en uso y NO hay caché, retornar lista básica
        if camera_in_use:
            current_idx = session.get('camera_index', 0)
            # Retornar lista más completa de cámaras típicas
            basic_list = [
                {'index': 0, 'name': 'Cámara 0 (Integrada)', 'resolution': 'Disponible', 'available': True},
                {'index': 1, 'name': 'Cámara 1 (CAMO/Virtual)', 'resolution': 'Disponible', 'available': True},
                {'index': 2, 'name': 'Cámara 2 (Externa USB)', 'resolution': 'Disponible', 'available': True},
            ]
            return jsonify({
                'success': True,
                'cameras': basic_list,
                'count': len(basic_list),
                'current': current_idx,
                'cached': False,
                'camera_in_use': True,
                'note': 'Lista básica - escaneo completo requiere cámara libre'
            }), 200
        
        # Cámara libre - escanear todas las cámaras
        logger.info("[camera/list] Escaneando cámaras disponibles...")
        available_cameras = []
        
        # Nombres descriptivos para cámaras comunes
        camera_names = {
            0: 'Integrada (Laptop)',
            1: 'CAMO/Virtual',
            2: 'Externa USB (W1)',
            3: 'Externa USB 2',
            4: 'Otra'
        }
        
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Verificar si la cámara realmente da frames
                ret, frame = cap.read()
                if ret and frame is not None:
                    avg = frame.mean()
                    status = 'Activa' if avg > 10 else 'Sin señal'
                else:
                    status = 'Sin frames'
                
                name = camera_names.get(i, f'Cámara {i}')
                
                available_cameras.append({
                    'index': i,
                    'name': f'Cámara {i} ({name})',
                    'resolution': f'{width}x{height}',
                    'status': status,
                    'available': True
                })
                cap.release()
        
        # Actualizar caché
        _camera_list_cache = available_cameras
        _camera_list_cache_time = time_mod.time()
        
        logger.info(f"[camera/list] Encontradas {len(available_cameras)} cámaras, caché actualizado")
        
        return jsonify({
            'success': True,
            'cameras': available_cameras,
            'count': len(available_cameras),
            'current': session.get('camera_index', 0),
            'cached': False
        }), 200
        
    except Exception as e:
        logger.error(f"[camera/list] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/camera/select', methods=['POST'])
@login_required
def camera_select():
    """
    Selecciona el índice de cámara a usar
    
    Body JSON:
        camera_index: int - 0 para integrada, 1+ para externa
    
    Returns:
        JSON con confirmación
    """
    try:
        data = request.get_json() or {}
        camera_index = data.get('camera_index', 0)
        
        # Guardar en sesión
        session['camera_index'] = camera_index
        
        return jsonify({
            'success': True,
            'camera_index': camera_index,
            'message': f'Cámara seleccionada: índice {camera_index}'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/camera/config', methods=['GET', 'POST'])
@login_required
def camera_config():
    """
    Obtiene o actualiza la configuración de cámara
    
    GET: Retorna configuración actual
    POST: Actualiza configuración (solo cuando NO hay sesión activa)
    
    Body JSON (POST):
        camera_index: int - Índice de cámara (0=integrada, 1+=externa)
        resolution: dict - {width: int, height: int}
        jpeg_quality: int - Calidad JPEG (1-100)
    
    Returns:
        JSON con configuración actual
    
    SEGURIDAD:
        - No permite cambiar cámara/resolución si hay sesión de análisis activa
        - jpeg_quality se puede cambiar siempre (toma efecto inmediatamente)
    """
    from app.core.analysis_session import get_current_session
    
    # Verificar si hay sesión de análisis ACTIVA (no solo existente)
    # Una sesión existe pero puede estar COMPLETED/ERROR, en cuyo caso no está activa
    analysis_session = get_current_session()
    is_session_active = analysis_session is not None and analysis_session.is_active
    
    if request.method == 'GET':
        # Retornar configuración actual
        return jsonify({
            'success': True,
            'config': {
                'camera_index': session.get('camera_index', current_app.config.get('CAMERA_INDEX', 0)),
                'resolution': {
                    'width': session.get('processing_width', current_app.config.get('CAMERA_PROCESSING_WIDTH', 960)),
                    'height': session.get('processing_height', current_app.config.get('CAMERA_PROCESSING_HEIGHT', 540))
                },
                'jpeg_quality': session.get('jpeg_quality', current_app.config.get('JPEG_QUALITY', 60)),
                'fps': current_app.config.get('CAMERA_FPS', 30)
            },
            'available_resolutions': current_app.config.get('AVAILABLE_RESOLUTIONS', []),
            'available_jpeg_qualities': current_app.config.get('AVAILABLE_JPEG_QUALITIES', []),
            'session_active': is_session_active
        }), 200
    
    # POST: Actualizar configuración
    try:
        data = request.get_json() or {}
        
        # Verificar si hay sesión activa (solo para cambios de cámara/resolución)
        session_active = is_session_active
        changes_made = []
        
        # 1. JPEG Quality - siempre se puede cambiar
        if 'jpeg_quality' in data:
            quality = int(data['jpeg_quality'])
            if 1 <= quality <= 100:
                session['jpeg_quality'] = quality
                changes_made.append(f"jpeg_quality={quality}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'jpeg_quality debe estar entre 1 y 100'
                }), 400
        
        # 2. Cámara y Resolución
        # NOTA: Aunque haya stream activo, permitimos guardar la config
        # porque el frontend va a recargar la página después, lo cual
        # liberará la cámara y aplicará la nueva configuración.
        # Solo bloqueamos si hay una SESIÓN DE ANÁLISIS activa (con datos ROM).
        
        if 'camera_index' in data:
            new_camera_index = int(data['camera_index'])
            session['camera_index'] = new_camera_index
            session.modified = True  # Forzar guardado de sesión
            changes_made.append(f"camera_index={new_camera_index}")
            logger.info(f"[camera_config] Cámara cambiada a índice {new_camera_index}")
            
            # Invalidar caché de lista de cámaras
            global _camera_list_cache, _camera_list_cache_time
            _camera_list_cache = None
            _camera_list_cache_time = 0
        
        if 'resolution' in data:
            res = data['resolution']
            if isinstance(res, dict) and 'width' in res and 'height' in res:
                session['processing_width'] = int(res['width'])
                session['processing_height'] = int(res['height'])
                session.modified = True  # Forzar guardado de sesión
                changes_made.append(f"resolution={res['width']}x{res['height']}")
                logger.info(f"[camera_config] Resolución cambiada a {res['width']}x{res['height']}")
        
        return jsonify({
            'success': True,
            'changes': changes_made,
            'message': f"Configuración actualizada: {', '.join(changes_made)}" if changes_made else "Sin cambios",
            'config': {
                'camera_index': session.get('camera_index', 0),
                'resolution': {
                    'width': session.get('processing_width', 960),
                    'height': session.get('processing_height', 540)
                },
                'jpeg_quality': session.get('jpeg_quality', 60)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error en camera_config: {e}")
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
    
    Query params:
        camera: int - Índice de cámara (0=integrada, 1=externa). Default: 1
    
    Returns:
        Response: Stream MJPEG multipart
    """
    from app.analyzers import (
        ShoulderProfileAnalyzer, ShoulderFrontalAnalyzer, 
        ElbowProfileAnalyzer,
        HipProfileAnalyzer, HipFrontalAnalyzer,
        KneeProfileAnalyzer,
        AnkleProfileAnalyzer
    )
    
    # ⚠️ CRÍTICO: Capturar valores de session ANTES del generador
    # (el generador se ejecuta fuera del request context)
    analyzer_type = session.get('analyzer_type')
    user_id = session.get('user_id')
    
    # Obtener configuración de cámara desde session (con defaults de config)
    # Soporte para cámaras RTSP/HTTP (string) o índice entero
    camera_param = request.args.get('camera', None)
    if camera_param is None:
        camera_param = session.get('camera_index', current_app.config.get('CAMERA_INDEX', 0))

    try:
        camera_session_index = int(camera_param)
    except (TypeError, ValueError):
        camera_session_index = camera_param  # Puede ser URL/rtsp
    jpeg_quality = session.get('jpeg_quality', current_app.config.get('JPEG_QUALITY', 60))
    processing_width = session.get('processing_width', current_app.config.get('CAMERA_PROCESSING_WIDTH', 960))
    processing_height = session.get('processing_height', current_app.config.get('CAMERA_PROCESSING_HEIGHT', 540))
    
    # Log CRÍTICO para debug
    print(f"\n{'='*60}")
    print(f"🎥 VIDEO_FEED REQUEST")
    print(f"   URL param 'camera': {request.args.get('camera', 'NO SET')}")
    print(f"   session['camera_index']: {session.get('camera_index', 'NO SET')}")
    print(f"   FINAL camera_session_index: {camera_session_index}")
    print(f"{'='*60}\n")
    
    logger.info(f"[video_feed] Iniciando con camera_index={camera_session_index}, session['camera_index']={session.get('camera_index', 'NO SET')}")
    
    def generate_frames():
        # El analyzer se obtiene de la caché global con get_cached_analyzer()
        # Ya no usamos variable global current_analyzer
        
        if not analyzer_type or not user_id:
            # Frame de error
            error_frame = _create_error_frame("No hay ejercicio activo. Selecciona un ejercicio primero.")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
            return
        
        # Mapa de analyzers
        analyzer_classes = {
            'shoulder_profile': ShoulderProfileAnalyzer,
            'shoulder_frontal': ShoulderFrontalAnalyzer,
            'elbow_profile': ElbowProfileAnalyzer,
            'hip_profile': HipProfileAnalyzer,
            'hip_frontal': HipFrontalAnalyzer,
            'knee_profile': KneeProfileAnalyzer,
            'ankle_profile': AnkleProfileAnalyzer,
        }
        
        # Inicializar analyzer si no existe o es diferente
        analyzer_class = analyzer_classes.get(analyzer_type)
        if not analyzer_class:
            error_frame = _create_error_frame(f"Analyzer '{analyzer_type}' no implementado aún")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
            return
        
        # Obtener analyzer cacheado (reutiliza si ya existe)
        import time as time_module
        
        print(f"\n{'='*60}")
        print(f"🎬 VIDEO_FEED INICIADO - {time_module.strftime('%H:%M:%S')}")
        print(f"📍 TIMING: Obteniendo analyzer '{analyzer_type}'...")
        t0 = time_module.time()
        
        current_analyzer = get_cached_analyzer(analyzer_type, analyzer_class)
        
        t1 = time_module.time()
        print(f"📍 TIMING: Analyzer obtenido en {t1-t0:.2f}s")
        
        # Obtener índice de cámara de la sesión (default desde config)
        camera_index = camera_session_index if camera_session_index is not None else 0
        
        # Adquirir cámara (context manager automático)
        # Resolución desde session o config
        try:
            print(f"📍 TIMING: Adquiriendo cámara (índice={camera_index}, res={processing_width}x{processing_height})...")
            t2 = time_module.time()
            
            with camera_manager.acquire_camera(user_id=user_id, camera_index=camera_index, width=processing_width, height=processing_height) as cap:
                t3 = time_module.time()
                print(f"📍 TIMING: Cámara adquirida en {t3-t2:.2f}s")
                print(f"🎥 STREAMING INICIADO - Total setup: {t3-t0:.2f}s")
                print(f"{'='*60}\n")
                
                frame_count = 0
                mediapipe_ready = False
                first_process_logged = False
                
                while True:
                    ret, frame = cap.read()
                    
                    if not ret:
                        logger.warning("No se pudo leer frame de la cámara")
                        break
                    
                    frame_count += 1
                    
                    # Verificar si MediaPipe está listo
                    if not mediapipe_ready:
                        # Chequear si el pose model ya se inicializó
                        mediapipe_ready = hasattr(current_analyzer, 'pose') and current_analyzer.pose is not None
                        
                        if frame_count == 1:
                            print(f"📍 TIMING: Primer frame leído, mediapipe_ready={mediapipe_ready}")
                        
                        if not mediapipe_ready:
                            # MediaPipe AÚN inicializando - Mostrar frame CRUDO (sin procesar)
                            # Esto da feedback visual inmediato al usuario (ve su cámara en ~2s)
                            if frame_count % 30 == 0:  # Log cada 30 frames (~1 segundo)
                                print(f"⏳ MediaPipe inicializando... Frame {frame_count}")
                            
                            # Frame crudo con overlay de "Cargando..."
                            raw_frame = frame.copy()
                            cv2.putText(
                                raw_frame,
                                "Inicializando MediaPipe...",
                                (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (0, 255, 255),  # Amarillo
                                2
                            )
                            cv2.putText(
                                raw_frame,
                                "El skeleton aparecera en unos segundos",
                                (50, 90),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 255, 255),  # Blanco
                                1
                            )
                            
                            processed_frame = raw_frame
                        else:
                            # MediaPipe LISTO - Primera vez que procesamos
                            print(f"✅ MediaPipe listo! Iniciando procesamiento con skeleton")
                            t_first = time_module.time()
                            processed_frame = current_analyzer.process_frame(frame)
                            t_first_end = time_module.time()
                            print(f"📍 TIMING: Primer process_frame: {t_first_end-t_first:.2f}s")
                    else:
                        # MediaPipe ya estaba listo - Procesamiento normal
                        try:
                            if not first_process_logged and frame_count <= 5:
                                t_proc = time_module.time()
                                processed_frame = current_analyzer.process_frame(frame)
                                t_proc_end = time_module.time()
                                print(f"📍 TIMING: Frame #{frame_count} process_frame: {t_proc_end-t_proc:.3f}s")
                                if frame_count == 5:
                                    first_process_logged = True
                            else:
                                processed_frame = current_analyzer.process_frame(frame)
                        except Exception as e:
                            logger.error(f"Error al procesar frame: {e}")
                            processed_frame = _create_error_frame(f"Error en procesamiento: {str(e)}")
                    
                    # Codificar frame como JPEG (calidad desde session o config)
                    try:
                        ret_encode, buffer = cv2.imencode(
                            '.jpg', 
                            processed_frame, 
                            [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
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
            # Forzar liberación de cámara si aún está en uso
            try:
                if not camera_manager.is_available():
                    camera_manager.force_release()
                    logger.info(f"Cámara liberada forzadamente al finalizar stream de '{user_id}'")
            except Exception as cleanup_error:
                logger.error(f"Error en cleanup de cámara: {cleanup_error}")
    
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
        
        # Guardar en sesión
        session['analysis_active'] = True
        session['analysis_start_time'] = time.time()
        
        # 🔍 LOGGING CRÍTICO: Verificar estado del analyzer
        current_analyzer = get_current_analyzer()
        logger.info(f"🚀 Iniciando sesión oficial: {segment_type}/{exercise_key} por usuario {session.get('user_id')}")
        logger.info(f"🔍 Estado del analyzer: {'Inicializado' if current_analyzer else 'None (esperando video_feed)'}")
        
        if current_analyzer:
            # Verificar datos inmediatamente
            test_data = current_analyzer.get_current_data()
            angle_val = test_data.get('angle', 0)
            max_rom_val = test_data.get('max_rom', 0)
            
            angle_str = f"{angle_val:.2f}" if isinstance(angle_val, (int, float)) else 'N/A'
            max_rom_str = f"{max_rom_val:.2f}" if isinstance(max_rom_val, (int, float)) else 'N/A'
            
            logger.info(f"✅ Datos del analyzer: angle={angle_str}, max_rom={max_rom_str}")
        
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
    try:
        # Obtener datos finales del analyzer
        final_data = {}
        current_analyzer = get_current_analyzer()
        if current_analyzer:
            final_data = current_analyzer.get_current_data()
        
        # Limpiar sesión
        session['analysis_active'] = False
        session.pop('analysis_start_time', None)
        
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
    
    Polling endpoint - el frontend puede llamar cada 200-500ms
    
    Returns:
        JSON con datos actuales del analyzer
    """
    try:
        # Usar el sistema de caché para obtener el analyzer actual
        analyzer = get_current_analyzer()
        
        if analyzer is None:
            # No loguear en cada polling - solo devolver datos vacíos
            return jsonify({
                'success': False,
                'error': 'No hay analyzer activo',
                'data': {}
            }), 200
        
        # Obtener datos del analyzer
        data = analyzer.get_current_data()
        
        # NO loguear en cada polling - afecta rendimiento
        # Solo loguear si hay problemas
        
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
    try:
        # Obtener analyzer del caché
        current_analyzer = get_current_analyzer()
        
        if current_analyzer is None:
            logger.warning("🔄 Intento de reset pero current_analyzer es None")
            return jsonify({
                'success': False,
                'error': 'No hay analyzer activo'
            }), 400
        
        # 🔍 LOGGING CRÍTICO: Estado ANTES del reset
        before_data = current_analyzer.get_current_data()
        angle_before = before_data.get('angle', 0)
        rom_before = before_data.get('max_rom', 0)
        
        angle_before_str = f"{angle_before:.2f}" if isinstance(angle_before, (int, float)) else 'N/A'
        rom_before_str = f"{rom_before:.2f}" if isinstance(rom_before, (int, float)) else 'N/A'
        
        logger.info(f"🔄 ANTES del reset: angle={angle_before_str}, max_rom={rom_before_str}")
        
        # Resetear analyzer
        current_analyzer.reset()
        
        # 🔍 LOGGING CRÍTICO: Estado DESPUÉS del reset
        after_data = current_analyzer.get_current_data()
        angle_after = after_data.get('angle', 0)
        rom_after = after_data.get('max_rom', 0)
        
        angle_after_str = f"{angle_after:.2f}" if isinstance(angle_after, (int, float)) else 'N/A'
        rom_after_str = f"{rom_after:.2f}" if isinstance(rom_after, (int, float)) else 'N/A'
        
        logger.info(f"✅ DESPUÉS del reset: angle={angle_after_str}, max_rom={rom_after_str}")
        
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


@api_bp.route('/analysis/save', methods=['POST'])
@login_required
def save_analysis_to_history():
    """
    Guarda el resultado de un análisis ROM.
    
    Si se proporciona subject_id -> Guarda en rom_session (análisis de sujeto)
    Si NO hay subject_id -> Guarda en user_analysis_history (auto-análisis)
    
    Body JSON:
        subject_id: int (opcional) - ID del sujeto analizado (si es análisis de sujeto)
        segment: str - Segmento analizado (shoulder, hip, knee, etc.)
        exercise_type: str - Tipo de ejercicio (flexion, extension, etc.)
        side: str - Lado (left, right, bilateral)
        camera_view: str - Vista de cámara (profile, frontal)
        rom_value: float - Valor ROM principal (o promedio bilateral)
        left_rom: float - ROM lado izquierdo (solo bilateral)
        right_rom: float - ROM lado derecho (solo bilateral)
        classification: str - Clasificación ROM (Normal, Limitado, etc.)
        quality_score: float - Puntuación de calidad (0-100)
        duration: float - Duración del análisis en segundos
        notes: str - Notas opcionales
        
    Returns:
        JSON con ID del registro creado
    """
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuario no autenticado'
            }), 401
        
        # Validar campos requeridos
        required_fields = ['segment', 'exercise_type', 'rom_value']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }), 400
        
        # Determinar si es análisis de sujeto o auto-análisis
        subject_id = data.get('subject_id')
        
        # Importar database manager
        from database.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # ============================================================
        # RUTA 1: Análisis de Sujeto -> Guardar en rom_session
        # ============================================================
        if subject_id:
            logger.info(f"📊 Guardando análisis de SUJETO: subject_id={subject_id}, user_id={user_id}")
            
            # Verificar que el usuario tiene acceso al sujeto
            user_role = session.get('role', 'student')
            if not db_manager.can_user_access_subject(user_id, int(subject_id), user_role):
                return jsonify({
                    'success': False,
                    'error': 'No tiene permisos para analizar este sujeto'
                }), 403
            
            # Mapear camera_view: 'profile' -> 'lateral' para la BD
            camera_view_map = {
                'profile': 'lateral',
                'frontal': 'frontal',
                'posterior': 'posterior'
            }
            camera_view = camera_view_map.get(data.get('camera_view', 'profile'), 'lateral')
            
            # Preparar datos para rom_session
            try:
                rom_session = db_manager.create_rom_session(
                    subject_id=int(subject_id),
                    user_id=user_id,
                    segment=data.get('segment', ''),
                    exercise_type=data.get('exercise_type', ''),
                    camera_view=camera_view,
                    side=data.get('side', 'right'),
                    rom_value=float(data.get('rom_value', 0)),
                    max_angle=float(data.get('rom_value', 0)),  # Usar rom_value como max_angle
                    min_angle=0.0,
                    quality_score=float(data.get('quality_score', 0)) if data.get('quality_score') else None,
                    duration=float(data.get('duration', 0)) if data.get('duration') else None,
                    notes=data.get('notes', '')
                )
                
                # rom_session es ahora un diccionario, acceder con ['id']
                logger.info(f"✅ Análisis de SUJETO guardado en rom_session: subject={subject_id}, session_id={rom_session['id']}")
                return jsonify({
                    'success': True,
                    'message': 'Análisis de sujeto guardado correctamente',
                    'session_id': rom_session['id'],
                    'analysis_type': 'subject'
                }), 201
                
            except Exception as e:
                logger.error(f"Error al guardar en rom_session: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error al guardar análisis de sujeto: {str(e)}'
                }), 500
        
        # ============================================================
        # RUTA 2: Auto-análisis -> Guardar en user_analysis_history
        # ============================================================
        else:
            logger.info(f"📊 Guardando AUTO-ANÁLISIS: user_id={user_id}")
            
            # Preparar datos para user_analysis_history
            history_data = {
                'segment': data.get('segment', ''),
                'exercise_type': data.get('exercise_type', ''),
                'side': data.get('side', 'right'),
                'camera_view': data.get('camera_view', 'profile'),
                'rom_value': float(data.get('rom_value', 0)),
                'left_rom': float(data.get('left_rom', 0)) if data.get('left_rom') else None,
                'right_rom': float(data.get('right_rom', 0)) if data.get('right_rom') else None,
                'classification': data.get('classification', 'Sin clasificar'),
                'quality_score': float(data.get('quality_score', 0)) if data.get('quality_score') else None,
                'duration': float(data.get('duration', 0)) if data.get('duration') else None
            }
            
            result = db_manager.save_analysis_to_history(user_id, history_data)
            
            if result and result.get('success'):
                logger.info(f"✅ AUTO-ANÁLISIS guardado en historial: user={user_id}, segment={history_data['segment']}, id={result.get('id')}")
                return jsonify({
                    'success': True,
                    'message': 'Auto-análisis guardado en historial',
                    'history_id': result.get('id'),
                    'analysis_type': 'self'
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Error al guardar en base de datos'
                }), 500
            
    except ValueError as ve:
        logger.error(f"Error de validación al guardar análisis: {ve}")
        return jsonify({
            'success': False,
            'error': f'Error de validación: {str(ve)}'
        }), 400
        
    except Exception as e:
        logger.error(f"Error al guardar análisis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/clear-subject', methods=['POST'])
@login_required
def clear_analysis_subject():
    """
    Limpia el sujeto de análisis de la sesión.
    Debe llamarse después de completar un análisis de sujeto.
    
    Returns:
        JSON confirmando la limpieza
    """
    try:
        # Limpiar variables de sesión relacionadas con el análisis de sujeto
        subject_id = session.pop('analysis_subject_id', None)
        subject_name = session.pop('analysis_subject_name', None)
        
        if subject_id:
            logger.info(f"🧹 Sesión de análisis limpiada: subject_id={subject_id}, subject_name={subject_name}")
        
        return jsonify({
            'success': True,
            'message': 'Sesión de análisis limpiada',
            'cleared_subject_id': subject_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error al limpiar sesión de análisis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/history', methods=['GET'])
@login_required
def get_analysis_history():
    """
    Obtiene el historial de análisis del usuario actual.
    
    Query params:
        segment: str - Filtrar por segmento
        exercise_type: str - Filtrar por tipo de ejercicio
        limit: int - Límite de resultados (default 50)
        offset: int - Offset para paginación (default 0)
        
    Returns:
        JSON con lista de análisis históricos
    """
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuario no autenticado'
            }), 401
        
        # Obtener parámetros de filtro
        segment = request.args.get('segment')
        exercise_type = request.args.get('exercise_type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Obtener historial
        from database.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        history = db_manager.get_user_analysis_history(
            user_id=user_id,
            segment=segment,
            exercise_type=exercise_type,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener historial de análisis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/recent', methods=['GET'])
@login_required
def get_recent_analysis():
    """
    Obtiene los análisis recientes para un ejercicio específico.
    
    Si se proporciona subject_id -> Busca en rom_session (historial del sujeto)
    Si NO hay subject_id -> Busca en user_analysis_history (auto-análisis del usuario)
    
    Query params:
        segment: str - Segmento (requerido)
        exercise_type: str - Tipo de ejercicio (requerido)
        subject_id: int - ID del sujeto (opcional, para análisis de sujeto)
        limit: int - Cantidad de resultados (default 10)
        
    Returns:
        JSON con lista de análisis recientes
    """
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuario no autenticado'
            }), 401
        
        # Obtener parámetros
        segment = request.args.get('segment')
        exercise_type = request.args.get('exercise_type')
        subject_id = request.args.get('subject_id')
        limit = int(request.args.get('limit', 10))
        
        if not segment or not exercise_type:
            return jsonify({
                'success': False,
                'error': 'Se requiere segment y exercise_type'
            }), 400
        
        from database.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # ============================================================
        # RUTA 1: Historial de SUJETO -> Buscar en rom_session
        # ============================================================
        if subject_id:
            logger.info(f"📊 Obteniendo historial de SUJETO: subject_id={subject_id}, segment={segment}")
            
            # Verificar acceso al sujeto
            user_role = session.get('role', 'student')
            if not db_manager.can_user_access_subject(user_id, int(subject_id), user_role):
                return jsonify({
                    'success': False,
                    'error': 'No tiene permisos para ver este sujeto'
                }), 403
            
            recent = db_manager.get_recent_sessions_for_subject(
                subject_id=int(subject_id),
                segment=segment,
                exercise_type=exercise_type,
                limit=limit
            )
        # ============================================================
        # RUTA 2: AUTO-ANÁLISIS -> Buscar en user_analysis_history
        # ============================================================
        else:
            logger.info(f"📊 Obteniendo AUTO-ANÁLISIS: user_id={user_id}, segment={segment}")
            
            recent = db_manager.get_recent_history_for_exercise(
                user_id=user_id,
                segment=segment,
                exercise_type=exercise_type,
                limit=limit
            )
        
        return jsonify({
            'success': True,
            'count': len(recent),
            'recent': recent,
            'is_subject_history': bool(subject_id)
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener análisis recientes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ENDPOINTS DE SESIÓN DE ANÁLISIS ROM (NUEVO FLUJO CON ESTADOS)
# ============================================================================

@api_bp.route('/session/start', methods=['POST'])
@login_required
def start_session():
    """
    Inicia una nueva sesión de análisis ROM con el flujo controlado por estados.
    
    Estados: IDLE → DETECTING_PERSON → CHECKING_ORIENTATION → CHECKING_POSTURE 
             → COUNTDOWN → ANALYZING → COMPLETED
    
    Body JSON:
        exercise_id: ID del ejercicio (ej: 'shoulder_flexion_right')
        suppress_tts_result: bool - Si True, suprime TTS del resultado (para bilateral secuencial)
        
    Returns:
        JSON con estado inicial de la sesión
    """
    from app.core.analysis_session import create_analysis_session, AnalysisState
    
    print(f"\n{'='*60}")
    print(f"[API] /api/session/start LLAMADO!")
    print(f"{'='*60}")
    
    try:
        data = request.get_json() or {}
        exercise_id = data.get('exercise_id', '')
        suppress_tts_result = data.get('suppress_tts_result', False)
        print(f"[API] exercise_id recibido: {exercise_id}, suppress_tts: {suppress_tts_result}")
        
        # Parsear exercise_id para extraer joint_type, movement_type y orientation
        # Formato esperado: 'shoulder_flexion_right' o 'shoulder_abduction_bilateral'
        parts = exercise_id.split('_')
        
        if len(parts) < 2:
            return jsonify({
                'success': False,
                'error': 'exercise_id inválido. Formato: segment_movement_side'
            }), 400
        
        joint_type = parts[0]  # 'shoulder', 'elbow', etc.
        movement_type = parts[1] if len(parts) > 1 else 'flexion'
        
        # Determinar orientación requerida según el ejercicio
        orientation_map = {
            'flexion': 'profile',
            'extension': 'profile', 
            'abduction': 'frontal',
            'adduction': 'frontal',
            'rotation': 'frontal'
        }
        required_orientation = orientation_map.get(movement_type, 'profile')
        
        # Crear nueva sesión
        print(f"[API] Creando AnalysisSession para: {joint_type}/{movement_type}/{required_orientation}")
        analysis_session = create_analysis_session(
            joint_type=joint_type,
            movement_type=movement_type,
            required_orientation=required_orientation
        )
        print(f"[API] AnalysisSession creada: {analysis_session}")
        
        # 🦵 Configurar suppress_tts_result si viene en la petición
        if suppress_tts_result:
            analysis_session.suppress_tts_result = True
            print(f"[API] suppress_tts_result activado (modo bilateral secuencial)")
        
        # ✅ IMPORTANTE: Resetear el analyzer actual para nueva medición
        # Esto asegura que left_max_rom y right_max_rom empiecen en 0
        current_analyzer = get_current_analyzer()
        if current_analyzer and hasattr(current_analyzer, 'reset'):
            current_analyzer.reset()
            current_app.logger.info(f"[SESSION_START] Analyzer reseteado para nueva medición")
        
        # Iniciar la sesión
        print(f"[API] Llamando analysis_session.start()...")
        analysis_session.start()
        print(f"[API] Sesión iniciada! Estado: {analysis_session.state.name}")
        
        return jsonify({
            'success': True,
            'message': 'Sesión de análisis iniciada',
            'session': {
                'state': analysis_session.state.name,
                'message': analysis_session.state_message,
                'joint_type': joint_type,
                'movement_type': movement_type,
                'required_orientation': required_orientation
            }
        }), 200
        
    except Exception as e:
        print(f"[API] ERROR en /api/session/start: {e}")
        import traceback
        traceback.print_exc()
        current_app.logger.error(f"Error al iniciar sesión: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/session/set_leg', methods=['POST'])
@login_required
def set_selected_leg():
    """
    Configura qué pierna analizar en el analyzer actual (para hip abduction).
    
    Body JSON:
        leg: 'left' | 'right' | 'both'
        suppress_tts: bool - Si True, suprime el TTS del resultado (para modo bilateral secuencial)
        
    Returns:
        JSON con resultado de la operación
    """
    from app.core.analysis_session import get_current_session
    
    try:
        data = request.get_json() or {}
        leg = data.get('leg', 'both')
        suppress_tts = data.get('suppress_tts', False)
        
        if leg not in ['left', 'right', 'both']:
            return jsonify({
                'success': False,
                'error': f"Valor de 'leg' inválido: {leg}. Debe ser 'left', 'right' o 'both'"
            }), 400
        
        # Obtener analyzer actual
        current_analyzer = get_current_analyzer()
        
        if current_analyzer is None:
            return jsonify({
                'success': False,
                'error': 'No hay analyzer activo'
            }), 400
        
        # Verificar que el analyzer soporte selected_leg
        if hasattr(current_analyzer, 'selected_leg'):
            current_analyzer.selected_leg = leg
            current_app.logger.info(f"[SESSION] Pierna configurada: {leg}")
            
            # Configurar suppress_tts en la sesión de análisis
            analysis_session = get_current_session()
            if analysis_session and hasattr(analysis_session, 'suppress_tts_result'):
                analysis_session.suppress_tts_result = suppress_tts
                current_app.logger.info(f"[SESSION] suppress_tts_result: {suppress_tts}")
            
            return jsonify({
                'success': True,
                'message': f'Pierna configurada: {leg}',
                'selected_leg': leg,
                'suppress_tts': suppress_tts
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'El analyzer actual no soporta selección de pierna'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error al configurar pierna: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/session/status', methods=['GET'])
@login_required
def get_session_status():
    """
    Obtiene el estado actual de la sesión de análisis Y procesa el frame actual.
    
    Este endpoint hace doble función:
    1. Procesa el frame actual del analyzer para avanzar la máquina de estados
    2. Retorna el estado actualizado
    
    Endpoint de polling - el frontend llama cada 300-500ms.
    
    Returns:
        JSON con estado completo de la sesión
    """
    from app.core.analysis_session import get_current_session
    
    try:
        analysis_session = get_current_session()
        
        if analysis_session is None:
            return jsonify({
                'success': False,
                'error': 'No hay sesión activa',
                'session': None
            }), 200
        
        # Obtener analyzer actual del cache
        current_analyzer = get_current_analyzer()
        
        # DEBUG: Verificar estado del analyzer
        current_state = analysis_session.state.name
        if current_state in ['ANALYZING', 'CHECKING_ORIENTATION', 'DETECTING_PERSON']:
            import random
            if random.random() < 0.2:  # 20% de las veces
                logger.info(f"[SESSION_STATUS] state={current_state}, analyzer={'EXISTS' if current_analyzer else 'NONE'}, analyzer_type={_current_analyzer_type}")
        
        # Si la sesión está activa, procesar con datos del analyzer actual
        if analysis_session.is_active and current_analyzer is not None:
            # Obtener datos del analyzer
            analyzer_data = current_analyzer.get_current_data() if hasattr(current_analyzer, 'get_current_data') else {}
            
            # Extraer datos relevantes
            landmarks_detected = analyzer_data.get('landmarks_detected', False)
            landmarks = True if landmarks_detected else None
            
            # Obtener ángulo - usar valor ABSOLUTO para ROM (el signo indica dirección, no magnitud)
            raw_angle = analyzer_data.get('angle') or analyzer_data.get('current_angle')
            current_angle = abs(raw_angle) if raw_angle is not None else None
            
            raw_orientation = analyzer_data.get('orientation', '')
            confidence = analyzer_data.get('confidence', 0.0)
            is_profile = analyzer_data.get('is_profile_position', False)
            orientation_quality = analyzer_data.get('orientation_quality', 0.0)
            
            # DEBUG: Log más frecuente para CHECKING_ORIENTATION
            current_state = analysis_session.state.name
            if current_state == 'CHECKING_ORIENTATION':
                import random
                if random.random() < 0.3:  # 30% de las veces
                    logger.info(f"[ORIENTATION_DEBUG] orientation='{raw_orientation}', is_profile={is_profile}, quality={orientation_quality:.2f}, confidence={confidence:.2f}")
            
            # DEBUG: Log para ANALYZING
            if current_state == 'ANALYZING':
                import random
                if random.random() < 0.2:  # 20% de las veces
                    logger.info(f"[ANALYZING_DEBUG] angle={current_angle}, landmarks_detected={landmarks_detected}")
                
                # Actualizar datos bilaterales si es frontal (usar ángulos ACTUALES, no máximos)
                if hasattr(current_analyzer, 'left_angle') and hasattr(current_analyzer, 'right_angle'):
                    analysis_session.update_bilateral_data(
                        current_analyzer.left_angle,
                        current_analyzer.right_angle
                    )
            
            # Ahora el analyzer devuelve 'profile' o 'frontal' directamente
            # Solo necesitamos pasar lo que dice el analyzer
            orientation = raw_orientation.lower() if raw_orientation else None
            
            # Fallback para valores legacy ("mirando izquierda", etc.)
            if orientation and orientation not in ['profile', 'frontal']:
                if 'mirando' in orientation or 'izquierda' in orientation or 'derecha' in orientation:
                    orientation = 'profile'
                elif 'frente' in orientation:
                    orientation = 'frontal'
            
            # Obtener el lado detectado del analyzer (left, right, o bilateral)
            detected_side = analyzer_data.get('side', None)
            # Normalizar el valor del lado
            if detected_side and detected_side not in ('left', 'right', 'bilateral'):
                detected_side = None  # Ignorar valores como "Detectando..."
            
            # Procesar frame en la máquina de estados (ahora incluye confidence y side)
            process_result = analysis_session.process_frame(
                landmarks=landmarks,
                current_angle=current_angle,
                detected_orientation=orientation,
                confidence=confidence,
                side=detected_side
            )
        
        # Obtener estado actualizado
        status = analysis_session.get_status()
        
        # Enriquecer mensaje para frontal durante ANALYZING (mostrar ambos ángulos)
        if status.get('state') == 'ANALYZING' and current_analyzer is not None:
            if hasattr(current_analyzer, 'left_angle') and hasattr(current_analyzer, 'right_angle'):
                # Es un analyzer frontal con ángulos bilaterales
                left = current_analyzer.left_angle
                right = current_analyzer.right_angle
                status['message'] = f"Izq: {left:.1f}° | Der: {right:.1f}°"
        
        return jsonify({
            'success': True,
            'session': status
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error al obtener estado de sesión: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/session/stop', methods=['POST'])
@login_required  
def stop_session():
    """
    Detiene la sesión de análisis actual.
    
    Si estaba en estado ANALYZING, intenta generar un resultado parcial.
    
    Returns:
        JSON con resultado final (si aplica)
    """
    from app.core.analysis_session import get_current_session, clear_current_session
    
    try:
        analysis_session = get_current_session()
        
        if analysis_session is None:
            return jsonify({
                'success': False,
                'error': 'No hay sesión activa para detener'
            }), 200
        
        # Detener sesión y obtener resultado
        result = analysis_session.stop()
        
        # Limpiar sesión
        clear_current_session()
        
        return jsonify({
            'success': True,
            'message': 'Sesión detenida',
            'result': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error al detener sesión: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/session/process_frame', methods=['POST'])
@login_required
def process_session_frame():
    """
    Procesa un frame y avanza la máquina de estados de la sesión.
    
    Este endpoint es llamado desde el video_feed loop para actualizar
    el estado de la sesión con los datos del frame actual.
    
    Body JSON:
        landmarks_detected: bool - Si se detectaron landmarks
        current_angle: float - Ángulo actual medido
        orientation: str - Orientación detectada ('frontal' o 'profile')
    
    Returns:
        JSON con estado actualizado
    """
    from app.core.analysis_session import get_current_session
    
    try:
        analysis_session = get_current_session()
        
        if analysis_session is None or not analysis_session.is_active:
            return jsonify({
                'success': False,
                'active': False,
                'error': 'No hay sesión activa'
            }), 200
        
        data = request.get_json() or {}
        
        # Procesar frame con los datos recibidos
        result = analysis_session.process_frame(
            landmarks=data.get('landmarks_detected', False),
            current_angle=data.get('current_angle'),
            detected_orientation=data.get('orientation')
        )
        
        return jsonify({
            'success': True,
            'active': True,
            'frame_result': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error al procesar frame de sesión: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
