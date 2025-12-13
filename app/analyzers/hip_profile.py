"""
🦵 HIP PROFILE ANALYZER - Análisis de Flexión/Extensión de Cadera
===================================================================
Analizador para vista de PERFIL (medición de flexión/extensión de cadera)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestión de estado interno (ángulos, ROM máximo)
- API pública para obtener datos actuales

SISTEMA DE MEDICIÓN:
- Eje FIJO: Vertical absoluto (0, 1) que pasa por la CADERA
- Brazo MÓVIL: Línea del muslo (CADERA → RODILLA)
- 0° = Pierna vertical hacia abajo (posición neutra de pie)
- +135° = Flexión máxima (rodilla hacia pecho)
- -30° = Extensión máxima (pierna hacia atrás)

Referencias:
- AAOS: Flexión 0-135°, Extensión 0-30°
- Nordin & Frankel (2022)
- Kapandji (6ta ed.)

Autor: BIOTRACK Team
Fecha: 2025-12-06
Basado en: tests/test_hip_profile.py, shoulder_profile.py
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


class HipProfileAnalyzer:
    """
    Analizador de cadera en vista de PERFIL
    
    Mide:
    - Flexión (pierna hacia adelante/arriba)
    - Extensión (pierna hacia atrás)
    - ROM máximo alcanzado
    
    Uso en Flask:
        analyzer = HipProfileAnalyzer()
        
        # En loop de video stream:
        processed_frame = analyzer.process_frame(frame)
        current_data = analyzer.get_current_data()
    """
    
    def __init__(
        self, 
        processing_width: int = 640, 
        processing_height: int = 480,
        show_skeleton: bool = False
    ):
        """
        Inicializa el analizador para vista de PERFIL
        
        Args:
            processing_width: Ancho para procesamiento de MediaPipe
            processing_height: Alto para procesamiento de MediaPipe
            show_skeleton: Si mostrar el skeleton completo de MediaPipe
        """
        # ⚡ OPTIMIZACIÓN: Usar instancia COMPARTIDA de MediaPipe Pose
        self.pose = get_shared_pose()
        
        # Resolución de procesamiento
        self.processing_width = processing_width
        self.processing_height = processing_height
        
        # Variables para tracking de ángulos
        self.current_angle = 0.0
        self.max_angle = 0.0
        self.side = "Detectando..."
        self.orientation = "Detectando..."
        self.confidence = 0.0
        self.frame_count = 0
        
        # Configuración de visualización
        self.show_skeleton = show_skeleton
        
        # Métricas de rendimiento
        self.fps_history = deque(maxlen=30)
        self.processing_times = deque(maxlen=30)
        self.last_time = time.time()
        
        # Caché de colores
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
        
        # Orientación real verificada
        self.is_profile_position = False
        self.orientation_quality = 0.0
        
        logger.info("[HipProfileAnalyzer] Inicializado con pose singleton compartido")
    
    def calculate_hip_angle(
        self, 
        shoulder: Tuple[int, int],
        hip: Tuple[int, int], 
        knee: Tuple[int, int],
        orientation: str = ""
    ) -> float:
        """
        Calcula el ángulo de flexión/extensión de cadera con eje vertical fijo
        
        Sistema goniómetro estándar (según AAOS):
        - Brazo FIJO: Eje vertical absoluto (0, 1) que pasa por la CADERA
        - Brazo MÓVIL: Línea del muslo (CADERA → RODILLA)
        - 0° = Pierna vertical hacia abajo (posición neutra de pie)
        - +ángulo = Flexión (pierna hacia adelante/arriba)
        - -ángulo = Extensión (pierna hacia atrás)
        
        Args:
            shoulder: Coordenadas (x, y) del hombro (referencia visual)
            hip: Coordenadas (x, y) de la cadera (VÉRTICE del ángulo)
            knee: Coordenadas (x, y) de la rodilla
            orientation: Orientación de la persona ('mirando izquierda' o 'mirando derecha')
        
        Returns:
            float: Ángulo en grados
                   - Positivo (0° a 135°): Flexión
                   - Negativo (-1° a -30°): Extensión
        """
        # Vector vertical fijo (referencia 0° - apunta hacia abajo)
        vertical_down_vector = np.array([0, 1])
        
        # Vector del muslo (CADERA → RODILLA) - brazo móvil del goniómetro
        thigh_vector = np.array([knee[0] - hip[0], knee[1] - hip[1]])
        
        # Normalizar vector del muslo
        thigh_norm = np.linalg.norm(thigh_vector)
        
        if thigh_norm == 0:
            return 0.0
        
        thigh_vector_normalized = thigh_vector / thigh_norm
        
        # Calcular ángulo entre eje vertical y muslo (magnitud)
        dot_product = np.dot(vertical_down_vector, thigh_vector_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle_magnitude = np.degrees(np.arccos(dot_product))
        
        # Determinar dirección (flexión vs extensión) según orientación
        # Producto cruz 2D para saber si rodilla está adelante o atrás de la cadera
        knee_relative_x = knee[0] - hip[0]
        
        if "derecha" in orientation.lower():
            # Persona mirando derecha → Adelante es derecha (+x)
            # FLEXIÓN: rodilla hacia la derecha (+x) → ángulo positivo
            # EXTENSIÓN: rodilla hacia la izquierda (-x) → ángulo negativo
            angle = angle_magnitude if knee_relative_x > 0 else -angle_magnitude
        else:
            # Persona mirando izquierda → Adelante es izquierda (-x)
            # FLEXIÓN: rodilla hacia la izquierda (-x) → ángulo positivo
            # EXTENSIÓN: rodilla hacia la derecha (+x) → ángulo negativo
            angle = angle_magnitude if knee_relative_x < 0 else -angle_magnitude
        
        return float(angle)
    
    def detect_side(self, landmarks) -> Tuple[str, float, str]:
        """
        Detecta qué lado del cuerpo se está ANALIZANDO (vista de perfil)
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (lado, confianza, orientación)
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        
        # Visibilidad promedio de cada lado
        left_visibility = (left_shoulder.visibility + left_hip.visibility) / 2
        right_visibility = (right_shoulder.visibility + right_hip.visibility) / 2
        
        # Confianza de detección de persona
        avg_visibility = (left_shoulder.visibility + right_shoulder.visibility + 
                         left_hip.visibility + right_hip.visibility + 
                         nose.visibility) / 5
        detection_confidence = min(avg_visibility * 1.2, 1.0)
        
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        
        if nose.x > shoulder_center_x:
            # Nariz a la derecha del centro → mira a su izquierda → lado derecho visible
            side = 'right'
            orientation = "mirando izquierda"
        else:
            # Nariz a la izquierda del centro → mira a su derecha → lado izquierdo visible
            side = 'left'
            orientation = "mirando derecha"
        
        return side, float(detection_confidence), orientation
    
    def verify_profile_position(self, landmarks) -> Tuple[bool, float, str]:
        """
        Verifica si la persona está REALMENTE en posición de perfil.
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (is_profile, quality, message)
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Diferencia de visibilidad entre hombros
        visibility_diff = abs(left_shoulder.visibility - right_shoulder.visibility)
        
        # Alineación de hombros (en perfil, están casi en la misma X)
        shoulder_x_diff = abs(left_shoulder.x - right_shoulder.x)
        
        # Alineación de caderas
        hip_x_diff = abs(left_hip.x - right_hip.x)
        
        # Umbrales MÁS ESTRICTOS para perfil
        # En perfil REAL: hombros casi alineados verticalmente (diff X muy pequeña)
        SHOULDER_ALIGNMENT_THRESHOLD = 0.12  # Reducido de 0.25 - más estricto
        VISIBILITY_DIFF_THRESHOLD = 0.20     # Un hombro debe ser más visible que otro
        HIP_ALIGNMENT_THRESHOLD = 0.12       # Reducido de 0.25 - caderas también alineadas
        
        # Calcular scores
        alignment_score = max(0, 1 - (shoulder_x_diff / SHOULDER_ALIGNMENT_THRESHOLD))
        visibility_score = min(1, visibility_diff / VISIBILITY_DIFF_THRESHOLD)
        hip_score = max(0, 1 - (hip_x_diff / HIP_ALIGNMENT_THRESHOLD))
        
        quality = (alignment_score * 0.4 + visibility_score * 0.3 + hip_score * 0.3)
        
        # Para ser perfil: hombros Y caderas deben estar alineados
        is_profile = shoulder_x_diff < SHOULDER_ALIGNMENT_THRESHOLD and hip_x_diff < HIP_ALIGNMENT_THRESHOLD
        
        # DEBUG: Log cada ~30 frames para ver valores reales
        if self.frame_count % 30 == 0:
            logger.info(f"[HIP_PROFILE_CHECK] shoulder_x={shoulder_x_diff:.3f} (th={SHOULDER_ALIGNMENT_THRESHOLD}), "
                       f"hip_x={hip_x_diff:.3f} (th={HIP_ALIGNMENT_THRESHOLD}), "
                       f"is_profile={is_profile}, quality={quality:.2f}")
        
        if is_profile:
            if quality > 0.8:
                message = "Perfil excelente"
            elif quality > 0.6:
                message = "Perfil correcto"
            else:
                message = "Perfil aceptable"
        else:
            message = "Gire más hacia un lado"
        
        self.is_profile_position = is_profile
        self.orientation_quality = quality
        
        return is_profile, quality, message
    
    def get_landmarks_2d(
        self, 
        landmark, 
        frame_width: int, 
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Convierte landmarks normalizados a coordenadas de píxeles
        """
        return (
            int(landmark.x * frame_width), 
            int(landmark.y * frame_height)
        )
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un frame y retorna el frame anotado
        
        MÉTODO PRINCIPAL - Llamar en cada frame del video stream
        """
        start_time = time.time()
        self.frame_count += 1
        
        # Guardar dimensiones originales
        original_h, original_w = frame.shape[:2]
        
        # Reducir resolución para procesamiento
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
        
        # Trabajar con resolución original para visualización
        image_rgb.flags.writeable = True
        image = frame.copy()
        
        if results.pose_landmarks:
            self.landmarks_detected = True
            h, w = image.shape[:2]
            landmarks = results.pose_landmarks.landmark
            
            # Detectar lado visible
            side, detection_confidence, orientation = self.detect_side(landmarks)
            self.side = side
            
            # Verificar si está en posición de perfil
            is_profile, profile_quality, profile_message = self.verify_profile_position(landmarks)
            
            # ⚡ CRÍTICO: Actualizar is_profile_position para que analysis_session funcione
            self.is_profile_position = is_profile
            
            if is_profile:
                self.orientation = "profile"
                self.posture_valid = True
            else:
                self.orientation = "frontal"
                self.posture_valid = False
            
            self.confidence = detection_confidence
            self.orientation_quality = profile_quality
            
            # Dibujar skeleton si está habilitado
            if self.show_skeleton:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            # Procesar vista de perfil
            self._process_profile_view(image, landmarks, w, h, side, self.orientation, detection_confidence)
            
            # Panel de información (COMENTADO - info ya visible en panel web)
            # self._draw_info_panel(image, self.orientation, detection_confidence, w, h)
            
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
        
        # Calcular métricas de rendimiento
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_time) if (current_time - self.last_time) > 0 else 0
        self.fps_history.append(fps)
        self.last_time = current_time
        
        # Métricas de rendimiento (COMENTADO - info ya visible en panel web)
        # self._draw_performance_metrics(image, fps, processing_time)
        
        return image
    
    def _process_profile_view(
        self, 
        image: np.ndarray, 
        landmarks, 
        w: int, 
        h: int, 
        side: str, 
        orientation: str, 
        confidence: float
    ):
        """
        Procesa vista de perfil - Análisis de flexión/extensión de cadera
        """
        # Seleccionar landmarks según el lado detectado
        if side == 'left':
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        else:
            shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        
        self.side = side  # Mantener 'left'/'right' para DB
        
        # Obtener coordenadas 2D
        shoulder_2d = self.get_landmarks_2d(shoulder, w, h)
        hip_2d = self.get_landmarks_2d(hip, w, h)
        knee_2d = self.get_landmarks_2d(knee, w, h)
        ankle_2d = self.get_landmarks_2d(ankle, w, h)
        
        # Calcular ángulo de flexión/extensión de cadera
        angle = self.calculate_hip_angle(shoulder_2d, hip_2d, knee_2d, orientation)
        
        # Actualizar estadísticas
        self.current_angle = angle
        
        # ROM máximo (valor absoluto para incluir extensión)
        if abs(angle) > abs(self.max_angle):
            self.max_angle = angle
        
        # ===== VISUALIZACIÓN =====
        
        # Puntos clave
        cv2.circle(image, hip_2d, 12, self.color_cache['yellow'], -1, cv2.LINE_4)      # CADERA (vértice)
        cv2.circle(image, shoulder_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4) # HOMBRO
        cv2.circle(image, knee_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4)        # RODILLA
        cv2.circle(image, ankle_2d, 6, self.color_cache['white'], -1, cv2.LINE_4)      # TOBILLO
        
        # Borde negro para mayor visibilidad en cadera
        cv2.circle(image, hip_2d, 14, (0, 0, 0), 2, cv2.LINE_4)
        
        # Línea de referencia vertical fija (pasa por la CADERA)
        vertical_length = 180
        vertical_start = (hip_2d[0], hip_2d[1] - vertical_length)
        vertical_end = (hip_2d[0], hip_2d[1] + vertical_length)
        cv2.line(image, vertical_start, vertical_end, self.color_cache['green'], 3, cv2.LINE_4)
        
        # Etiqueta del eje vertical
        cv2.putText(
            image, "0", 
            (hip_2d[0] + 10, hip_2d[1] + vertical_length - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color_cache['green'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "o", 
            (hip_2d[0] + 22, hip_2d[1] + vertical_length - 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, self.color_cache['green'], 1, cv2.LINE_4
        )
        
        # Línea del muslo (CADERA → RODILLA) - brazo móvil
        thigh_color = self._get_angle_color(angle)
        cv2.line(image, hip_2d, knee_2d, thigh_color, 4, cv2.LINE_4)
        
        # Pierna inferior (RODILLA → TOBILLO) - referencia visual
        cv2.line(image, knee_2d, ankle_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Línea del torso (HOMBRO → CADERA) - referencia visual
        cv2.line(image, shoulder_2d, hip_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Dibujar arco del ángulo
        self._draw_angle_arc(image, hip_2d, angle)
        
        # Mostrar ángulo junto a la cadera
        angle_num = f"{abs(angle):.1f}"
        text_pos = (hip_2d[0] + 25, hip_2d[1] - 35)
        
        # Fondo para el texto
        (text_w, text_h), _ = cv2.getTextSize(angle_num, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        cv2.rectangle(
            image, 
            (text_pos[0] - 5, text_pos[1] - text_h - 5),
            (text_pos[0] + text_w + 15, text_pos[1] + 5),
            (0, 0, 0), -1
        )
        # Número del ángulo
        cv2.putText(
            image, angle_num, text_pos,
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, thigh_color, 2, cv2.LINE_4
        )
        # Símbolo de grados
        cv2.putText(
            image, "o", (text_pos[0] + text_w + 2, text_pos[1] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, thigh_color, 1, cv2.LINE_4
        )
        
        # Indicador de estado de flexión/extensión (COMENTADO - info en panel web)
        # if angle < 0:
        #     status = "EXTENSION"
        #     status_color = self.color_cache['orange']
        # elif angle < 30:
        #     status = "NEUTRO"
        #     status_color = self.color_cache['white']
        # elif angle < 90:
        #     status = "FLEXION PARCIAL"
        #     status_color = self.color_cache['yellow']
        # else:
        #     status = "FLEXION"
        #     status_color = self.color_cache['green']
        # 
        # cv2.putText(
        #     image, status, 
        #     (hip_2d[0] - 60, hip_2d[1] + 50),
        #     cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2, cv2.LINE_4
        # )
    
    def _draw_angle_arc(
        self, 
        image: np.ndarray, 
        center: Tuple[int, int], 
        angle: float, 
        radius: int = 50
    ):
        """
        Dibuja un arco visual que representa el ángulo medido
        """
        # El arco va desde la vertical (90° en coordenadas OpenCV) hacia el muslo
        start_angle = 90  # Vertical hacia abajo
        
        if angle < 0:
            # Extensión: arco hacia atrás
            end_angle = 90 - abs(angle)
            arc_color = self.color_cache['orange']
        else:
            # Flexión: arco hacia adelante
            end_angle = 90 + angle
            arc_color = self._get_angle_color(angle)
        
        if angle != 0:
            cv2.ellipse(
                image, center, (radius, radius),
                0, min(start_angle, end_angle), max(start_angle, end_angle),
                arc_color, 2, cv2.LINE_4
            )
    
    def _draw_info_panel(
        self, 
        image: np.ndarray, 
        orientation: str, 
        confidence: float, 
        w: int, 
        h: int
    ):
        """
        Dibuja panel de información en la imagen (método mantenido para compatibilidad)
        """
        panel_height = 160
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        
        cv2.putText(
            image, "ANÁLISIS DE CADERA (PERFIL)", (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, self.color_cache['cyan'], 2, cv2.LINE_4
        )
        
        color_side = self.color_cache['green'] if confidence > 0.5 else self.color_cache['orange']
        cv2.putText(
            image, f"Lado: {self.side}", (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_side, 2, cv2.LINE_4
        )
        
        angle_color = self._get_angle_color(self.current_angle)
        direction_text = "FLEX" if self.current_angle > 0 else "EXT" if self.current_angle < 0 else ""
        cv2.putText(
            image, f"Angulo: {abs(self.current_angle):.1f}deg {direction_text}", (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, angle_color, 2, cv2.LINE_4
        )
        
        cv2.putText(
            image, f"ROM Max: {abs(self.max_angle):.1f}deg", (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.color_cache['green'], 2, cv2.LINE_4
        )
    
    def _draw_performance_metrics(
        self, 
        image: np.ndarray, 
        current_fps: float, 
        current_processing_time: float
    ):
        """
        Dibuja métricas de rendimiento (método mantenido para compatibilidad)
        """
        h, w = image.shape[:2]
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        panel_x = w - 180
        panel_y = 100
        
        overlay = image.copy()
        cv2.rectangle(overlay, (panel_x - 10, panel_y), (w - 10, panel_y + 60), 
                     self.color_cache['gray'], -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        cv2.putText(
            image, f"FPS: {current_fps:.1f}", 
            (panel_x, panel_y + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_cache['green'], 1, cv2.LINE_4
        )
        
        cv2.putText(
            image, f"Latencia: {current_processing_time:.1f}ms", 
            (panel_x, panel_y + 45),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_cache['yellow'], 1, cv2.LINE_4
        )
    
    def _get_angle_color(self, angle: float) -> Tuple[int, int, int]:
        """
        Retorna color según el ángulo de flexión/extensión de cadera
        """
        abs_angle = abs(angle)
        
        if angle < 0:
            return self.color_cache['orange']  # Extensión
        elif abs_angle < 30:
            return self.color_cache['white']
        elif abs_angle < 60:
            return self.color_cache['yellow']
        elif abs_angle < 90:
            return self.color_cache['orange']
        elif abs_angle < 120:
            return self.color_cache['magenta']
        else:
            return self.color_cache['green']
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos actuales del análisis
        
        API PÚBLICA - Usar para obtener datos en tiempo real
        """
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        # Determinar tipo de movimiento basado en el ángulo
        if self.current_angle < 0:
            movement = "extension"
        else:
            movement = "flexion"
        
        return {
            'segment': 'hip',
            'joint_type': 'hip_profile',
            'angle': round(self.current_angle, 1),
            'max_rom': round(abs(self.max_angle), 1),
            'side': self.side,
            'orientation': self.orientation,
            'confidence': round(self.confidence, 2),
            'posture_valid': self.posture_valid,
            'landmarks_detected': self.landmarks_detected,
            'is_profile_position': self.is_profile_position,
            'orientation_quality': round(self.orientation_quality, 2),
            'fps': round(avg_fps, 1),
            'frame_count': self.frame_count,
            'posture_correct': self.posture_valid and self.is_profile_position,
            'current_angle': round(self.current_angle, 1),
            'max_angle': round(self.max_angle, 1),
            'processing_time_ms': round(avg_processing, 1),
            'rom_max': round(abs(self.max_angle), 1),
            'rom_min': 0.0,
            'analysis_type': 'hip_profile',
            'movement_type': movement,
            'posture_feedback': 'Posición correcta' if self.posture_valid else 'Ajuste su posición'
        }
    
    def reset(self):
        """
        Reinicia todas las estadísticas
        
        API PÚBLICA - Usar para comenzar nueva medición
        """
        self.max_angle = 0.0
        self.current_angle = 0.0
        self.fps_history.clear()
        self.processing_times.clear()
        self.frame_count = 0
        self.posture_valid = False
        self.landmarks_detected = False
        self.is_profile_position = False
        self.orientation_quality = 0.0
        logger.info("[HipProfileAnalyzer] Estadísticas reiniciadas")
    
    def cleanup(self):
        """
        Limpia recursos del analyzer
        
        NOTA: NO cerrar el pose porque es compartido (singleton)
        """
        self.pose = None
        self.fps_history.clear()
        self.processing_times.clear()
        logger.info("[HipProfileAnalyzer] Recursos liberados")
