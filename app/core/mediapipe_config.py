"""
🎯 CONFIGURACIÓN OPTIMIZADA DE MEDIAPIPE PARA DIFERENTES ENTORNOS
Detecta automáticamente el entorno y configura MediaPipe apropiadamente

MODOS:
- localhost: Configuración estándar para desarrollo local
- vps: Configuración optimizada para servidores remotos (Railway, VPS, etc.)
"""
import os
import mediapipe as mp

class MediaPipeConfig:
    """Configurador inteligente de MediaPipe para diferentes entornos"""
    
    # Cache del modo actual
    _current_mode = None
    
    @staticmethod
    def get_camera_mode():
        """
        Obtiene el modo de cámara actual desde la configuración
        Prioridad: Variable de entorno > Sesión Flask > Config por defecto
        """
        # 1. Variable de entorno tiene prioridad
        env_mode = os.environ.get('CAMERA_MODE')
        if env_mode:
            return env_mode.lower()
        
        # 2. Intentar obtener de Flask config/session
        try:
            from flask import current_app, session
            # Primero verificar sesión (configuración del usuario)
            if session and session.get('camera_mode'):
                return session.get('camera_mode').lower()
            # Luego config de la app
            if current_app and current_app.config.get('CAMERA_MODE'):
                return current_app.config.get('CAMERA_MODE').lower()
        except:
            pass
        
        # 3. Default: detectar automáticamente
        return MediaPipeConfig._auto_detect_mode()
    
    @staticmethod
    def _auto_detect_mode():
        """
        Detecta automáticamente si estamos en VPS o localhost
        """
        # Indicadores de entorno VPS/Railway/producción
        vps_indicators = [
            os.getenv('RAILWAY_ENVIRONMENT') == 'production',
            os.getenv('PORT') is not None,
            os.getenv('RAILWAY_PROJECT_ID') is not None,
            os.getenv('RAILWAY_SERVICE_ID') is not None,
            os.getenv('FLASK_ENV') == 'production',
            os.getenv('PRODUCTION') == 'true',
            # Detectar si NO hay display (servidor headless)
            os.getenv('DISPLAY') is None and os.name != 'nt',
        ]
        
        if any(vps_indicators):
            return 'vps'
        return 'localhost'
    
    @staticmethod
    def is_vps_mode():
        """Verifica si estamos en modo VPS"""
        return MediaPipeConfig.get_camera_mode() == 'vps'
    
    @staticmethod
    def is_localhost_mode():
        """Verifica si estamos en modo localhost"""
        return MediaPipeConfig.get_camera_mode() == 'localhost'
    
    @staticmethod
    def is_railway_environment():
        """Detecta si estamos ejecutando en Railway (legacy, usa is_vps_mode)"""
        return MediaPipeConfig.is_vps_mode()
    
    @staticmethod
    def create_pose_detector():
        """
        Crea un detector de pose optimizado según el entorno
        VPS = CPU only, configuración ligera
        LocalHost = Configuración estándar
        """
        mode = MediaPipeConfig.get_camera_mode()
        
        if mode == 'vps':
            print("🌐 Modo VPS detectado - Configurando MediaPipe para servidor remoto (CPU)")
            # Configuración CPU-only optimizada para VPS
            # Menor complejidad y confianza para mejor rendimiento
            pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # LITE: Más rápido en CPU
                smooth_landmarks=True,
                min_detection_confidence=0.3,  # Bajo para mejor detección
                min_tracking_confidence=0.3,   # Bajo para mejor tracking
                enable_segmentation=False
            )
        else:
            print("💻 Modo LocalHost detectado - Configuración MediaPipe estándar")
            # Configuración estándar para desarrollo local
            pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,  # FULL: Mejor precisión
                smooth_landmarks=True,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
                enable_segmentation=False
            )
        
        MediaPipeConfig._current_mode = mode
        return pose
    
    @staticmethod
    def get_optimized_settings():
        """Obtiene configuraciones optimizadas según el entorno"""
        mode = MediaPipeConfig.get_camera_mode()
        
        if mode == 'vps':
            return {
                'model_complexity': 0,  # LITE
                'min_detection_confidence': 0.3,
                'min_tracking_confidence': 0.3,
                'processing_fps': 5,  # Menor FPS en VPS
                'enable_gpu': False,
                'processing_width': 640,
                'processing_height': 480,
                'jpeg_quality': 50,
                'mode': 'vps'
            }
        else:
            return {
                'model_complexity': 1,  # FULL
                'min_detection_confidence': 0.7,
                'min_tracking_confidence': 0.7,
                'processing_fps': 15,  # Mayor FPS local
                'enable_gpu': True,
                'processing_width': 960,
                'processing_height': 540,
                'jpeg_quality': 60,
                'mode': 'localhost'
            }
    
    @staticmethod
    def get_camera_settings():
        """
        Obtiene configuración de cámara según el modo
        VPS: Configuración para WebRTC/cliente remoto
        LocalHost: Configuración para cámara local
        """
        mode = MediaPipeConfig.get_camera_mode()
        
        if mode == 'vps':
            return {
                'mode': 'vps',
                'source': 'client_webrtc',
                'processing_width': 640,
                'processing_height': 480,
                'jpeg_quality': 50,
                'target_fps': 5,
                'description': 'Cámara del navegador cliente - Procesamiento en servidor VPS'
            }
        else:
            return {
                'mode': 'localhost',
                'source': 'server_local',
                'processing_width': 960,
                'processing_height': 540,
                'jpeg_quality': 60,
                'target_fps': 15,
                'description': 'Cámara local del servidor - Procesamiento local'
            }