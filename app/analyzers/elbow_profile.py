"""
💪 ELBOW PROFILE ANALYZER - Análisis de Flexión/Extensión de Codo
===================================================================
Analizador para vista de PERFIL (medición de flexión/extensión del codo)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestión de estado interno (ángulos, ROM máximo)
- API pública para obtener datos actuales

SISTEMA DE MEDICIÓN:
- Eje FIJO: Vertical absoluto (0, 1) que pasa por el CODO
- Brazo MÓVIL: Línea del antebrazo (CODO → MUÑECA)
- 0° = Antebrazo hacia abajo (brazo extendido)
- 150° = Flexión máxima (mano toca hombro)

Autor: BIOTRACK Team
Fecha: 2025-12-02
Basado en: tests/test_elbow_profile.py
"""

import cv2
import mediapipe as mp
import numpy as np
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


class ElbowProfileAnalyzer:
    """
    Analizador de codo en vista de PERFIL
    
    Mide:
    - Flexión (antebrazo hacia arriba, mano hacia hombro)
    - Extensión (antebrazo hacia abajo, brazo recto)
    - ROM máximo alcanzado
    
    Uso en Flask:
        analyzer = ElbowProfileAnalyzer()
        
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
        # Antes: Cada analyzer creaba su Pose() → 22s por analyzer
        # Ahora: TODOS comparten UNA instancia → 12s total, reutilización instantánea
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
        self.is_profile_position = False  # True solo si está realmente de perfil
        self.orientation_quality = 0.0    # 0.0 - 1.0, qué tan bien posicionado está
        
        logger.info("[ElbowProfileAnalyzer] Inicializado con pose singleton compartido")
    
    def calculate_elbow_angle(
        self, 
        shoulder: Tuple[int, int], 
        elbow: Tuple[int, int], 
        wrist: Tuple[int, int],
        orientation: str = ""
    ) -> float:
        """
        Calcula el ángulo de flexión/extensión del codo con eje vertical fijo
        
        Sistema goniómetro estándar (según bibliografía AAOS/AMA):
        - Brazo FIJO: Eje vertical absoluto (0, 1) que pasa por el CODO
        - Brazo MÓVIL: Línea del antebrazo (CODO → MUÑECA)
        - 0° = Antebrazo hacia abajo (brazo extendido - posición neutral)
        - +90° = Antebrazo horizontal (flexión)
        - +150° = Flexión máxima (mano toca hombro)
        - Valores NEGATIVOS = Hiperextensión (antebrazo "pasa" de la vertical)
        
        Detección de Hiperextensión:
        - Usa producto cruz 2D para determinar si el antebrazo está
          "adelante" (flexión) o "atrás" (hiperextensión) del eje vertical
        - Referencia: Beighton Scale - hiperextensión >10° indica hiperlaxitud
        
        Args:
            shoulder: Coordenadas (x, y) del hombro (referencia visual)
            elbow: Coordenadas (x, y) del codo (VÉRTICE del ángulo)
            wrist: Coordenadas (x, y) de la muñeca
            orientation: Orientación de la persona ('mirando izquierda' o 'mirando derecha')
        
        Returns:
            float: Ángulo en grados
                   - Positivo (0° a 180°): Flexión normal
                   - Negativo (-1° a -15°): Hiperextensión
        """
        # Vector vertical fijo (referencia 0° - apunta hacia abajo)
        vertical_down_vector = np.array([0, 1])
        
        # Vector del antebrazo (CODO → MUÑECA) - brazo móvil del goniómetro
        forearm_vector = np.array([wrist[0] - elbow[0], wrist[1] - elbow[1]])
        
        # Normalizar vector del antebrazo
        forearm_norm = np.linalg.norm(forearm_vector)
        
        if forearm_norm == 0:
            return 0.0
        
        forearm_vector_normalized = forearm_vector / forearm_norm
        
        # Calcular ángulo entre eje vertical y antebrazo (magnitud)
        dot_product = np.dot(vertical_down_vector, forearm_vector_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle_magnitude = np.degrees(np.arccos(dot_product))
        
        # =========================================================================
        # DETECCIÓN DE HIPEREXTENSIÓN usando producto cruz 2D
        # =========================================================================
        # Producto cruz 2D: determina en qué lado del eje vertical está el antebrazo
        # cross = Vx * Fy - Vy * Fx
        # donde V = vertical (0, 1) y F = forearm
        # cross = 0 * Fy - 1 * Fx = -Fx = -(wrist_x - elbow_x)
        cross_product = -(wrist[0] - elbow[0])  # Simplificado: -forearm_x
        
        # La interpretación del signo depende de hacia dónde mira la persona:
        # - Mirando DERECHA: flexión es cuando muñeca va hacia la derecha (+X)
        #   → cross negativo = flexión, cross positivo = hiperextensión
        # - Mirando IZQUIERDA: flexión es cuando muñeca va hacia la izquierda (-X)
        #   → cross positivo = flexión, cross negativo = hiperextensión
        
        is_hyperextension = False
        
        if "derecha" in orientation.lower():
            # Mirando derecha: hiperextensión si muñeca está a la IZQUIERDA del codo
            is_hyperextension = cross_product > 0 and angle_magnitude < 30
        elif "izquierda" in orientation.lower():
            # Mirando izquierda: hiperextensión si muñeca está a la DERECHA del codo
            is_hyperextension = cross_product < 0 and angle_magnitude < 30
        
        # Solo considerar hiperextensión para ángulos pequeños (<30°)
        # porque en flexión completa no tiene sentido hablar de hiperextensión
        if is_hyperextension and angle_magnitude < 30:
            # Retornar valor negativo para indicar hiperextensión
            return float(-angle_magnitude)
        
        return float(angle_magnitude)
    
    def detect_side(self, landmarks) -> Tuple[str, float, str]:
        """
        Detecta qué lado del cuerpo se está ANALIZANDO (vista de perfil)
        
        Usa método combinado de profundidad Z + visibilidad para mayor precisión.
        
        ⚠️ IMPORTANTE: La confianza retornada indica la CONFIANZA DE DETECCIÓN DE PERSONA,
        NO la confianza de que esté en perfil. Esto es crucial para que DETECTING_PERSON
        funcione sin importar la orientación.
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (lado, confianza, orientación)
                - lado: 'left' o 'right' (el lado del cuerpo visible hacia la cámara)
                - confianza: float (0-1) - Confianza de DETECCIÓN DE PERSONA
                - orientación: str descripción de la orientación
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        
        # Profundidad promedio (más cerca = más negativo en Z)
        left_depth = (left_shoulder.z + left_elbow.z) / 2
        right_depth = (right_shoulder.z + right_elbow.z) / 2
        
        # Visibilidad promedio
        left_vis = (left_shoulder.visibility + left_elbow.visibility) / 2
        right_vis = (right_shoulder.visibility + right_elbow.visibility) / 2
        
        # Score combinado (profundidad 70%, visibilidad 30%)
        left_score = (-left_depth * 0.7) + (left_vis * 0.3)
        right_score = (-right_depth * 0.7) + (right_vis * 0.3)
        
        # ⚡ CONFIANZA DE DETECCIÓN DE PERSONA (no de orientación)
        # Se basa en la visibilidad promedio de los landmarks clave
        # Si vemos bien los hombros y codos = persona detectada con confianza
        avg_visibility = (left_shoulder.visibility + right_shoulder.visibility + 
                         left_elbow.visibility + right_elbow.visibility + 
                         nose.visibility) / 5
        detection_confidence = min(avg_visibility * 1.2, 1.0)  # Escalar ligeramente
        
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        
        if left_score > right_score:
            side = 'left'
            orientation = "mirando izquierda" if nose.x < shoulder_center_x else "mirando derecha"
        else:
            side = 'right'
            orientation = "mirando derecha" if nose.x > shoulder_center_x else "mirando izquierda"
        
        return side, detection_confidence, orientation
    
    def verify_profile_position(self, landmarks) -> Tuple[bool, float, str]:
        """
        Verifica si la persona está REALMENTE en posición de perfil.
        
        Para estar en perfil:
        - Los hombros deben estar alineados (diferencia X pequeña)
        - Un hombro debe tener visibilidad significativamente mayor que el otro
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (is_profile, quality, message)
                - is_profile: True si está en perfil válido
                - quality: float (0-1) calidad de la posición
                - message: Mensaje descriptivo
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # 1. Verificar diferencia de visibilidad entre hombros
        visibility_diff = abs(left_shoulder.visibility - right_shoulder.visibility)
        
        # 2. Verificar alineación de hombros (en perfil, están casi en la misma X)
        shoulder_x_diff = abs(left_shoulder.x - right_shoulder.x)
        
        # 3. Verificar alineación de caderas
        hip_x_diff = abs(left_hip.x - right_hip.x)
        
        # Umbrales para considerar perfil válido
        SHOULDER_ALIGNMENT_THRESHOLD = 0.25
        VISIBILITY_DIFF_THRESHOLD = 0.15
        HIP_ALIGNMENT_THRESHOLD = 0.25
        
        # Calcular scores individuales
        alignment_score = max(0, 1 - (shoulder_x_diff / SHOULDER_ALIGNMENT_THRESHOLD))
        visibility_score = min(1, visibility_diff / VISIBILITY_DIFF_THRESHOLD)
        hip_score = max(0, 1 - (hip_x_diff / HIP_ALIGNMENT_THRESHOLD))
        
        # Score total (promedio ponderado)
        quality = (alignment_score * 0.4 + visibility_score * 0.3 + hip_score * 0.3)
        
        # Determinar si está en perfil
        is_profile = shoulder_x_diff < SHOULDER_ALIGNMENT_THRESHOLD
        
        # Generar mensaje descriptivo
        if is_profile:
            if quality > 0.7:
                message = "Perfil excelente"
            elif quality > 0.5:
                message = "Perfil bueno"
            else:
                message = "Perfil aceptable"
        else:
            if shoulder_x_diff > 0.3:
                message = "Gira más hacia el perfil"
            else:
                message = "Ajusta tu posición"
        
        # Actualizar estado interno
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
            h, w = original_h, original_w
            landmarks = results.pose_landmarks.landmark
            
            self.landmarks_detected = True
            
            # Detectar lado visible (retorna confianza de detección de lado)
            side, detection_confidence, raw_orientation = self.detect_side(landmarks)
            self.side = side  # Mantener 'left'/'right' para compatibilidad con DB
            
            # ⚡ NUEVO: Verificar si realmente está en posición de perfil
            is_profile, profile_quality, profile_msg = self.verify_profile_position(landmarks)
            self.is_profile_position = is_profile
            
            # Actualizar orientación con verificación real
            if is_profile:
                self.orientation = "profile"  # Usar "profile" cuando es válido
                self.posture_valid = True
            else:
                self.orientation = "frontal"  # No está en perfil = está de frente
                self.posture_valid = False
            
            # ⚠️ IMPORTANTE: Para DETECTING_PERSON usar solo la confianza de detección
            # Para CHECKING_ORIENTATION se usará orientation_quality
            # La confianza de detección NO debe depender de si está en perfil o no
            # Usamos una confianza alta si detectamos landmarks básicos
            self.confidence = detection_confidence  # Confianza de que hay persona
            self.orientation_quality = profile_quality  # Calidad de perfil por separado
            
            # Dibujar skeleton completo si está habilitado
            if self.show_skeleton:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            # Procesar vista de perfil
            self._process_profile_view(image, landmarks, w, h, side, self.orientation, detection_confidence)
            
            # Dibujar panel de información (COMENTADO - info ya visible en panel web)
            # self._draw_info_panel(image, self.orientation, detection_confidence, w, h)
            
        else:
            self.landmarks_detected = False
            self.posture_valid = False
            cv2.putText(
                image, "No se detecta persona", (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, self.color_cache['red'], 2, cv2.LINE_4
            )
        
        # Calcular métricas de rendimiento
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_time) if (current_time - self.last_time) > 0 else 0
        self.fps_history.append(fps)
        self.last_time = current_time
        
        # Dibujar métricas de rendimiento (COMENTADO - info ya visible en panel web)
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
        Procesa vista de perfil - Análisis de flexión/extensión de codo
        
        Args:
            image: Frame a dibujar
            landmarks: Landmarks de MediaPipe
            w: Ancho del frame
            h: Alto del frame
            side: Lado detectado ('left' o 'right')
            orientation: Orientación de la persona
            confidence: Confianza de detección
        """
        # Seleccionar landmarks según el lado detectado
        if side == 'left':
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
            wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
            side_display = "IZQUIERDO"  # Para mostrar en pantalla
        else:
            shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
            wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
            side_display = "DERECHO"  # Para mostrar en pantalla
        
        # IMPORTANTE: self.side debe ser 'left' o 'right' para compatibilidad con DB
        # La DB tiene CHECK constraint: side IN ('left', 'right', 'bilateral')
        self.side = side  # Mantener 'left'/'right' para el sistema
        
        # Obtener coordenadas 2D
        shoulder_2d = self.get_landmarks_2d(shoulder, w, h)
        elbow_2d = self.get_landmarks_2d(elbow, w, h)
        wrist_2d = self.get_landmarks_2d(wrist, w, h)
        
        # Calcular ángulo de flexión del codo (pasamos orientación para detectar hiperextensión)
        angle = self.calculate_elbow_angle(shoulder_2d, elbow_2d, wrist_2d, orientation)
        
        # Actualizar estadísticas
        self.current_angle = angle
        
        # Para ROM máximo, usamos valor absoluto porque hiperextensión también es ROM
        # Pero mantenemos el signo en current_angle para saber si es hiperextensión
        if abs(angle) > abs(self.max_angle):
            self.max_angle = angle
        
        # ===== VISUALIZACIÓN =====
        
        # Dibujar puntos clave
        cv2.circle(image, elbow_2d, 12, self.color_cache['yellow'], -1, cv2.LINE_4)  # CODO (vértice)
        cv2.circle(image, shoulder_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4)  # HOMBRO
        cv2.circle(image, wrist_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4)  # MUÑECA
        
        # Borde negro para mayor visibilidad
        cv2.circle(image, elbow_2d, 14, (0, 0, 0), 2, cv2.LINE_4)
        
        # Línea de referencia vertical fija que pasa por el CODO
        vertical_length = 150
        vertical_start = (elbow_2d[0], elbow_2d[1] - vertical_length)
        vertical_end = (elbow_2d[0], elbow_2d[1] + vertical_length)
        cv2.line(image, vertical_start, vertical_end, self.color_cache['green'], 3, cv2.LINE_4)
        
        # Etiqueta del eje vertical (usamos 'o' superíndice porque OpenCV no renderiza bien '°')
        cv2.putText(
            image, "0", 
            (elbow_2d[0] + 10, elbow_2d[1] + vertical_length - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color_cache['green'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "o", 
            (elbow_2d[0] + 22, elbow_2d[1] + vertical_length - 18),  # Posición elevada
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, self.color_cache['green'], 1, cv2.LINE_4
        )
        
        # Línea del antebrazo (CODO → MUÑECA) - brazo móvil del goniómetro
        forearm_color = self._get_angle_color(angle)
        cv2.line(image, elbow_2d, wrist_2d, forearm_color, 4, cv2.LINE_4)
        
        # Brazo superior (HOMBRO → CODO) - referencia visual
        cv2.line(image, shoulder_2d, elbow_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Dibujar arco del ángulo
        self._draw_angle_arc(image, elbow_2d, angle)
        
        # Mostrar ángulo junto al codo (usamos 'o' superíndice porque OpenCV no renderiza bien '°')
        angle_num = f"{angle:.1f}"
        text_pos = (elbow_2d[0] + 20, elbow_2d[1] - 30)
        
        # Fondo para el texto (calculamos tamaño con número + espacio para 'o')
        (text_w, text_h), _ = cv2.getTextSize(angle_num, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        cv2.rectangle(
            image, 
            (text_pos[0] - 5, text_pos[1] - text_h - 5),
            (text_pos[0] + text_w + 15, text_pos[1] + 5),  # +15 para el símbolo 'o'
            (0, 0, 0), -1
        )
        # Número del ángulo
        cv2.putText(
            image, angle_num, text_pos,
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, forearm_color, 2, cv2.LINE_4
        )
        # Símbolo 'o' superíndice
        cv2.putText(
            image, "o", (text_pos[0] + text_w + 2, text_pos[1] - 15),  # Posición elevada
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, forearm_color, 1, cv2.LINE_4
        )
        
        # Indicador de estado de flexión/extensión/hiperextensión (COMENTADO - info ya visible en panel web)
        # if angle < 0:
        #     # Ángulo negativo = HIPEREXTENSIÓN
        #     status = "HIPEREXTENSION"
        #     status_color = (0, 191, 255)  # Amarillo dorado (RGB: 255, 191, 0 → BGR)
        # elif angle < 30:
        #     status = "EXTENSION"
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
        #     (elbow_2d[0] - 60, elbow_2d[1] + 40),
        #     cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2, cv2.LINE_4
        # )
    
    def _draw_angle_arc(
        self, 
        image: np.ndarray, 
        center: Tuple[int, int], 
        angle: float, 
        radius: int = 40
    ):
        """
        Dibuja un arco visual que representa el ángulo medido
        
        Args:
            image: Frame a dibujar
            center: Centro del arco (posición del codo)
            angle: Ángulo a representar (puede ser negativo para hiperextensión)
            radius: Radio del arco
        """
        # El arco va desde la vertical (90° en coordenadas OpenCV) hacia el antebrazo
        # En OpenCV, 0° es hacia la derecha, 90° hacia abajo
        start_angle = 90  # Vertical hacia abajo
        
        # Para hiperextensión (ángulo negativo), el arco va hacia el otro lado
        if angle < 0:
            # Hiperextensión: arco va hacia el lado opuesto
            end_angle = 90 + abs(angle)  # Hacia atrás de la vertical
        else:
            end_angle = 90 - angle  # Hacia donde apunta el antebrazo (flexión)
        
        if angle != 0:
            color = self._get_angle_color(angle)
            cv2.ellipse(
                image, center, (radius, radius),
                0, min(start_angle, end_angle), max(start_angle, end_angle),
                color, 2, cv2.LINE_4
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
        Dibuja panel de información en la imagen
        
        Args:
            image: Frame a dibujar
            orientation: Orientación detectada
            confidence: Confianza de detección
            w: Ancho del frame
            h: Alto del frame
        """
        # Panel superior con información
        panel_height = 160
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        
        # Título
        title = "ANÁLISIS DE CODO (PERFIL)"
        cv2.putText(
            image, title, (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, self.color_cache['cyan'], 2, cv2.LINE_4
        )
        
        # Lado detectado
        color_side = self.color_cache['green'] if confidence > 0.5 else self.color_cache['orange']
        cv2.putText(
            image, f"Lado: {self.side}", (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_side, 2, cv2.LINE_4
        )
        
        # Ángulo actual (usamos 'deg' porque OpenCV no renderiza bien '°')
        angle_color = self._get_angle_color(self.current_angle)
        cv2.putText(
            image, f"Angulo Actual: {self.current_angle:.1f}deg", (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, angle_color, 2, cv2.LINE_4
        )
        
        # ROM Máximo
        cv2.putText(
            image, f"ROM Maximo: {self.max_angle:.1f}deg", (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.color_cache['green'], 2, cv2.LINE_4
        )
        
        # Barra de progreso ROM
        self._draw_rom_bar(image, w, h)
    
    def _draw_rom_bar(self, image: np.ndarray, width: int, height: int):
        """
        Dibuja barra de progreso del ROM de codo
        
        Args:
            image: Frame a dibujar
            width: Ancho del frame
            height: Alto del frame
        """
        bar_x = width - 300
        bar_y = 50
        bar_width = 260
        bar_height = 30
        
        # Fondo de la barra
        cv2.rectangle(
            image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
            self.color_cache['gray'], -1
        )
        cv2.rectangle(
            image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
            self.color_cache['white'], 2
        )
        
        # Rango de codo: -15° (hiperextensión) a 150° (flexión máxima)
        # La barra muestra el rango completo con el 0° en su posición proporcional
        min_range = -15
        max_range = 150
        total_range = max_range - min_range  # 165°
        
        # Calcular posición del cero (punto de referencia)
        zero_position = int(bar_width * abs(min_range) / total_range)
        
        # Calcular posición del ángulo actual
        angle_clamped = max(min_range, min(self.current_angle, max_range))
        current_position = int(bar_width * (angle_clamped - min_range) / total_range)
        
        # Color según ángulo
        color = self._get_angle_color(self.current_angle)
        
        # Dibujar línea de referencia en 0° (línea vertical blanca)
        cv2.line(
            image,
            (bar_x + zero_position, bar_y),
            (bar_x + zero_position, bar_y + bar_height),
            self.color_cache['white'], 2, cv2.LINE_4
        )
        
        # Llenar barra desde 0° hasta el ángulo actual
        if self.current_angle >= 0:
            # Flexión: llenar desde 0 hacia la derecha
            cv2.rectangle(
                image, (bar_x + zero_position, bar_y), 
                (bar_x + current_position, bar_y + bar_height), 
                color, -1
            )
        else:
            # Hiperextensión: llenar desde 0 hacia la izquierda
            cv2.rectangle(
                image, (bar_x + current_position, bar_y), 
                (bar_x + zero_position, bar_y + bar_height), 
                color, -1
            )
        
        # Indicador de posición actual
        cv2.line(
            image, 
            (bar_x + current_position, bar_y - 5), 
            (bar_x + current_position, bar_y + bar_height + 5), 
            self.color_cache['yellow'], 3, cv2.LINE_4
        )
        
        # Texto de referencia
        cv2.putText(
            image, "ROM Codo", (bar_x, bar_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color_cache['white'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "-15", (bar_x - 15, bar_y + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.color_cache['white'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "0", (bar_x + zero_position - 5, bar_y + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.color_cache['green'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "90", (bar_x + int(bar_width * 0.6), bar_y + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.color_cache['white'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "150", (bar_x + bar_width - 20, bar_y + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.color_cache['white'], 1, cv2.LINE_4
        )
    
    def _draw_performance_metrics(
        self, 
        image: np.ndarray, 
        current_fps: float, 
        current_processing_time: float
    ):
        """
        Dibuja métricas de rendimiento en esquina superior derecha
        
        Args:
            image: Frame a dibujar
            current_fps: FPS actual
            current_processing_time: Tiempo de procesamiento actual en ms
        """
        h, w = image.shape[:2]
        
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        panel_x = w - 180
        panel_y = 100
        
        # Fondo semitransparente
        overlay = image.copy()
        cv2.rectangle(overlay, (panel_x - 10, panel_y), (w - 10, panel_y + 60), 
                     self.color_cache['gray'], -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Métricas
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
        Retorna color según el ángulo de flexión/extensión
        
        Args:
            angle: Ángulo en grados (puede ser negativo para hiperextensión)
        
        Returns:
            tuple: Color BGR
        """
        if angle < 0:
            return (0, 191, 255)               # Hiperextensión - Amarillo dorado (BGR)
        elif angle < 30:
            return self.color_cache['white']   # Casi extendido
        elif angle < 60:
            return self.color_cache['yellow']  # Poco flexionado
        elif angle < 90:
            return self.color_cache['orange']  # Medio flexionado
        elif angle < 120:
            return self.color_cache['magenta'] # Muy flexionado
        else:
            return self.color_cache['green']   # Flexión máxima
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos actuales del análisis
        
        API PÚBLICA - Usar para obtener datos en tiempo real
        
        Returns:
            dict: Datos actuales del análisis
        """
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        # Determinar tipo de movimiento basado en el ángulo
        if self.current_angle < 0:
            movement = 'hyperextension'  # Hiperextensión (ángulo negativo)
        elif self.current_angle < 30:
            movement = 'extension'       # Extensión normal
        else:
            movement = 'flexion'         # Flexión
        
        return {
            # Campos ESTÁNDAR (compatibles con todos los analyzers)
            'angle': round(self.current_angle, 1),
            'max_rom': round(abs(self.max_angle), 1),  # Valor absoluto para ROM
            'side': self.side,
            'orientation': self.orientation,
            'confidence': round(self.confidence, 2),
            'posture_valid': self.posture_valid,
            'landmarks_detected': self.landmarks_detected,
            'is_profile_position': self.is_profile_position,
            'orientation_quality': round(self.orientation_quality, 2),
            'fps': round(avg_fps, 1),
            'frame_count': self.frame_count,
            # Campos adicionales para codo
            'current_angle': round(self.current_angle, 1),  # Alias para compatibilidad
            'max_angle': round(self.max_angle, 1),          # Alias (puede ser negativo)
            'processing_time_ms': round(avg_processing, 1),
            'rom_max': round(abs(self.max_angle), 1),       # Alias
            'rom_min': 0.0,
            'analysis_type': 'elbow_profile',
            'movement_type': movement,
            # Campos específicos de hiperextensión
            'is_hyperextension': self.current_angle < 0,
            'hyperextension_angle': round(abs(self.current_angle), 1) if self.current_angle < 0 else 0.0
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
        logger.info("[ElbowProfileAnalyzer] Estadísticas reiniciadas")
    
    def cleanup(self):
        """
        Limpia recursos del analyzer
        
        NOTA: NO cerrar el pose porque es compartido (singleton)
        """
        logger.info("[ElbowProfileAnalyzer] Cleanup - pose compartido NO se cierra")
        # NO hacer self.pose.close() porque es singleton compartido
        pass
