"""
🦶 ANKLE PROFILE ANALYZER - Análisis de Dorsiflexión/Plantarflexión de Tobillo
===============================================================================
Analizador para vista de PERFIL (medición de dorsiflexión/plantarflexión)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestión de estado interno (ángulos, ROM máximo)
- API pública para obtener datos actuales

SISTEMA DE MEDICIÓN (basado en test_ankle_profile.py):
- VÉRTICE: TOBILLO (maléolo lateral del peroné)
- Brazo FIJO: Eje vertical absoluto (0, 1) que pasa por el TOBILLO
- Brazo MÓVIL: Vector PARALELO a la planta del pie (TALÓN → DEDOS)

Conversión de ángulos:
- ~90° interno = Posición NEUTRA (planta paralela al suelo) → 0° mostrado
- < 85° interno = FLEXIÓN PLANTAR (dedos hacia abajo) → 0-50° mostrado
- > 95° interno = DORSIFLEXIÓN (dedos hacia arriba) → 0-20° mostrado

Landmarks utilizados:
- Rodilla: LEFT_KNEE (25), RIGHT_KNEE (26)
- Tobillo: LEFT_ANKLE (27), RIGHT_ANKLE (28)
- Talón: LEFT_HEEL (29), RIGHT_HEEL (30)
- Punta del pie: LEFT_FOOT_INDEX (31), RIGHT_FOOT_INDEX (32)

Autor: BIOTRACK Team
Fecha: 2025-12-07
Basado en: test_ankle_profile.py (sistema validado)
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


class AnkleProfileAnalyzer:
    """
    Analizador de tobillo en vista de PERFIL
    
    Mide:
    - Dorsiflexión (pie hacia arriba, hacia espinilla) - 0° a 20°
    - Plantarflexión (pie hacia abajo, punta) - 0° a 50°
    - ROM máximo alcanzado
    
    Uso en Flask:
        analyzer = AnkleProfileAnalyzer()
        
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
        self.current_angle = 0.0          # Ángulo mostrado (0° = neutro)
        self.raw_angle = 90.0             # Ángulo sin procesar (90° = neutro)
        self.max_dorsiflexion = 0.0       # Máximo en dorsiflexión (0-20°)
        self.max_plantarflexion = 0.0     # Máximo en flexión plantar (0-50°)
        self.max_angle = 0.0              # Máximo general (para compatibilidad)
        self.side = "Detectando..."
        self.orientation = "Detectando..."
        self.confidence = 0.0
        self.frame_count = 0
        
        # Tipo de movimiento actual
        self.current_movement = "neutral"  # "dorsiflexion", "plantarflexion", "neutral"
        
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
        
        logger.info("[AnkleProfileAnalyzer] Inicializado con pose singleton compartido")
    
    def calculate_ankle_angle(
        self, 
        ankle: Tuple[int, int], 
        heel: Tuple[int, int], 
        foot_index: Tuple[int, int]
    ) -> Tuple[float, float, str]:
        """
        Calcula el ángulo de dorsiflexión/plantarflexión del tobillo
        
        Sistema goniómetro (IDÉNTICO a test_ankle_profile.py):
        - VÉRTICE: TOBILLO (maléolo lateral del peroné)
        - Brazo FIJO: Eje vertical absoluto (0, 1) que pasa por el TOBILLO
        - Brazo MÓVIL: Vector PARALELO a la planta del pie (TALÓN → DEDOS)
        
        Returns:
            tuple: (ángulo_mostrar, ángulo_raw, tipo_movimiento)
                - ángulo_mostrar: Ángulo a mostrar (0° = neutro, siempre positivo)
                - ángulo_raw: Ángulo real medido desde vertical (85-95° = neutro)
                - tipo_movimiento: 'dorsiflexion', 'plantarflexion', o 'neutral'
        """
        # Vector vertical fijo (referencia - apunta hacia abajo)
        vertical_down_vector = np.array([0, 1])
        
        # Vector de la PLANTA del pie (TALÓN → DEDOS)
        # Este vector representa la orientación de la superficie plantar
        sole_vector = np.array([foot_index[0] - heel[0], foot_index[1] - heel[1]])
        
        # Normalizar vector de la planta
        sole_norm = np.linalg.norm(sole_vector)
        
        if sole_norm == 0:
            return 0.0, 90.0, "neutral"
        
        sole_vector_normalized = sole_vector / sole_norm
        
        # Calcular ángulo entre eje vertical y vector de la planta
        dot_product = np.dot(vertical_down_vector, sole_vector_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        
        # Ángulo sin signo (0° a 180°)
        raw_angle = np.degrees(np.arccos(dot_product))
        
        # Convertir a ángulo de visualización
        # 90° interno → 0° mostrado (NEUTRO - planta paralela al suelo)
        # < 85° interno → PLANTARFLEXIÓN (dedos apuntan hacia abajo)
        # > 95° interno → DORSIFLEXIÓN (dedos apuntan hacia arriba)
        
        if raw_angle < 85:
            # Plantarflexión (dedos hacia abajo)
            display_angle = 90 - raw_angle
            movement_type = "plantarflexion"
        elif raw_angle <= 95:
            # Rango neutro (85-95°)
            display_angle = 0.0
            movement_type = "neutral"
        else:
            # Dorsiflexión (dedos hacia arriba)
            display_angle = raw_angle - 90
            movement_type = "dorsiflexion"
        
        return float(display_angle), float(raw_angle), movement_type
    
    def detect_side(self, landmarks) -> Tuple[str, float, str]:
        """
        Detecta qué lado del cuerpo se está ANALIZANDO (vista de perfil)
        
        LÓGICA (considerando que la cámara ve como espejo - igual que shoulder_profile):
        - La imagen de la webcam es como verte en un espejo
        - Si en la imagen la nariz está a la DERECHA del centro → 
          en realidad estás mirando a TU IZQUIERDA → lado DERECHO visible
        - Si en la imagen la nariz está a la IZQUIERDA del centro → 
          en realidad estás mirando a TU DERECHA → lado IZQUIERDO visible
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (lado, confianza, orientación)
        """
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        
        # Calcular visibilidad para confianza
        left_visibility = (left_ankle.visibility + left_knee.visibility) / 2
        right_visibility = (right_ankle.visibility + right_knee.visibility) / 2
        confidence = max(left_visibility, right_visibility)
        
        # Centro del cuerpo (usando tobillos)
        ankle_center_x = (left_ankle.x + right_ankle.x) / 2
        
        # LÓGICA ESPEJO (igual que shoulder_profile.py):
        # En la imagen (efecto espejo):
        # nose.x > center → en imagen miras a la derecha → en realidad miras a TU izquierda
        #                 → Tu lado DERECHO está hacia la cámara
        # nose.x < center → en imagen miras a la izquierda → en realidad miras a TU derecha
        #                 → Tu lado IZQUIERDO está hacia la cámara
        if nose.x > ankle_center_x:
            # En imagen: nariz a la derecha → Tú miras a TU izquierda
            # → Tu lado DERECHO está hacia la cámara
            side = 'right'
            orientation = "mirando izquierda"
        else:
            # En imagen: nariz a la izquierda → Tú miras a TU derecha
            # → Tu lado IZQUIERDO está hacia la cámara
            side = 'left'
            orientation = "mirando derecha"
        
        return side, float(confidence), orientation
    
    def verify_profile_position(self, landmarks) -> Tuple[bool, float, str]:
        """
        Verifica si la persona está REALMENTE en posición de perfil.
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (is_profile, quality, message)
        """
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        
        # Verificar diferencia de visibilidad
        visibility_diff = abs(left_hip.visibility - right_hip.visibility)
        
        # Verificar alineación de caderas
        hip_x_diff = abs(left_hip.x - right_hip.x)
        
        # Verificar alineación de hombros
        shoulder_x_diff = abs(left_shoulder.x - right_shoulder.x)
        
        # Verificar alineación de tobillos
        ankle_x_diff = abs(left_ankle.x - right_ankle.x)
        
        # ⚠️ UMBRALES MUY ESTRICTOS para perfil de TOBILLO
        HIP_ALIGNMENT_THRESHOLD = 0.08
        VISIBILITY_DIFF_THRESHOLD = 0.25
        SHOULDER_ALIGNMENT_THRESHOLD = 0.08
        ANKLE_ALIGNMENT_THRESHOLD = 0.10  # Tobillos pueden estar un poco más separados
        
        # Calcular scores
        hip_alignment_score = max(0, 1 - (hip_x_diff / HIP_ALIGNMENT_THRESHOLD))
        visibility_score = min(1, visibility_diff / VISIBILITY_DIFF_THRESHOLD)
        shoulder_score = max(0, 1 - (shoulder_x_diff / SHOULDER_ALIGNMENT_THRESHOLD))
        ankle_score = max(0, 1 - (ankle_x_diff / ANKLE_ALIGNMENT_THRESHOLD))
        
        # Score total (tobillos importantes para este análisis)
        quality = (hip_alignment_score * 0.3 + visibility_score * 0.2 + 
                   shoulder_score * 0.2 + ankle_score * 0.3)
        
        # Para ser perfil, TODOS deben estar alineados
        is_profile = (hip_x_diff < HIP_ALIGNMENT_THRESHOLD and 
                      shoulder_x_diff < SHOULDER_ALIGNMENT_THRESHOLD and
                      ankle_x_diff < ANKLE_ALIGNMENT_THRESHOLD and
                      quality > 0.4)
        
        # DEBUG log
        if self.frame_count % 30 == 0:
            logger.info(f"[ANKLE_PROFILE_CHECK] shoulder_x={shoulder_x_diff:.3f}, "
                       f"hip_x={hip_x_diff:.3f}, ankle_x={ankle_x_diff:.3f}, "
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
        """Convierte landmarks normalizados a coordenadas de píxeles"""
        return (
            int(landmark.x * frame_width), 
            int(landmark.y * frame_height)
        )
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un frame y retorna el frame anotado
        
        Args:
            frame: Frame de OpenCV (BGR numpy array)
        
        Returns:
            np.ndarray: Frame procesado con anotaciones visuales
        """
        start_time = time.time()
        self.frame_count += 1
        
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
        
        image_rgb.flags.writeable = True
        image = frame.copy()
        
        if results.pose_landmarks:
            h, w = original_h, original_w
            landmarks = results.pose_landmarks.landmark
            
            self.landmarks_detected = True
            
            # Detectar lado visible
            side, detection_confidence, raw_orientation = self.detect_side(landmarks)
            self.side = side
            
            # Verificar perfil
            is_profile, profile_quality, profile_msg = self.verify_profile_position(landmarks)
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
            
        else:
            self.landmarks_detected = False
            self.posture_valid = False
            cv2.putText(
                image, "No se detecta persona", (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, self.color_cache['red'], 2, cv2.LINE_4
            )
        
        # Métricas de rendimiento
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_time) if (current_time - self.last_time) > 0 else 0
        self.fps_history.append(fps)
        self.last_time = current_time
        
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
        """Procesa vista de perfil - Análisis de dorsiflexión/plantarflexión"""
        
        # Seleccionar landmarks según el lado detectado
        if side == 'left':
            knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            heel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL]
            foot_index = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
            side_display = "IZQUIERDA"
        else:
            knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
            heel = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL]
            foot_index = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]
            side_display = "DERECHA"
        
        self.side = side
        
        # Obtener coordenadas 2D
        knee_2d = self.get_landmarks_2d(knee, w, h)
        ankle_2d = self.get_landmarks_2d(ankle, w, h)
        heel_2d = self.get_landmarks_2d(heel, w, h)
        foot_index_2d = self.get_landmarks_2d(foot_index, w, h)
        
        # Calcular ángulo usando método del test (vector planta vs vertical)
        display_angle, raw_angle, movement_type = self.calculate_ankle_angle(
            ankle_2d, heel_2d, foot_index_2d
        )
        
        # Actualizar estadísticas
        self.current_angle = display_angle
        self.raw_angle = raw_angle
        self.current_movement = movement_type
        
        # Actualizar máximos según tipo de movimiento
        if movement_type == "dorsiflexion" and display_angle > self.max_dorsiflexion:
            self.max_dorsiflexion = display_angle
        elif movement_type == "plantarflexion" and display_angle > self.max_plantarflexion:
            self.max_plantarflexion = display_angle
        
        # Actualizar max_angle general (para compatibilidad)
        self.max_angle = max(self.max_dorsiflexion, self.max_plantarflexion)
        
        # ===== VISUALIZACIÓN =====
        
        # Dibujar puntos clave
        cv2.circle(image, ankle_2d, 12, self.color_cache['yellow'], -1, cv2.LINE_4)  # TOBILLO (vértice)
        cv2.circle(image, knee_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4)   # RODILLA
        cv2.circle(image, heel_2d, 6, self.color_cache['white'], -1, cv2.LINE_4)     # TALÓN
        cv2.circle(image, foot_index_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4) # DEDOS
        
        # Borde negro para mayor visibilidad
        cv2.circle(image, ankle_2d, 14, (0, 0, 0), 2, cv2.LINE_4)
        
        # Etiqueta del vértice
        cv2.putText(image, "TOBILLO", 
                   (ankle_2d[0] + 15, ankle_2d[1] - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.color_cache['yellow'], 1, cv2.LINE_4)
        
        # ===== LÍNEA VERTICAL (Brazo FIJO del goniómetro) =====
        vertical_length = 120
        vertical_start = (ankle_2d[0], ankle_2d[1] - vertical_length)
        vertical_end = (ankle_2d[0], ankle_2d[1] + vertical_length)
        cv2.line(image, vertical_start, vertical_end, self.color_cache['green'], 2, cv2.LINE_4)
        
        # ===== LÍNEA PARALELA A LA PLANTA (Brazo MÓVIL del goniómetro) =====
        # Vector de la planta del pie (TALÓN → DEDOS)
        sole_vector = np.array([foot_index_2d[0] - heel_2d[0], foot_index_2d[1] - heel_2d[1]])
        sole_length = np.linalg.norm(sole_vector)
        
        if sole_length > 0:
            # Normalizar vector de la planta
            sole_vector_normalized = sole_vector / sole_length
            
            # Calcular punto final del brazo móvil (paralelo a planta, desde tobillo)
            display_length = 100
            parallel_end_point = (
                int(ankle_2d[0] + sole_vector_normalized[0] * display_length),
                int(ankle_2d[1] + sole_vector_normalized[1] * display_length)
            )
            
            # Dibujar línea desde TOBILLO en dirección paralela a la planta
            foot_color = self._get_angle_color(display_angle, movement_type)
            cv2.line(image, ankle_2d, parallel_end_point, foot_color, 4, cv2.LINE_4)
            
            # Etiqueta en el brazo móvil
            label_pos = (
                int(ankle_2d[0] + sole_vector_normalized[0] * display_length * 0.6),
                int(ankle_2d[1] + sole_vector_normalized[1] * display_length * 0.6) - 10
            )
            cv2.putText(image, "PLANTA", label_pos,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, foot_color, 1, cv2.LINE_4)
        
        # ===== LÍNEAS DE REFERENCIA (contexto anatómico) =====
        # Línea de la planta real (TALÓN → DEDOS) - gris para referencia
        cv2.line(image, heel_2d, foot_index_2d, self.color_cache['light_gray'], 2, cv2.LINE_4)
        
        # Pierna inferior (RODILLA → TOBILLO)
        cv2.line(image, knee_2d, ankle_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Dibujar arco del ángulo
        self._draw_angle_arc(image, ankle_2d, display_angle, movement_type)
        
        # Mostrar ángulo
        angle_num = f"{display_angle:.1f}"
        text_pos = (ankle_2d[0] + 20, ankle_2d[1] - 30)
        
        # Fondo para el texto
        (text_w, text_h), _ = cv2.getTextSize(angle_num, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        cv2.rectangle(
            image, 
            (text_pos[0] - 5, text_pos[1] - text_h - 5),
            (text_pos[0] + text_w + 15, text_pos[1] + 5),
            (0, 0, 0), -1
        )
        cv2.putText(
            image, angle_num, text_pos,
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, self._get_angle_color(display_angle, movement_type), 2, cv2.LINE_4
        )
        cv2.putText(
            image, "o", (text_pos[0] + text_w + 2, text_pos[1] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, self._get_angle_color(display_angle, movement_type), 1, cv2.LINE_4
        )
        
        # Indicador de tipo de movimiento con colores diferenciados
        if movement_type == "dorsiflexion":
            movement_label = "DORSI"
            movement_color = self.color_cache['cyan']
        elif movement_type == "plantarflexion":
            movement_label = "PLANTAR"
            movement_color = self.color_cache['orange']
        else:
            movement_label = "NEUTRO"
            movement_color = self.color_cache['white']
        
        cv2.putText(
            image, movement_label, (ankle_2d[0] + 20, ankle_2d[1] + 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, movement_color, 2, cv2.LINE_4
        )
        
        # Indicador del lado
        cv2.putText(
            image, f"Pie: {side_display}", (20, h - 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color_cache['white'], 2, cv2.LINE_4
        )
    
    def _draw_angle_arc(
        self, 
        image: np.ndarray, 
        center: Tuple[int, int], 
        angle: float,
        movement_type: str,
        radius: int = 35
    ):
        """Dibuja un arco visual que representa el ángulo medido"""
        if angle < 1:
            return
        
        color = self._get_angle_color(angle, movement_type)
        
        # El arco siempre desde vertical (270° en sistema OpenCV donde 0° es derecha)
        # Para dorsiflexión: arco hacia arriba (dedos suben)
        # Para plantarflexión: arco hacia abajo (dedos bajan)
        if movement_type == "dorsiflexion":
            start_angle = 270 - angle
            end_angle = 270
        else:  # plantarflexion
            start_angle = 270
            end_angle = 270 + angle
        
        cv2.ellipse(
            image, center, (radius, radius),
            0, start_angle, end_angle,
            color, 2, cv2.LINE_4
        )
    
    def _get_angle_color(self, angle: float, movement_type: str) -> Tuple[int, int, int]:
        """Retorna color según el ángulo y tipo de movimiento"""
        if movement_type == "dorsiflexion":
            # Dorsiflexión: rango típico 0-20°
            if angle < 5:
                return self.color_cache['white']
            elif angle < 10:
                return self.color_cache['yellow']
            elif angle < 15:
                return self.color_cache['orange']
            else:
                return self.color_cache['green']
        else:
            # Plantarflexión: rango típico 0-50°
            if angle < 10:
                return self.color_cache['white']
            elif angle < 25:
                return self.color_cache['yellow']
            elif angle < 40:
                return self.color_cache['orange']
            else:
                return self.color_cache['green']
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos actuales del análisis
        
        Returns:
            Dict con todos los datos relevantes del análisis
        """
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        return {
            # Campos ESTÁNDAR (compatibilidad con otros analyzers)
            'angle': round(self.current_angle, 1),
            'max_rom': round(self.max_angle, 1),
            'side': self.side,
            'orientation': self.orientation,
            'confidence': round(self.confidence, 2),
            'posture_valid': self.posture_valid,
            'landmarks_detected': self.landmarks_detected,
            'is_profile_position': self.is_profile_position,
            'orientation_quality': round(self.orientation_quality, 2),
            'fps': round(avg_fps, 1),
            'frame_count': self.frame_count,
            
            # Campos específicos de TOBILLO
            'current_angle': round(self.current_angle, 1),
            'raw_angle': round(self.raw_angle, 1),
            'max_dorsiflexion': round(self.max_dorsiflexion, 1),
            'max_plantarflexion': round(self.max_plantarflexion, 1),
            'movement_type': self.current_movement,
            
            # Campos adicionales
            'max_angle': round(self.max_angle, 1),
            'processing_time_ms': round(avg_processing, 1),
            'rom_max': round(self.max_angle, 1),
            'rom_min': 0.0,
            'analysis_type': 'ankle_profile',
            'segment': 'ankle',
            'joint_type': 'ankle',
            
            # Campos de compatibilidad con otros analyzers
            'is_hyperextension': False,
            'hyperextension_angle': 0.0
        }
    
    def reset(self):
        """Reinicia todas las estadísticas"""
        self.max_angle = 0.0
        self.max_dorsiflexion = 0.0
        self.max_plantarflexion = 0.0
        self.current_angle = 0.0
        self.raw_angle = 90.0
        self.current_movement = "neutral"
        self.fps_history.clear()
        self.processing_times.clear()
        self.frame_count = 0
        self.posture_valid = False
        self.landmarks_detected = False
        self.is_profile_position = False
        self.orientation_quality = 0.0
        logger.info("[AnkleProfileAnalyzer] Estadísticas reiniciadas")
    
    def cleanup(self):
        """Limpia recursos del analyzer"""
        logger.info("[AnkleProfileAnalyzer] Cleanup - pose compartido NO se cierra")
        # NO hacer self.pose.close() porque es singleton compartido
        pass
