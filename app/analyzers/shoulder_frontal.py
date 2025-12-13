"""
💪 SHOULDER FRONTAL ANALYZER - Análisis de Abducción Bilateral de Hombros
===========================================================================
Analizador para vista FRONTAL (medición de abducción simultánea de ambos hombros)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestión de estado interno (ángulos bilaterales, ROM máximo)
- API pública para obtener datos actuales

Autor: BIOTRACK Team
Fecha: 2025-11-14
Basado en: tests/test_shoulder_frontal.py
"""

import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque
from typing import Dict, Any, Tuple, Optional

# Importar instancia compartida de MediaPipe Pose (singleton)
from app.core.pose_singleton import get_shared_pose

# Inicializar MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


class ShoulderFrontalAnalyzer:
    """
    Analizador de hombros en vista FRONTAL
    
    Mide:
    - Abducción bilateral (ambos brazos simultáneamente)
    - Simetría entre ambos lados
    - ROM máximo alcanzado para cada lado
    
    Uso en Flask:
        analyzer = ShoulderFrontalAnalyzer()
        
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
        Inicializa el analizador para vista FRONTAL
        
        Args:
            processing_width: Ancho para procesamiento de MediaPipe
            processing_height: Alto para procesamiento de MediaPipe
            show_skeleton: Si mostrar el skeleton completo de MediaPipe
        """
        # ⚡ OPTIMIZACIÓN: Usar instancia COMPARTIDA de MediaPipe Pose
        # Antes: Cada analyzer creaba su Pose() → 22s por analyzer
        # Ahora: TODOS comparten UNA instancia → 12s total, reutilización instantánea
        self.pose = get_shared_pose()
        
        # Resolución de procesamiento
        self.processing_width = processing_width
        self.processing_height = processing_height
        
        # Variables para tracking de ángulos (bilateral)
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_max_rom = 0.0
        self.right_max_rom = 0.0
        self.asymmetry = 0.0  # Diferencia entre ambos lados
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
            'light_gray': (200, 200, 200),
            'purple': (255, 0, 127)
        }
        
        # Estado de postura
        self.posture_valid = False
        self.landmarks_detected = False
        self.orientation_frontal = False
        
        # Histéresis para detección frontal (evita parpadeo durante movimiento)
        self._was_frontal = False
        
        # Atributos para compatibilidad con analysis_session
        self.confidence = 0.0              # Confianza de detección de persona
        self.orientation = "frontal"       # Tipo de orientación esperada
        self.is_frontal_position = False   # True si está realmente de frente
        self.orientation_quality = 0.0     # Calidad de la orientación 0-1
    
    def calculate_abduction_angle(
        self, 
        shoulder: Tuple[int, int], 
        hip: Tuple[int, int],
        elbow: Tuple[int, int]
    ) -> float:
        """
        Calcula el ángulo de abducción con eje vertical fijo
        
        Sistema goniómetro estándar:
        - Brazo FIJO: Línea vertical (hombro → cadera)
        - Brazo MÓVIL: Línea del brazo (hombro → codo)
        - 0° = Brazo pegado al cuerpo
        - 90° = Brazo horizontal
        - 180° = Brazo arriba (sobre la cabeza)
        
        Args:
            shoulder: Coordenadas (x, y) del hombro
            hip: Coordenadas (x, y) de la cadera
            elbow: Coordenadas (x, y) del codo
        
        Returns:
            float: Ángulo de abducción en grados (0-180)
        """
        # Vector vertical de referencia (hombro → cadera)
        vertical_vector = np.array([hip[0] - shoulder[0], hip[1] - shoulder[1]])
        
        # Vector del brazo (hombro → codo)
        arm_vector = np.array([elbow[0] - shoulder[0], elbow[1] - shoulder[1]])
        
        # Normalizar vectores
        vertical_norm = np.linalg.norm(vertical_vector)
        arm_norm = np.linalg.norm(arm_vector)
        
        if vertical_norm == 0 or arm_norm == 0:
            return 0.0
        
        vertical_normalized = vertical_vector / vertical_norm
        arm_normalized = arm_vector / arm_norm
        
        # Calcular ángulo usando producto punto
        dot_product = np.dot(vertical_normalized, arm_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle = np.degrees(np.arccos(dot_product))
        
        return float(angle)
    
    def detect_frontal_orientation(self, landmarks) -> Tuple[bool, float]:
        """
        Detecta si la persona está REALMENTE en vista frontal
        
        Criterios RELAJADOS para mantener detección durante movimiento:
        1. Ambos hombros visibles (>0.5, antes era >0.7)
        2. Visibilidad similar entre ambos (<0.25, antes era <0.15)
        3. Distancia horizontal entre hombros > distancia vertical
        4. Caderas opcionalmente visibles
        5. HISTÉRESIS: Si ya estaba en frontal, mantener con criterios más relajados
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (es_frontal: bool, confianza: float)
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Visibilidad de hombros
        left_vis = left_shoulder.visibility
        right_vis = right_shoulder.visibility
        avg_shoulder_vis = (left_vis + right_vis) / 2
        shoulder_vis_diff = abs(left_vis - right_vis)
        
        # Visibilidad de caderas (ahora opcional)
        left_hip_vis = left_hip.visibility
        right_hip_vis = right_hip.visibility
        avg_hip_vis = (left_hip_vis + right_hip_vis) / 2
        hip_vis_diff = abs(left_hip_vis - right_hip_vis)
        
        # Distancia HORIZONTAL entre hombros (normalizada)
        shoulder_horizontal_dist = abs(left_shoulder.x - right_shoulder.x)
        # Distancia VERTICAL entre hombros (debería ser muy pequeña si está de frente)
        shoulder_vertical_dist = abs(left_shoulder.y - right_shoulder.y)
        
        # Ratio: en vista frontal, horizontal >> vertical
        # En perfil, los hombros están casi en el mismo x, así que horizontal es pequeño
        if shoulder_horizontal_dist > 0.01:  # Evitar división por cero
            frontal_ratio = shoulder_horizontal_dist / max(shoulder_vertical_dist, 0.01)
        else:
            frontal_ratio = 0.0
        
        # Criterios RELAJADOS para vista frontal:
        # Los valores se ajustan según si ya estábamos en modo frontal (histéresis)
        # Esto evita que la detección parpadee durante el movimiento
        
        # Usar histéresis: si ya estaba en frontal, usar criterios más relajados
        if hasattr(self, '_was_frontal') and self._was_frontal:
            # Criterios de MANTENIMIENTO (más relajados)
            min_shoulder_vis = 0.4       # Antes: 0.7, ahora más tolerante
            max_vis_diff = 0.35          # Antes: 0.15, ahora más tolerante
            min_horizontal_dist = 0.08   # Antes: 0.15, ahora más tolerante
            min_frontal_ratio = 1.5      # Antes: 3.0, ahora más tolerante
            min_hip_vis = 0.3            # Antes: 0.5, ahora más tolerante
            max_hip_diff = 0.35          # Antes: 0.2, ahora más tolerante
        else:
            # Criterios de ENTRADA (moderados, no tan estrictos como antes)
            min_shoulder_vis = 0.5       # Antes: 0.7
            max_vis_diff = 0.25          # Antes: 0.15
            min_horizontal_dist = 0.10   # Antes: 0.15
            min_frontal_ratio = 2.0      # Antes: 3.0
            min_hip_vis = 0.4            # Antes: 0.5
            max_hip_diff = 0.3           # Antes: 0.2
        
        # Verificar criterios principales (hombros)
        shoulders_ok = (
            avg_shoulder_vis > min_shoulder_vis and
            shoulder_vis_diff < max_vis_diff and
            shoulder_horizontal_dist > min_horizontal_dist and
            frontal_ratio > min_frontal_ratio
        )
        
        # Verificar caderas (ahora es opcional - solo bonus para confianza)
        hips_ok = (
            avg_hip_vis > min_hip_vis and
            hip_vis_diff < max_hip_diff
        )
        
        # Es frontal si los hombros cumplen criterios
        # Las caderas ahora solo afectan la confianza, no bloquean
        is_frontal = shoulders_ok
        
        # Guardar estado para histéresis en próximo frame
        self._was_frontal = is_frontal
        
        # Calcular confianza
        if is_frontal:
            # Confianza basada en qué tan bien cumple los criterios
            vis_score = min(avg_shoulder_vis, 1.0)
            ratio_score = min(frontal_ratio / 5.0, 1.0)  # Normalizar ratio
            hip_bonus = 0.1 if hips_ok else 0.0  # Bonus si caderas OK
            confidence = (vis_score + ratio_score) / 2 + hip_bonus
            confidence = min(confidence, 1.0)  # Limitar a 1.0
        else:
            confidence = avg_shoulder_vis * 0.5  # Baja confianza si no es frontal
        
        return is_frontal, float(confidence)
    
    def get_landmarks_2d(
        self, 
        landmark, 
        frame_width: int, 
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Convierte landmarks normalizados a coordenadas de píxeles
        
        Args:
            landmark: Landmark de MediaPipe (normalizado 0-1)
            frame_width: Ancho del frame en píxeles
            frame_height: Alto del frame en píxeles
        
        Returns:
            tuple: (x, y) en coordenadas de píxeles
        """
        return (
            int(landmark.x * frame_width), 
            int(landmark.y * frame_height)
        )
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un frame y retorna el frame anotado
        
        MÉTODO PRINCIPAL - Llamar en cada frame del video stream
        
        Args:
            frame: Frame de OpenCV (BGR numpy array)
        
        Returns:
            np.ndarray: Frame procesado con anotaciones visuales
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
            
            # Detectar orientación frontal
            is_frontal, detection_confidence = self.detect_frontal_orientation(landmarks)
            self.orientation_frontal = is_frontal
            
            # Guardar atributos para compatibilidad con analysis_session
            self.confidence = detection_confidence  # Confianza de que hay persona
            self.is_frontal_position = is_frontal   # True si está de frente
            self.orientation_quality = detection_confidence if is_frontal else 0.3
            self.orientation = "frontal" if is_frontal else "profile"  # Invertido: reportar qué ES
            
            # Dibujar skeleton solo si está habilitado
            if self.show_skeleton:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            if is_frontal:
                # Procesar vista frontal (abducción bilateral)
                self._process_frontal_view(image, landmarks, w, h, detection_confidence)
            else:
                # No es vista frontal
                self.posture_valid = False
                cv2.putText(
                    image, 
                    "Colocate de FRENTE a la camara", 
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    self.color_cache['orange'], 
                    2, 
                    cv2.LINE_4
                )
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
        
        # Mostrar métricas en video (DESHABILITADO - info ya visible en panel web)
        # self._draw_performance_metrics(image, fps, processing_time)
        
        return image
    
    def _process_frontal_view(
        self, 
        image: np.ndarray, 
        landmarks, 
        w: int, 
        h: int, 
        confidence: float
    ):
        """Procesa vista frontal - Análisis de abducción bilateral"""
        # Obtener landmarks de ambos lados
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        
        # Convertir a coordenadas 2D
        left_shoulder_2d = self.get_landmarks_2d(left_shoulder, w, h)
        right_shoulder_2d = self.get_landmarks_2d(right_shoulder, w, h)
        left_hip_2d = self.get_landmarks_2d(left_hip, w, h)
        right_hip_2d = self.get_landmarks_2d(right_hip, w, h)
        left_elbow_2d = self.get_landmarks_2d(left_elbow, w, h)
        right_elbow_2d = self.get_landmarks_2d(right_elbow, w, h)
        left_wrist_2d = self.get_landmarks_2d(left_wrist, w, h)
        right_wrist_2d = self.get_landmarks_2d(right_wrist, w, h)
        
        # Calcular ángulos de abducción para ambos lados
        left_angle = self.calculate_abduction_angle(
            left_shoulder_2d, left_hip_2d, left_elbow_2d
        )
        right_angle = self.calculate_abduction_angle(
            right_shoulder_2d, right_hip_2d, right_elbow_2d
        )
        
        # Actualizar estadísticas
        self.left_angle = left_angle
        self.right_angle = right_angle
        
        if left_angle > self.left_max_rom:
            self.left_max_rom = left_angle
        if right_angle > self.right_max_rom:
            self.right_max_rom = right_angle
        
        # Calcular asimetría
        self.asymmetry = abs(left_angle - right_angle)
        
        # Validar postura
        self.posture_valid = (
            confidence > 0.6 and 
            left_angle < 200 and 
            right_angle < 200 and
            self.asymmetry < 40  # Diferencia razonable
        )
        
        # Dibujar puntos clave (LADO IZQUIERDO en perspectiva del usuario)
        cv2.circle(image, left_shoulder_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4)
        cv2.circle(image, left_hip_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4)
        cv2.circle(image, left_elbow_2d, 8, self.color_cache['yellow'], -1, cv2.LINE_4)
        
        # Dibujar puntos clave (LADO DERECHO en perspectiva del usuario)
        cv2.circle(image, right_shoulder_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4)
        cv2.circle(image, right_hip_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4)
        cv2.circle(image, right_elbow_2d, 8, self.color_cache['yellow'], -1, cv2.LINE_4)
        
        # Líneas de referencia vertical (IZQUIERDA)
        cv2.line(image, left_shoulder_2d, left_hip_2d, self.color_cache['green'], 2, cv2.LINE_4)
        
        # Líneas de referencia vertical (DERECHA)
        cv2.line(image, right_shoulder_2d, right_hip_2d, self.color_cache['green'], 2, cv2.LINE_4)
        
        # Líneas del brazo (IZQUIERDA)
        cv2.line(image, left_shoulder_2d, left_elbow_2d, self.color_cache['blue'], 3, cv2.LINE_4)
        cv2.line(image, left_elbow_2d, left_wrist_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Líneas del brazo (DERECHA)
        cv2.line(image, right_shoulder_2d, right_elbow_2d, self.color_cache['purple'], 3, cv2.LINE_4)
        cv2.line(image, right_elbow_2d, right_wrist_2d, self.color_cache['purple'], 2, cv2.LINE_4)
        
        # Mostrar ángulos en cada hombro (usamos 'o' en lugar de '°' porque OpenCV no renderiza bien el símbolo)
        left_angle_text = f"{left_angle:.1f}"
        cv2.putText(
            image, 
            left_angle_text, 
            (left_shoulder_2d[0] - 60, left_shoulder_2d[1] - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            self.color_cache['cyan'], 
            2, 
            cv2.LINE_4
        )
        # Dibujar 'o' pequeña como símbolo de grados (simulando superíndice)
        (text_width_l, _), _ = cv2.getTextSize(left_angle_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.putText(
            image,
            "o",
            (left_shoulder_2d[0] - 60 + text_width_l + 1, left_shoulder_2d[1] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            self.color_cache['cyan'],
            1,
            cv2.LINE_4
        )
        
        right_angle_text = f"{right_angle:.1f}"
        cv2.putText(
            image, 
            right_angle_text, 
            (right_shoulder_2d[0] + 20, right_shoulder_2d[1] - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            self.color_cache['purple'], 
            2, 
            cv2.LINE_4
        )
        # Dibujar 'o' pequeña como símbolo de grados (simulando superíndice)
        (text_width_r, _), _ = cv2.getTextSize(right_angle_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.putText(
            image,
            "o",
            (right_shoulder_2d[0] + 20 + text_width_r + 1, right_shoulder_2d[1] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            self.color_cache['purple'],
            1,
            cv2.LINE_4
        )
        
        # Panel de información en video (DESHABILITADO - info ya visible en panel web)
        # self._draw_info_panel(image, confidence, w, h)
        
        # Barras de progreso para cada lado (DESHABILITADO - info ya visible en panel web)
        # self._draw_rom_bars(image, w, h)
    
    def _draw_info_panel(
        self, 
        image: np.ndarray, 
        confidence: float, 
        w: int, 
        h: int
    ):
        """Dibuja el panel de información en la imagen"""
        # Panel superior con información
        panel_height = 180
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        
        # Título
        cv2.putText(
            image, 
            "ABDUCCION BILATERAL DE HOMBROS (FRONTAL)", 
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            self.color_cache['white'], 
            2, 
            cv2.LINE_4
        )
        
        # Ángulos actuales
        cv2.putText(
            image, 
            f"Izquierdo: {self.left_angle:.1f}deg | Derecho: {self.right_angle:.1f}deg", 
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            self.color_cache['cyan'], 
            2, 
            cv2.LINE_4
        )
        
        # ROM máximo de cada lado
        cv2.putText(
            image, 
            f"ROM Max: Izq {self.left_max_rom:.1f}deg | Der {self.right_max_rom:.1f}deg", 
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            self.color_cache['green'], 
            2, 
            cv2.LINE_4
        )
        
        # Asimetría
        asymmetry_color = self.color_cache['green'] if self.asymmetry < 15 else self.color_cache['orange']
        cv2.putText(
            image, 
            f"Asimetria: {self.asymmetry:.1f}deg", 
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            asymmetry_color, 
            2, 
            cv2.LINE_4
        )
        
        # Estado de postura
        posture_text = "Postura correcta" if self.posture_valid else "Ajusta postura"
        posture_color = self.color_cache['green'] if self.posture_valid else self.color_cache['orange']
        cv2.putText(
            image, 
            posture_text, 
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            posture_color, 
            2, 
            cv2.LINE_4
        )
    
    def _draw_rom_bars(self, image: np.ndarray, w: int, h: int):
        """Dibuja barras de progreso verticales para ROM de cada lado"""
        bar_width = 40
        bar_max_height = 200
        bar_x_left = w - 120
        bar_x_right = w - 60
        bar_y_bottom = h - 50
        
        # Calcular alturas de barras (0-180° = 0-100%)
        left_bar_height = int((self.left_angle / 180) * bar_max_height)
        right_bar_height = int((self.right_angle / 180) * bar_max_height)
        
        # Fondo de las barras
        cv2.rectangle(
            image, 
            (bar_x_left, bar_y_bottom - bar_max_height), 
            (bar_x_left + bar_width, bar_y_bottom), 
            self.color_cache['gray'], 
            -1
        )
        cv2.rectangle(
            image, 
            (bar_x_right, bar_y_bottom - bar_max_height), 
            (bar_x_right + bar_width, bar_y_bottom), 
            self.color_cache['gray'], 
            -1
        )
        
        # Barras de progreso
        cv2.rectangle(
            image, 
            (bar_x_left, bar_y_bottom - left_bar_height), 
            (bar_x_left + bar_width, bar_y_bottom), 
            self.color_cache['cyan'], 
            -1
        )
        cv2.rectangle(
            image, 
            (bar_x_right, bar_y_bottom - right_bar_height), 
            (bar_x_right + bar_width, bar_y_bottom), 
            self.color_cache['purple'], 
            -1
        )
        
        # Etiquetas
        cv2.putText(
            image, 
            "IZQ", 
            (bar_x_left + 5, bar_y_bottom + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            self.color_cache['white'], 
            1, 
            cv2.LINE_4
        )
        cv2.putText(
            image, 
            "DER", 
            (bar_x_right + 5, bar_y_bottom + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            self.color_cache['white'], 
            1, 
            cv2.LINE_4
        )
    
    def _draw_performance_metrics(
        self, 
        image: np.ndarray, 
        current_fps: float, 
        current_processing_time: float
    ):
        """Dibuja métricas de rendimiento en pantalla"""
        h, w = image.shape[:2]
        
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        panel_x = w - 200
        panel_y = h - 100
        
        # Fondo semitransparente
        overlay = image.copy()
        cv2.rectangle(
            overlay, 
            (panel_x - 10, panel_y), 
            (w - 10, h - 10), 
            self.color_cache['gray'], 
            -1
        )
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Métricas
        cv2.putText(
            image, 
            f"FPS: {current_fps:.1f}", 
            (panel_x, panel_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            self.color_cache['green'], 
            1, 
            cv2.LINE_4
        )
        
        cv2.putText(
            image, 
            f"Latencia: {current_processing_time:.1f}ms", 
            (panel_x, panel_y + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            self.color_cache['yellow'], 
            1, 
            cv2.LINE_4
        )
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos actuales del análisis bilateral
        
        Returns:
            Dict con datos de ambos lados (left_angle, right_angle, max_rom, etc.)
        """
        """
        Obtiene los datos actuales del análisis
        
        Returns:
            dict: Diccionario con datos actuales:
                - left_angle: Ángulo izquierdo actual (float)
                - right_angle: Ángulo derecho actual (float)
                - left_max_rom: ROM máximo izquierdo (float)
                - right_max_rom: ROM máximo derecho (float)
                - asymmetry: Asimetría entre lados (float)
                - posture_valid: Si la postura es válida (bool)
                - landmarks_detected: Si se detectaron landmarks (bool)
                - orientation_frontal: Si está en vista frontal (bool)
                - fps: FPS actual (float)
        """
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        # Usar el mayor ángulo de los dos lados como ángulo principal
        # (para abducción bilateral, típicamente se reporta el lado dominante o promedio)
        main_angle = max(self.left_angle, self.right_angle)
        max_rom = max(self.left_max_rom, self.right_max_rom)
        
        return {
            # Campos específicos de frontal (bilateral)
            'left_angle': round(self.left_angle, 2),
            'right_angle': round(self.right_angle, 2),
            'left_max_rom': round(self.left_max_rom, 2),
            'right_max_rom': round(self.right_max_rom, 2),
            'asymmetry': round(self.asymmetry, 2),
            
            # Campos compatibles con analysis_session (igual que profile)
            'angle': round(main_angle, 2),              # Ángulo principal para ROM
            'max_rom': round(max_rom, 2),               # ROM máximo
            'orientation': self.orientation,            # 'frontal' o 'profile'
            'confidence': round(self.confidence, 2),    # Confianza de detección
            'posture_valid': self.posture_valid,
            'landmarks_detected': self.landmarks_detected,
            'is_profile_position': False,               # Siempre False para frontal
            'is_frontal_position': self.is_frontal_position,
            'orientation_quality': round(self.orientation_quality, 2),
            'orientation_frontal': self.orientation_frontal,  # Legacy
            
            # Métricas
            'fps': round(avg_fps, 1),
            'frame_count': self.frame_count
        }
    
    def reset(self):
        """
        Reinicia todas las estadísticas (ROM, ángulos, etc.)
        
        Útil para iniciar una nueva sesión de medición sin recrear el analyzer
        """
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_max_rom = 0.0
        self.right_max_rom = 0.0
        self.asymmetry = 0.0
        self.fps_history.clear()
        self.processing_times.clear()
        self.frame_count = 0
        self.posture_valid = False
        self.landmarks_detected = False
        self.orientation_frontal = False
        self.confidence = 0.0
        self.is_frontal_position = False
        self.orientation_quality = 0.0
        self._was_frontal = False  # Reset histéresis
    
    def cleanup(self):
        """
        Libera recursos del analyzer
        
        ⚠️ CRÍTICO: NO cierra MediaPipe Pose porque es COMPARTIDO (singleton)
        La instancia singleton se mantiene viva en pose_singleton.py
        Solo liberamos la referencia local y limpiamos datos del analyzer
        """
        # Solo liberar referencia (NO cerrar - es singleton compartido)
        self.pose = None
        
        # Limpiar datos locales para liberar memoria
        self.fps_history.clear()
        self.processing_times.clear()
