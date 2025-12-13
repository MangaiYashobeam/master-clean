"""
⚙️ CONFIGURACIÓN DE LA APLICACIÓN FLASK - BIOTRACK
====================================================
Configuración centralizada para la aplicación Flask

ENTORNOS:
- Development: Desarrollo local con debug
- Production: Producción sin debug
- Testing: Tests automáticos

Autor: BIOTRACK Team
Fecha: 2025-11-14
"""

import os
from pathlib import Path
from datetime import timedelta


# ============================================================================
# RUTAS BASE
# ============================================================================

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorio de la aplicación
APP_DIR = BASE_DIR / 'app'

# Directorio de la base de datos
DATABASE_DIR = BASE_DIR / 'database'

# Directorio de instancia (uploads, logs, etc.)
INSTANCE_DIR = BASE_DIR / 'instance'


# ============================================================================
# CLASE DE CONFIGURACIÓN BASE
# ============================================================================

class Config:
    """Configuración base para todas las configuraciones"""
    
    # ========================================================================
    # CONFIGURACIÓN GENERAL DE FLASK
    # ========================================================================
    
    # Clave secreta para sesiones y CSRF (CAMBIAR EN PRODUCCIÓN)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'biotrack-secret-key-change-in-production-2025'
    
    # Nombre de la aplicación
    APP_NAME = 'BIOTRACK'
    
    # Versión
    VERSION = '10.0 CLEAN'
    
    # ========================================================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ========================================================================
    
    # Ruta a la base de datos SQLite
    DATABASE_PATH = str(DATABASE_DIR / 'biotrack.db')
    
    # URI de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # Desactivar track modifications (mejora performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Echo SQL queries (solo en desarrollo)
    SQLALCHEMY_ECHO = False
    
    # ========================================================================
    # CONFIGURACIÓN DE SESIONES
    # ========================================================================
    
    # Tiempo de vida de la sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Cookie de sesión
    SESSION_COOKIE_NAME = 'biotrack_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ========================================================================
    # CONFIGURACIÓN DE UPLOADS
    # ========================================================================
    
    # Directorio de uploads
    UPLOAD_FOLDER = str(APP_DIR / 'static' / 'uploads')
    
    # Tamaño máximo de archivo (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Extensiones permitidas para imágenes
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Extensiones permitidas para videos
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm'}
    
    # ========================================================================
    # CONFIGURACIÓN DE LOGGING
    # ========================================================================
    
    # Directorio de logs
    LOG_DIR = str(INSTANCE_DIR / 'logs')
    
    # Nivel de logging
    LOG_LEVEL = 'INFO'
    
    # Formato de logs
    LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    
    # Archivo de log principal
    LOG_FILE = str(Path(LOG_DIR) / 'biotrack.log')
    
    # Archivo de log de errores
    ERROR_LOG_FILE = str(Path(LOG_DIR) / 'errors.log')
    
    # Rotación de logs (max 10 MB, 5 backups)
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5
    
    # ========================================================================
    # CONFIGURACIÓN DE MEDIAPIPE
    # ========================================================================
    
    # Confianza mínima de detección
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.5
    
    # Confianza mínima de tracking
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
    
    # Complejidad del modelo (0=Lite, 1=Full, 2=Heavy)
    MEDIAPIPE_MODEL_COMPLEXITY = 1  # CPU optimizado
    
    # ========================================================================
    # CONFIGURACIÓN DE CÁMARA
    # ========================================================================
    
    # 🌐 MODO DE CÁMARA: 'localhost' o 'vps'
    # - localhost: Cámara local del navegador, procesamiento en servidor local
    # - vps: Cámara del cliente (WebRTC), procesamiento optimizado para servidor remoto
    CAMERA_MODE = os.environ.get('CAMERA_MODE', 'localhost')
    
    # Índice de cámara por defecto (0=integrada, 1+=externa)
    CAMERA_INDEX = 0
    
    # Resolución de cámara por defecto (para adquisición)
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720
    
    # Resolución de procesamiento (para análisis - menor = más rápido)
    CAMERA_PROCESSING_WIDTH = 960
    CAMERA_PROCESSING_HEIGHT = 540
    
    # FPS objetivo
    CAMERA_FPS = 30
    
    # Calidad JPEG para streaming (1-100, menor = más rápido, menos calidad)
    JPEG_QUALITY = 60
    
    # Resoluciones disponibles para selección
    AVAILABLE_RESOLUTIONS = [
        {'label': '480p (SD)', 'width': 854, 'height': 480},
        {'label': '540p', 'width': 960, 'height': 540},
        {'label': '720p (HD)', 'width': 1280, 'height': 720},
        {'label': '1080p (Full HD)', 'width': 1920, 'height': 1080},
    ]
    
    # Calidades JPEG disponibles
    AVAILABLE_JPEG_QUALITIES = [
        {'label': 'Bajo (rápido)', 'value': 40},
        {'label': 'Medio', 'value': 60},
        {'label': 'Alto', 'value': 80},
        {'label': 'Máximo', 'value': 95},
    ]
    
    # ========================================================================
    # CONFIGURACIÓN DE ESP32 (Control de altura de cámara)
    # ========================================================================
    
    # Puerto serial (detectado automáticamente si es None)
    ESP32_PORT = None
    
    # Baudrate
    ESP32_BAUDRATE = 115200
    
    # Timeout de conexión (segundos)
    ESP32_TIMEOUT = 5
    
    # ========================================================================
    # CONFIGURACIÓN DE VOZ GUIADA
    # ========================================================================
    
    # Habilitar sistema de voz
    VOICE_ENABLED = True
    
    # Motor TTS (pyttsx3 o gTTS)
    TTS_ENGINE = 'pyttsx3'  # Offline por defecto
    
    # Velocidad de habla (palabras por minuto)
    TTS_RATE = 150
    
    # Volumen (0.0 a 1.0)
    TTS_VOLUME = 0.9
    
    # Intervalo mínimo entre mensajes (segundos)
    VOICE_MIN_INTERVAL = 3.0
    
    # Directorio de cache de audio
    AUDIO_CACHE_DIR = str(APP_DIR / 'static' / 'audio_cache')
    
    # ========================================================================
    # CONFIGURACIÓN DE ROM (Rango de Movimiento)
    # ========================================================================
    
    # Segmentos corporales disponibles
    AVAILABLE_SEGMENTS = ['ankle', 'knee', 'hip', 'shoulder', 'elbow']
    
    # Tipos de ejercicio por segmento
    EXERCISE_TYPES = {
        'ankle': ['dorsiflexion', 'plantarflexion'],
        'knee': ['flexion', 'extension'],
        'hip': ['flexion', 'extension', 'abduction', 'adduction'],
        'shoulder': ['flexion', 'extension', 'abduction', 'adduction', 'external_rotation', 'internal_rotation'],
        'elbow': ['flexion', 'extension']
    }
    
    # Vistas de cámara disponibles
    CAMERA_VIEWS = ['lateral', 'frontal', 'posterior']
    
    # Lados
    SIDES = ['left', 'right', 'bilateral']
    
    # ========================================================================
    # CONFIGURACIÓN DE EXPORTS/REPORTES
    # ========================================================================
    
    # Directorio de reportes PDF
    PDF_EXPORT_DIR = str(INSTANCE_DIR / 'exports')
    
    # Formato de nombre de archivo PDF
    PDF_FILENAME_FORMAT = 'ROM_Report_{student_id}_{date}.pdf'
    
    # ========================================================================
    # CONFIGURACIÓN DE PAGINACIÓN
    # ========================================================================
    
    # Elementos por página en listados
    ITEMS_PER_PAGE = 20
    
    # ========================================================================
    # CONFIGURACIÓN DE SEGURIDAD
    # ========================================================================
    
    # Número máximo de intentos de login
    MAX_LOGIN_ATTEMPTS = 5
    
    # Tiempo de bloqueo tras intentos fallidos (minutos)
    LOGIN_LOCKOUT_DURATION = 15
    
    # Forzar HTTPS en producción
    FORCE_HTTPS = False
    
    # ========================================================================
    # CONFIGURACIÓN DE DESARROLLO
    # ========================================================================
    
    # Debug mode
    DEBUG = False
    
    # Testing mode
    TESTING = False
    
    # ========================================================================
    # USUARIOS DE PRUEBA (Solo desarrollo)
    # ========================================================================
    
    TEST_USERS = [
        {'username': 'admin', 'password': 'test123', 'role': 'admin'},
        {'username': 'carlos.mendez', 'password': 'test123', 'role': 'student'},
        {'username': 'maria.rodriguez', 'password': 'test123', 'role': 'student'},
        {'username': 'juan.garcia', 'password': 'test123', 'role': 'student'},
        {'username': 'laura.martinez', 'password': 'test123', 'role': 'student'}
    ]


