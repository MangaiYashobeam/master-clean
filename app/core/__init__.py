"""
Biomechanical Analysis Core Module
==================================

Este módulo contiene los componentes centrales del sistema de análisis:
- pose_singleton: Instancia compartida de MediaPipe
- orientation_detector: Detección de orientación del paciente
- mediapipe_config: Configuración optimizada de MediaPipe
- camera_manager: Gestión de cámara

NOTA: BaseJointAnalyzer está en app/analyzers/, NO aquí.
"""

__version__ = "1.0.0"
__author__ = "Proyecto Biomecánico"

# NO importar módulos aquí para evitar imports circulares
# Los módulos se importan directamente donde se necesitan:
#   from app.core.pose_singleton import get_shared_pose
#   from app.core.orientation_detector import AdaptiveOrientationDetector