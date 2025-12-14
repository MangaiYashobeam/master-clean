"""
🌐 VPS MEDIAPIPE ENGINE - Motor dedicado para procesamiento en VPS
===================================================================

Este módulo maneja el procesamiento de MediaPipe específicamente para
el modo VPS donde los frames vienen del navegador del cliente.

CARACTERÍSTICAS:
- Singleton de MediaPipe optimizado para VPS (model_complexity=0)
- Dibuja skeleton SIEMPRE (no depende de show_skeleton flag)
- Retorna datos de análisis completos
- Manejo robusto de errores

Autor: BIOTRACK Team
Fecha: 2025-12-14
"""

import cv2
import numpy as np
import mediapipe as mp
import math
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# SINGLETON GLOBAL DE MEDIAPIPE PARA VPS
# ============================================================================

_vps_pose_instance = None
_vps_drawing_utils = None
_vps_drawing_styles = None


def get_vps_pose():
    """Obtiene instancia de MediaPipe Pose optimizada para VPS"""
    global _vps_pose_instance, _vps_drawing_utils, _vps_drawing_styles
    
    if _vps_pose_instance is None:
        logger.info("🔧 [VPS Engine] Inicializando MediaPipe Pose para VPS...")
        
        _vps_pose_instance = mp.solutions.pose.Pose(
            static_image_mode=False,           # Video mode (tracking)
            model_complexity=0,                # LITE model para VPS
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        _vps_drawing_utils = mp.solutions.drawing_utils
        _vps_drawing_styles = mp.solutions.drawing_styles
        
        logger.info("✅ [VPS Engine] MediaPipe Pose inicializado correctamente")
    
    return _vps_pose_instance, _vps_drawing_utils, _vps_drawing_styles


class VPSMediaPipeEngine:
    """
    Motor de MediaPipe dedicado para procesamiento VPS
    
    Procesa frames del navegador del cliente y retorna:
    - Frame con skeleton dibujado
    - Datos de análisis (ángulos, landmarks, etc.)
    """
    
    # Mapeo de ejercicios a landmarks relevantes
    EXERCISE_LANDMARKS = {
        'shoulder_profile': {
            'joints': ['LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST', 
                      'RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST',
                      'LEFT_HIP', 'RIGHT_HIP'],
            'angle_points': {
                'left': ('LEFT_HIP', 'LEFT_SHOULDER', 'LEFT_ELBOW'),
                'right': ('RIGHT_HIP', 'RIGHT_SHOULDER', 'RIGHT_ELBOW')
            }
        },
        'shoulder_frontal': {
            'joints': ['LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST',
                      'RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST',
                      'LEFT_HIP', 'RIGHT_HIP'],
            'angle_points': {
                'left': ('LEFT_HIP', 'LEFT_SHOULDER', 'LEFT_ELBOW'),
                'right': ('RIGHT_HIP', 'RIGHT_SHOULDER', 'RIGHT_ELBOW')
            }
        },
        'elbow_profile': {
            'joints': ['LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST',
                      'RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST'],
            'angle_points': {
                'left': ('LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST'),
                'right': ('RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST')
            }
        },
        'hip_profile': {
            'joints': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE',
                      'RIGHT_SHOULDER', 'RIGHT_HIP', 'RIGHT_KNEE'],
            'angle_points': {
                'left': ('LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE'),
                'right': ('RIGHT_SHOULDER', 'RIGHT_HIP', 'RIGHT_KNEE')
            }
        },
        'hip_frontal': {
            'joints': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE',
                      'RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE'],
            'angle_points': {
                'left': ('LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE'),
                'right': ('RIGHT_SHOULDER', 'RIGHT_HIP', 'RIGHT_KNEE')
            }
        },
        'knee_profile': {
            'joints': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE',
                      'RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE'],
            'angle_points': {
                'left': ('LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE'),
                'right': ('RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE')
            }
        },
        'ankle_profile': {
            'joints': ['LEFT_KNEE', 'LEFT_ANKLE', 'LEFT_FOOT_INDEX',
                      'RIGHT_KNEE', 'RIGHT_ANKLE', 'RIGHT_FOOT_INDEX'],
            'angle_points': {
                'left': ('LEFT_KNEE', 'LEFT_ANKLE', 'LEFT_FOOT_INDEX'),
                'right': ('RIGHT_KNEE', 'RIGHT_ANKLE', 'RIGHT_FOOT_INDEX')
            }
        }
    }
    
    def __init__(self):
        self.pose, self.mp_draw, self.mp_styles = get_vps_pose()
        self.mp_pose = mp.solutions.pose
        
        # Estado del análisis
        self.current_angle = 0
        self.min_angle = 180
        self.max_angle = 0
        self.landmarks_detected = False
        self.active_side = 'right'
        
        logger.info("✅ [VPS Engine] VPSMediaPipeEngine inicializado")
    
    def process_frame(self, frame: np.ndarray, exercise_type: str = 'shoulder_profile') -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Procesa un frame con MediaPipe y dibuja el skeleton
        
        Args:
            frame: Frame BGR de OpenCV
            exercise_type: Tipo de ejercicio para calcular ángulos
            
        Returns:
            Tuple[frame_con_skeleton, datos_analisis]
        """
        try:
            # Convertir BGR a RGB para MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Procesar con MediaPipe
            results = self.pose.process(frame_rgb)
            
            # Inicializar datos de análisis
            analysis_data = {
                'landmarks_detected': False,
                'angle': 0,
                'min_angle': self.min_angle,
                'max_angle': self.max_angle,
                'side': self.active_side,
                'exercise_type': exercise_type,
                'rom': 0
            }
            
            if results.pose_landmarks:
                self.landmarks_detected = True
                analysis_data['landmarks_detected'] = True
                
                # SIEMPRE dibujar el skeleton completo
                self._draw_full_skeleton(frame, results.pose_landmarks)
                
                # Calcular ángulo según el ejercicio
                angle = self._calculate_exercise_angle(
                    results.pose_landmarks, 
                    exercise_type,
                    frame
                )
                
                if angle is not None:
                    self.current_angle = angle
                    
                    # Actualizar min/max
                    if angle < self.min_angle:
                        self.min_angle = angle
                    if angle > self.max_angle:
                        self.max_angle = angle
                    
                    # Calcular ROM
                    rom = self.max_angle - self.min_angle
                    
                    analysis_data.update({
                        'angle': round(angle, 1),
                        'min_angle': round(self.min_angle, 1),
                        'max_angle': round(self.max_angle, 1),
                        'rom': round(rom, 1)
                    })
                    
                    # Dibujar ángulo en el frame
                    self._draw_angle_display(frame, angle, exercise_type)
            else:
                self.landmarks_detected = False
                # Dibujar mensaje de "No detectado"
                cv2.putText(frame, "Persona no detectada", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            return frame, analysis_data
            
        except Exception as e:
            logger.error(f"[VPS Engine] Error procesando frame: {e}")
            import traceback
            traceback.print_exc()
            return frame, {'error': str(e), 'landmarks_detected': False}
    
    def _draw_full_skeleton(self, frame: np.ndarray, landmarks):
        """Dibuja el skeleton completo de MediaPipe"""
        try:
            # Dibujar conexiones del cuerpo
            self.mp_draw.draw_landmarks(
                frame,
                landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_styles.get_default_pose_landmarks_style(),
                connection_drawing_spec=self.mp_draw.DrawingSpec(
                    color=(0, 255, 0),  # Verde para conexiones
                    thickness=2,
                    circle_radius=2
                )
            )
            
            # Dibujar puntos clave con colores más visibles
            h, w = frame.shape[:2]
            for idx, landmark in enumerate(landmarks.landmark):
                if landmark.visibility > 0.5:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    
                    # Punto grande y visible
                    cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)  # Amarillo relleno
                    cv2.circle(frame, (x, y), 8, (0, 0, 0), 2)  # Borde negro
                    
        except Exception as e:
            logger.error(f"[VPS Engine] Error dibujando skeleton: {e}")
    
    def _calculate_exercise_angle(self, landmarks, exercise_type: str, frame: np.ndarray) -> Optional[float]:
        """Calcula el ángulo según el tipo de ejercicio"""
        try:
            config = self.EXERCISE_LANDMARKS.get(exercise_type, self.EXERCISE_LANDMARKS['shoulder_profile'])
            angle_points = config.get('angle_points', {})
            
            h, w = frame.shape[:2]
            
            # Determinar qué lado usar (el más visible)
            left_points = angle_points.get('left')
            right_points = angle_points.get('right')
            
            left_visibility = 0
            right_visibility = 0
            
            if left_points:
                for point_name in left_points:
                    idx = getattr(self.mp_pose.PoseLandmark, point_name)
                    left_visibility += landmarks.landmark[idx].visibility
                left_visibility /= len(left_points)
            
            if right_points:
                for point_name in right_points:
                    idx = getattr(self.mp_pose.PoseLandmark, point_name)
                    right_visibility += landmarks.landmark[idx].visibility
                right_visibility /= len(right_points)
            
            # Usar el lado más visible
            if left_visibility > right_visibility:
                points = left_points
                self.active_side = 'left'
            else:
                points = right_points
                self.active_side = 'right'
            
            if not points:
                return None
            
            # Obtener coordenadas de los 3 puntos
            coords = []
            for point_name in points:
                idx = getattr(self.mp_pose.PoseLandmark, point_name)
                lm = landmarks.landmark[idx]
                if lm.visibility < 0.5:
                    return None
                coords.append([lm.x * w, lm.y * h])
            
            # Calcular ángulo
            angle = self._calculate_angle(coords[0], coords[1], coords[2])
            
            # Dibujar arco del ángulo
            self._draw_angle_arc(frame, coords[0], coords[1], coords[2], angle)
            
            return angle
            
        except Exception as e:
            logger.error(f"[VPS Engine] Error calculando ángulo: {e}")
            return None
    
    def _calculate_angle(self, p1, p2, p3) -> float:
        """Calcula el ángulo entre 3 puntos (p2 es el vértice)"""
        v1 = np.array(p1) - np.array(p2)
        v2 = np.array(p3) - np.array(p2)
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return np.degrees(angle)
    
    def _draw_angle_arc(self, frame: np.ndarray, p1, p2, p3, angle: float):
        """Dibuja un arco visual del ángulo"""
        try:
            center = (int(p2[0]), int(p2[1]))
            
            v1 = np.array(p1) - np.array(p2)
            v2 = np.array(p3) - np.array(p2)
            
            angle1 = math.degrees(math.atan2(v1[1], v1[0]))
            angle2 = math.degrees(math.atan2(v2[1], v2[0]))
            
            if angle2 < angle1:
                angle1, angle2 = angle2, angle1
            
            # Dibujar arco
            cv2.ellipse(frame, center, (40, 40), 0, angle1, angle2, (255, 255, 0), 2)
            
            # Dibujar líneas del ángulo
            cv2.line(frame, center, (int(p1[0]), int(p1[1])), (255, 0, 255), 2)
            cv2.line(frame, center, (int(p3[0]), int(p3[1])), (255, 0, 255), 2)
            
        except Exception as e:
            pass  # No crítico si falla
    
    def _draw_angle_display(self, frame: np.ndarray, angle: float, exercise_type: str):
        """Dibuja el display del ángulo en el frame"""
        h, w = frame.shape[:2]
        
        # Fondo semi-transparente para el texto
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (250, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Texto del ángulo actual
        cv2.putText(frame, f"Angulo: {angle:.1f}", (20, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Min/Max
        cv2.putText(frame, f"Min: {self.min_angle:.1f}", (20, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Max: {self.max_angle:.1f}", (130, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # ROM
        rom = self.max_angle - self.min_angle
        cv2.putText(frame, f"ROM: {rom:.1f}", (20, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Lado activo
        cv2.putText(frame, f"Lado: {self.active_side}", (130, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def reset(self):
        """Reinicia los valores de análisis"""
        self.min_angle = 180
        self.max_angle = 0
        self.current_angle = 0
        logger.info("[VPS Engine] Valores reseteados")


# ============================================================================
# INSTANCIA GLOBAL DEL ENGINE
# ============================================================================

_vps_engine_instance = None


def get_vps_engine() -> VPSMediaPipeEngine:
    """Obtiene la instancia singleton del engine VPS"""
    global _vps_engine_instance
    
    if _vps_engine_instance is None:
        logger.info("🔧 [VPS Engine] Creando instancia VPSMediaPipeEngine...")
        _vps_engine_instance = VPSMediaPipeEngine()
    
    return _vps_engine_instance