# ============================================================================
# CONFIGURACIONES POR ENTORNO
# ============================================================================

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Cambiar a True para ver queries SQL
    LOG_LEVEL = 'DEBUG'
    
    # Permitir cookies en localhost sin HTTPS
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuración para producción"""
    
    DEBUG = False
    TESTING = False
    
    # Forzar HTTPS
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    
    # 🌐 VPS Mode por defecto en producción
    CAMERA_MODE = os.environ.get('CAMERA_MODE', 'vps')
    
    # Configuración optimizada para VPS
    CAMERA_PROCESSING_WIDTH = 640
    CAMERA_PROCESSING_HEIGHT = 480
    JPEG_QUALITY = 50
    
    # MediaPipe optimizado para servidor
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.3
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.3
    MEDIAPIPE_MODEL_COMPLEXITY = 0  # Lite para VPS
    
    # Clave secreta desde variable de entorno (OBLIGATORIO)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Log solo errores en producción
    LOG_LEVEL = 'ERROR'
    
    @classmethod
    def init_app(cls, app):
        """Inicialización adicional para producción"""
        
        # Asegurar que existe SECRET_KEY
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY debe estar definida en producción")


class TestingConfig(Config):
    """Configuración para tests"""
    
    TESTING = True
    DEBUG = True
    
    # Base de datos en memoria para tests
    DATABASE_PATH = ':memory:'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Desactivar CSRF en tests
    WTF_CSRF_ENABLED = False
    
    # Login sin restricciones
    MAX_LOGIN_ATTEMPTS = 999


# ============================================================================
# DICCIONARIO DE CONFIGURACIONES
# ============================================================================

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config(config_name: str = None) -> Config:
    """
    Obtiene la configuración según el nombre
    
    Args:
        config_name: 'development', 'production', 'testing', o None
    
    Returns:
        Clase de configuración
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)


def create_directories():
    """Crea los directorios necesarios si no existen"""
    directories = [
        Config.UPLOAD_FOLDER,
        Config.LOG_DIR,
        Config.AUDIO_CACHE_DIR,
        Config.PDF_EXPORT_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directorio verificado/creado: {directory}")


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == '__main__':
    # Crear directorios necesarios
    create_directories()
    
    # Mostrar configuración actual
    config_obj = get_config('development')
    
    print("=" * 70)
    print("⚙️  CONFIGURACIÓN DE BIOTRACK")
    print("=" * 70)
    print(f"Entorno: Development")
    print(f"Debug: {config_obj.DEBUG}")
    print(f"Base de datos: {config_obj.DATABASE_PATH}")
    print(f"Secret Key: {'***' if config_obj.SECRET_KEY else 'NO CONFIGURADA'}")
    print(f"Upload folder: {config_obj.UPLOAD_FOLDER}")
    print(f"Log dir: {config_obj.LOG_DIR}")
    print("=" * 70)
