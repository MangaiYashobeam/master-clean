"""
HIP FRONTAL ANALYZER - Analisis de Abduccion de Cadera
========================================================
Analizador para vista FRONTAL (medicion de abduccion de cadera)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestion de estado interno (angulos, ROM maximo)
- API publica para obtener datos actuales

SISTEMA DE MEDICION:
- Eje FIJO: Linea horizontal que pasa por ambas caderas
- Brazo MOVIL: Linea del muslo (CADERA -> RODILLA)
- 0 grados = Pierna vertical (posicion neutra de pie)
- +45 grados = Abduccion maxima (pierna separada lateralmente)

Referencias:
- AAOS: Abduccion 0-45 grados
- Kapandji (6ta ed.)

Autor: BIOTRACK Team
Fecha: 2025-12-06
Basado en: tests/test_hip_frontal.py, shoulder_frontal.py
"""

import cv2
import numpy as np
import mediapipe as mp
import time
import logging
from collections import deque
from typing import Dict, Any, Tuple, Optional

# Importar instancia compartida de MediaPipe Pose (singleton)
from app.core.pose_singleton import get_shared_pose

# Inicializar MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Logger
logger = logging.getLogger(__name__)


class HipFrontalAnalyzer:
    """
    Analizador de cadera en vista FRONTAL
    
    Mide:
    - Abduccion (pierna separandose lateralmente)
    - ROM maximo alcanzado
    
    Uso en Flask:
        analyzer = HipFrontalAnalyzer()
        
        # En loop de video stream:
        processed_frame = analyzer.process_frame(frame)
        current_data = analyzer.get_current_data()
    """
    
    def __init__(
        self, 
        processing_width: int = 640, 
        processing_height: int = 480,
        show_skeleton: bool = False,
        selected_leg: str = 'both'
    ):
        """
        Inicializa el analizador para vista FRONTAL
        
        Args:
            processing_width: Ancho para procesamiento de MediaPipe
            processing_height: Alto para procesamiento de MediaPipe
            show_skeleton: Si mostrar el skeleton completo de MediaPipe
            selected_leg: Pierna a analizar ('left', 'right', 'both')
        """
        # OPTIMIZACION: Usar instancia COMPARTIDA de MediaPipe Pose
        self.pose = get_shared_pose()
        
        # Resolucion de procesamiento
        self.processing_width = processing_width
        self.processing_height = processing_height
        
        # Pierna seleccionada
        self.selected_leg = selected_leg
        
        # Variables para tracking de angulos (bilateral)
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.current_angle = 0.0  # Angulo principal (segun pierna seleccionada)
        self.max_angle = 0.0
        self.max_left_angle = 0.0
        self.max_right_angle = 0.0
        self.side = "Detectando..."
        self.orientation = "Detectando..."
        self.confidence = 0.0
        self.frame_count = 0
        
        # Configuracion de visualizacion
        self.show_skeleton = show_skeleton
        
        # Metricas de rendimiento
        self.fps_history = deque(maxlen=30)
        self.processing_times = deque(maxlen=30)
        self.last_time = time.time()
        
        # Cache de colores
        self.color_cache = {
            'white': (255, 255, 255),
            'yellow': (0, 255, 255),
            'orange': (0, 165, 255),
            'magenta': (255, 0, 255),
            'green': (0, 255, 0),
            'cyan': (255, 255, 0),
            'blue': (255, 0, 0),
            'red': (0, 0, 255),
            'gray': (50, 50, 50),
            'light_gray': (200, 200, 200)
        }
        
        # Estado de postura
        self.posture_valid = False
        self.landmarks_detected = False
        
        # Orientacion frontal verificada
        self.is_frontal_position = False
        self.orientation_quality = 0.0
        
        logger.info("[HipFrontalAnalyzer] Inicializado con pose singleton compartido")
    
    def calculate_abduction_angle(
        self, 
        hip: Tuple[int, int], 
        knee: Tuple[int, int],
        is_left_leg: bool
    ) -> float:
        """
        Calcula el angulo de abduccion de cadera
        
        Sistema goniometro clinico estandar:
        - VERTICE: Cadera (hip)
        - Brazo FIJO: Eje vertical (perpendicular al suelo)
        - Brazo MOVIL: Linea del muslo (CADERA -> RODILLA)
        - 0 grados = Pierna vertical (posicion neutra)
        - Valores positivos = Abduccion (pierna separandose)
        
        Args:
            hip: Coordenadas (x, y) de la cadera
            knee: Coordenadas (x, y) de la rodilla
            is_left_leg: True si es pierna izquierda
        
        Returns:
            float: Angulo clinico en grados (0 = neutro, positivos = abduccion)
        """
        # Vector vertical (referencia 0 grados - apunta hacia abajo)
        vertical_down = np.array([0, 1])
        
        # Vector del muslo (CADERA -> RODILLA)
        thigh_vector = np.array([knee[0] - hip[0], knee[1] - hip[1]])
        
        # Normalizar
        thigh_norm = np.linalg.norm(thigh_vector)
        if thigh_norm == 0:
            return 0.0
        
        thigh_normalized = thigh_vector / thigh_norm
        
        # Calcular angulo con el eje vertical
        dot_product = np.dot(vertical_down, thigh_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle = np.degrees(np.arccos(dot_product))
        
        # Para abduccion, el angulo es simplemente la desviacion de la vertical
        # Solo consideramos valores positivos (abduccion)
        return float(angle)
    
    def detect_frontal_orientation(self, landmarks) -> Tuple[bool, float]:
        """
        Detecta si la persona esta de frente a la camara
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (is_frontal, confidence)
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Diferencia X entre hombros (en frontal, estan separados horizontalmente)
        shoulder_x_diff = abs(left_shoulder.x - right_shoulder.x)
        
        # Diferencia X entre caderas
        hip_x_diff = abs(left_hip.x - right_hip.x)
        
        # Visibilidad promedio
        avg_visibility = (left_shoulder.visibility + right_shoulder.visibility +
                         left_hip.visibility + right_hip.visibility) / 4
        
        # En posicion frontal, hombros y caderas estan separados horizontalmente
        # Umbral ajustado: no muy estricto pero tampoco muy permisivo
        FRONTAL_THRESHOLD = 0.12  # Aumentado de 0.08 - menos permisivo
        
        # Para frontal: O hombros O caderas bien separados (no ambos obligatorio)
        is_frontal = shoulder_x_diff > FRONTAL_THRESHOLD or hip_x_diff > FRONTAL_THRESHOLD
        
        # Bonus si ambos están bien visibles
        visibility_bonus = 1.0 if avg_visibility > 0.6 else avg_visibility / 0.6
        
        # Calcular calidad de la posicion frontal
        quality = min(1.0, (shoulder_x_diff + hip_x_diff) / 0.4) * visibility_bonus
        
        # DEBUG: Log cada ~30 frames para ver valores reales
        if self.frame_count % 30 == 0:
            logger.info(f"[HIP_FRONTAL_CHECK] shoulder_x={shoulder_x_diff:.3f}, hip_x={hip_x_diff:.3f} "
                       f"(th={FRONTAL_THRESHOLD}), is_frontal={is_frontal}, quality={quality:.2f}")
        
        return is_frontal, float(quality)
    
    def get_landmarks_2d(
        self, 
        landmark, 
        frame_width: int, 
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Convierte landmarks normalizados a coordenadas de pixeles
        """
        return (
            int(landmark.x * frame_width), 
            int(landmark.y * frame_height)
        )
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un frame y retorna el frame anotado
        
        METODO PRINCIPAL - Llamar en cada frame del video stream
        """
        start_time = time.time()
        self.frame_count += 1
        
        # Guardar dimensiones originales
        original_h, original_w = frame.shape[:2]
        
        # Reducir resolucion para procesamiento
        small_frame = cv2.resize(
            frame, 
            (self.processing_width, self.processing_height), 
            interpolation=cv2.INTER_LINEAR
        )
        
        # Convertir a RGB
        image_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        
        # Procesar con MediaPipe
        results = self.pose.process(image_rgb)
        
        # Trabajar con resolucion original para visualizacion
        image_rgb.flags.writeable = True
        image = frame.copy()
        
        if results.pose_landmarks:
            self.landmarks_detected = True
            h, w = image.shape[:2]
            landmarks = results.pose_landmarks.landmark
            
            # Verificar orientacion frontal
            is_frontal, frontal_quality = self.detect_frontal_orientation(landmarks)
            
            self.is_frontal_position = is_frontal
            self.orientation_quality = frontal_quality
            
            if is_frontal:
                self.orientation = "frontal"
                self.posture_valid = True
            else:
                self.orientation = "profile"
                self.posture_valid = False
            
            # Confianza de deteccion
            avg_vis = sum(l.visibility for l in landmarks) / len(landmarks)
            self.confidence = min(avg_vis * 1.2, 1.0)
            
            # Dibujar skeleton si esta habilitado
            if self.show_skeleton:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            # Procesar vista frontal
            self._process_frontal_view(image, landmarks, w, h)
            
            # Mostrar indicador de pierna seleccionada (si no es 'both')
            if self.selected_leg != 'both':
                leg_labels = {'left': 'PIERNA IZQUIERDA', 'right': 'PIERNA DERECHA'}
                leg_text = f"Analizando: {leg_labels.get(self.selected_leg, self.selected_leg)}"
                
                # Fondo para el texto
                (text_w, text_h), _ = cv2.getTextSize(leg_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(image, (w//2 - text_w//2 - 10, 10), 
                             (w//2 + text_w//2 + 10, 40), (0, 0, 0), -1)
                
                # Texto con color según pierna
                text_color = self.color_cache['cyan'] if self.selected_leg == 'left' else self.color_cache['magenta']
                cv2.putText(image, leg_text, (w//2 - text_w//2, 32),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2, cv2.LINE_4)
            
        else:
            self.landmarks_detected = False
            self.posture_valid = False
            cv2.putText(
                image, 
                "No se detecta persona", 
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                self.color_cache['red'], 
                2, 
                cv2.LINE_4
            )
        
        # Calcular metricas de rendimiento
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_time) if (current_time - self.last_time) > 0 else 0
        self.fps_history.append(fps)
        self.last_time = current_time
        
        return image
    
    def _process_frontal_view(
        self, 
        image: np.ndarray, 
        landmarks, 
        w: int, 
        h: int
    ):
        """
        Procesa vista frontal - Analisis de abduccion de cadera
        """
        # Obtener landmarks de ambos lados
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        
        # Convertir a coordenadas 2D
        left_hip_2d = self.get_landmarks_2d(left_hip, w, h)
        right_hip_2d = self.get_landmarks_2d(right_hip, w, h)
        left_knee_2d = self.get_landmarks_2d(left_knee, w, h)
        right_knee_2d = self.get_landmarks_2d(right_knee, w, h)
        left_ankle_2d = self.get_landmarks_2d(left_ankle, w, h)
        right_ankle_2d = self.get_landmarks_2d(right_ankle, w, h)
        
        # Calcular angulos de abduccion para ambas piernas
        self.left_angle = self.calculate_abduction_angle(left_hip_2d, left_knee_2d, True)
        self.right_angle = self.calculate_abduction_angle(right_hip_2d, right_knee_2d, False)
        
        # Actualizar maximos
        if self.left_angle > self.max_left_angle:
            self.max_left_angle = self.left_angle
        if self.right_angle > self.max_right_angle:
            self.max_right_angle = self.right_angle
        
        # Determinar angulo principal segun pierna seleccionada
        if self.selected_leg == 'left':
            self.current_angle = self.left_angle
            self.max_angle = self.max_left_angle
            self.side = 'left'
        elif self.selected_leg == 'right':
            self.current_angle = self.right_angle
            self.max_angle = self.max_right_angle
            self.side = 'right'
        else:
            # Bilateral: usar el mayor
            if self.left_angle > self.right_angle:
                self.current_angle = self.left_angle
                self.side = 'left'
            else:
                self.current_angle = self.right_angle
                self.side = 'right'
            self.max_angle = max(self.max_left_angle, self.max_right_angle)
        
        # ===== VISUALIZACION =====
        
        # Linea horizontal de referencia (pasa por ambas caderas)
        hip_center_y = (left_hip_2d[1] + right_hip_2d[1]) // 2
        cv2.line(image, (0, hip_center_y), (w, hip_center_y), 
                self.color_cache['green'], 2, cv2.LINE_4)
        
        # Dibujar pierna izquierda si es relevante
        if self.selected_leg in ['left', 'both']:
            self._draw_leg(image, left_hip_2d, left_knee_2d, left_ankle_2d, 
                          self.left_angle, "IZQ", True)
        
        # Dibujar pierna derecha si es relevante
        if self.selected_leg in ['right', 'both']:
            self._draw_leg(image, right_hip_2d, right_knee_2d, right_ankle_2d, 
                          self.right_angle, "DER", False)
        
        # Linea de referencia vertical (desde cada cadera)
        vertical_length = 150
        if self.selected_leg in ['left', 'both']:
            cv2.line(image, left_hip_2d, 
                    (left_hip_2d[0], left_hip_2d[1] + vertical_length),
                    self.color_cache['green'], 2, cv2.LINE_4)
        if self.selected_leg in ['right', 'both']:
            cv2.line(image, right_hip_2d, 
                    (right_hip_2d[0], right_hip_2d[1] + vertical_length),
                    self.color_cache['green'], 2, cv2.LINE_4)
    
    def _draw_leg(
        self, 
        image: np.ndarray, 
        hip: Tuple[int, int], 
        knee: Tuple[int, int], 
        ankle: Tuple[int, int],
        angle: float,
        label: str,
        is_left: bool
    ):
        """
        Dibuja una pierna con su angulo
        """
        # Color segun angulo
        leg_color = self._get_angle_color(angle)
        
        # Puntos
        cv2.circle(image, hip, 10, self.color_cache['yellow'], -1, cv2.LINE_4)
        cv2.circle(image, knee, 8, self.color_cache['cyan'], -1, cv2.LINE_4)
        cv2.circle(image, ankle, 6, self.color_cache['white'], -1, cv2.LINE_4)
        
        # Lineas
        cv2.line(image, hip, knee, leg_color, 3, cv2.LINE_4)
        cv2.line(image, knee, ankle, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Mostrar angulo
        angle_text = f"{angle:.1f}"
        text_offset = -70 if is_left else 30
        text_pos = (hip[0] + text_offset, hip[1] - 20)
        
        # Fondo
        (text_w, text_h), _ = cv2.getTextSize(angle_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(image, 
                     (text_pos[0] - 3, text_pos[1] - text_h - 3),
                     (text_pos[0] + text_w + 15, text_pos[1] + 3),
                     (0, 0, 0), -1)
        
        # Texto
        cv2.putText(image, angle_text, text_pos,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, leg_color, 2, cv2.LINE_4)
        cv2.putText(image, "o", (text_pos[0] + text_w + 2, text_pos[1] - 12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, leg_color, 1, cv2.LINE_4)
    
    def _get_angle_color(self, angle: float) -> Tuple[int, int, int]:
        """
        Retorna color segun el angulo de abduccion
        """
        if angle < 10:
            return self.color_cache['white']
        elif angle < 25:
            return self.color_cache['yellow']
        elif angle < 35:
            return self.color_cache['orange']
        elif angle < 45:
            return self.color_cache['magenta']
        else:
            return self.color_cache['green']
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos actuales del analisis
        
        API PUBLICA - Usar para obtener datos en tiempo real
        """
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        return {
            'segment': 'hip',
            'joint_type': 'hip_frontal',
            'angle': round(self.current_angle, 1),
            'max_rom': round(self.max_angle, 1),
            'side': self.side,
            'orientation': self.orientation,
            'confidence': round(self.confidence, 2),
            'posture_valid': self.posture_valid,
            'landmarks_detected': self.landmarks_detected,
            # Compatibilidad con analysis_session (igual que shoulder_frontal)
            'is_profile_position': False,  # Siempre False para frontal
            'is_frontal_position': self.is_frontal_position,
            'orientation_quality': round(self.orientation_quality, 2),
            'fps': round(avg_fps, 1),
            'frame_count': self.frame_count,
            'posture_correct': self.posture_valid and self.is_frontal_position,
            'current_angle': round(self.current_angle, 1),
            'max_angle': round(self.max_angle, 1),
            'processing_time_ms': round(avg_processing, 1),
            'rom_max': round(self.max_angle, 1),
            'rom_min': 0.0,
            'analysis_type': 'hip_frontal',
            'movement_type': 'abduction',
            'posture_feedback': 'Posicion correcta' if self.posture_valid else 'Pongase de frente a la camara',
            # Datos bilaterales
            'left_angle': round(self.left_angle, 1),
            'right_angle': round(self.right_angle, 1),
            'max_left_angle': round(self.max_left_angle, 1),
            'max_right_angle': round(self.max_right_angle, 1),
            'symmetry_diff': round(abs(self.left_angle - self.right_angle), 1)
        }
    
    def reset(self):
        """
        Reinicia todas las estadisticas
        
        API PUBLICA - Usar para comenzar nueva medicion
        NOTA: NO resetea selected_leg para mantener el indicador visual.
              selected_leg se controla desde el frontend vía /api/session/set_leg
        """
        self.max_angle = 0.0
        self.current_angle = 0.0
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.max_left_angle = 0.0
        self.max_right_angle = 0.0
        self.fps_history.clear()
        self.processing_times.clear()
        self.frame_count = 0
        self.posture_valid = False
        self.landmarks_detected = False
        self.is_frontal_position = False
        self.orientation_quality = 0.0
        logger.info("[HipFrontalAnalyzer] Estadisticas reiniciadas")
    
    def cleanup(self):
        """
        Limpia recursos del analyzer
        
        NOTA: NO cerrar el pose porque es compartido (singleton)
        """
        self.pose = None
        self.fps_history.clear()
        self.processing_times.clear()
        logger.info("[HipFrontalAnalyzer] Recursos liberados")
