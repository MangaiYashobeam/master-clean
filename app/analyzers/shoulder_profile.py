"""
💪 SHOULDER PROFILE ANALYZER - Análisis de Flexión/Extensión de Hombro
========================================================================
Analizador para vista de PERFIL (medición de flexión/extensión del hombro)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestión de estado interno (ángulos, ROM máximo)
- API pública para obtener datos actuales

Autor: BIOTRACK Team
Fecha: 2025-11-14
Basado en: tests/test_shoulder_profile.py
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


class ShoulderProfileAnalyzer:
    """
    Analizador de hombro en vista de PERFIL
    
    Mide:
    - Flexión (brazo hacia adelante/arriba)
    - Extensión (brazo hacia atrás)
    - ROM máximo alcanzado
    
    Uso en Flask:
        analyzer = ShoulderProfileAnalyzer()
        
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
    
    def calculate_extension_angle(
        self, 
        shoulder: Tuple[int, int], 
        elbow: Tuple[int, int], 
        side: str,
        orientation: str
    ) -> float:
        """
        Calcula el ángulo de flexión/extensión con eje vertical fijo
        
        Sistema goniómetro estándar:
        - Brazo FIJO: Eje vertical absoluto (0, 1)
        - Brazo MÓVIL: Línea del brazo (hombro → codo)
        - 0° = Brazo hacia abajo
        - +ángulo = Flexión (adelante/arriba)
        - -ángulo = Extensión (atrás)
        
        Lógica biomecánica:
        - FLEXIÓN: Codo se aleja del cuerpo hacia adelante
        - EXTENSIÓN: Codo va hacia atrás
        
        Args:
            shoulder: Coordenadas (x, y) del hombro
            elbow: Coordenadas (x, y) del codo
            side: 'left' o 'right'
            orientation: 'mirando derecha' o 'mirando izquierda'
        
        Returns:
            float: Ángulo en grados (positivo=flexión, negativo=extensión)
        """
        vertical_down_vector = np.array([0, 1])
        arm_vector = np.array([elbow[0] - shoulder[0], elbow[1] - shoulder[1]])
        
        arm_norm = np.linalg.norm(arm_vector)
        if arm_norm == 0:
            return 0.0
        
        arm_vector_normalized = arm_vector / arm_norm
        
        # Calcular ángulo
        dot_product = np.dot(vertical_down_vector, arm_vector_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle_magnitude = np.degrees(np.arccos(dot_product))
        
        # Determinar dirección según orientación de la persona
        # Producto cruz 2D: positivo si codo está a la derecha del hombro
        elbow_relative_x = elbow[0] - shoulder[0]
        
        # Lógica corregida considerando orientación
        if "mirando derecha" in orientation.lower():
            # Persona mirando derecha → Adelante es derecha (+x)
            # FLEXIÓN: codo hacia la derecha (+x) → ángulo positivo
            # EXTENSIÓN: codo hacia la izquierda (-x) → ángulo negativo
            angle = angle_magnitude if elbow_relative_x > 0 else -angle_magnitude
        else:
            # Persona mirando izquierda → Adelante es izquierda (-x)
            # FLEXIÓN: codo hacia la izquierda (-x) → ángulo positivo
            # EXTENSIÓN: codo hacia la derecha (+x) → ángulo negativo
            angle = angle_magnitude if elbow_relative_x < 0 else -angle_magnitude
        
        return float(angle)
    
    def detect_side(self, landmarks) -> Tuple[str, float, str]:
        """
        Detecta qué lado del cuerpo se está ANALIZANDO (vista de perfil)
        
        LÓGICA (considerando que la cámara ve como espejo):
        - La imagen de la webcam es como verte en un espejo
        - Si en la imagen la nariz está a la DERECHA del centro → 
          en realidad estás mirando a TU IZQUIERDA → lado DERECHO visible
        - Si en la imagen la nariz está a la IZQUIERDA del centro → 
          en realidad estás mirando a TU DERECHA → lado IZQUIERDO visible
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (lado, confianza, orientación)
                - lado: 'left' o 'right' (el lado del cuerpo visible hacia la cámara)
                - confianza: float (0-1)
                - orientación: str descripción de la orientación
        """
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        
        left_visibility = left_shoulder.visibility
        right_visibility = right_shoulder.visibility
        
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        
        # En la imagen (efecto espejo):
        # nose.x > center → en imagen miras a la derecha → en realidad miras a TU izquierda
        # nose.x < center → en imagen miras a la izquierda → en realidad miras a TU derecha
        if nose.x > shoulder_center_x:
            # En imagen: nariz a la derecha → Tú miras a TU izquierda
            # → Tu lado DERECHO está hacia la cámara
            side = 'right'
            orientation = "mirando izquierda"
            confidence = max(left_visibility, right_visibility)
        else:
            # En imagen: nariz a la izquierda → Tú miras a TU derecha
            # → Tu lado IZQUIERDO está hacia la cámara
            side = 'left'
            orientation = "mirando derecha"
            confidence = max(left_visibility, right_visibility)
        
        return side, float(confidence), orientation
    
    def verify_profile_position(self, landmarks) -> Tuple[bool, float, str]:
        """
        Verifica si la persona está REALMENTE en posición de perfil.
        
        Para estar en perfil:
        - Los hombros deben estar alineados (diferencia X pequeña)
        - Un hombro debe tener visibilidad significativamente mayor que el otro
        - Las caderas también deben estar alineadas
        
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
        # En perfil, un hombro debe ser mucho más visible que el otro
        visibility_diff = abs(left_shoulder.visibility - right_shoulder.visibility)
        
        # 2. Verificar alineación de hombros (en perfil, están casi en la misma X)
        shoulder_x_diff = abs(left_shoulder.x - right_shoulder.x)
        
        # 3. Verificar alineación de caderas
        hip_x_diff = abs(left_hip.x - right_hip.x)
        
        # Umbrales RELAJADOS para considerar perfil válido
        # En perfil real: hombros alineados verticalmente (diff X pequeña)
        SHOULDER_ALIGNMENT_THRESHOLD = 0.25  # Más permisivo (era 0.20)
        VISIBILITY_DIFF_THRESHOLD = 0.15     # Más permisivo (era 0.25)
        HIP_ALIGNMENT_THRESHOLD = 0.25       # Más permisivo (era 0.20)
        
        # Calcular scores individuales
        alignment_score = max(0, 1 - (shoulder_x_diff / SHOULDER_ALIGNMENT_THRESHOLD))
        visibility_score = min(1, visibility_diff / VISIBILITY_DIFF_THRESHOLD)
        hip_score = max(0, 1 - (hip_x_diff / HIP_ALIGNMENT_THRESHOLD))
        
        # Score total (promedio ponderado)
        quality = (alignment_score * 0.4 + visibility_score * 0.3 + hip_score * 0.3)
        
        # Determinar si está en perfil - CRITERIO SIMPLIFICADO
        # Solo verificamos alineación de hombros (el criterio más importante)
        is_profile = shoulder_x_diff < SHOULDER_ALIGNMENT_THRESHOLD
        
        # DEBUG: Log cada ~30 frames para ver valores
        if self.frame_count % 30 == 0:
            print(f"[PROFILE_CHECK] shoulder_x_diff={shoulder_x_diff:.3f} (threshold={SHOULDER_ALIGNMENT_THRESHOLD}), "
                  f"visibility_diff={visibility_diff:.3f}, is_profile={is_profile}, quality={quality:.2f}")
        
        # Generar mensaje descriptivo
        if is_profile:
            if quality > 0.8:
                message = "Perfil excelente"
            elif quality > 0.6:
                message = "Perfil correcto"
            else:
                message = "Perfil aceptable"
        else:
            if shoulder_x_diff >= SHOULDER_ALIGNMENT_THRESHOLD:
                message = "Gire más hacia un lado"
            elif visibility_diff <= VISIBILITY_DIFF_THRESHOLD * 0.5:
                message = "No se detecta perfil claro"
            else:
                message = "Ajuste su posición"
        
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
            self.landmarks_detected = True
            h, w = image.shape[:2]
            landmarks = results.pose_landmarks.landmark
            
            # Detectar lado visible
            side, detection_confidence, orientation = self.detect_side(landmarks)
            self.side = side  # 'left' o 'right' (compatible con frontend)
            
            # ⚡ NUEVO: Verificar si realmente está en posición de perfil
            is_profile, profile_quality, profile_message = self.verify_profile_position(landmarks)
            
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
            self.confidence = detection_confidence  # Solo confianza de que hay persona
            self.orientation_quality = profile_quality  # Calidad de perfil por separado
            
            # Dibujar skeleton solo si está habilitado
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
        """Procesa vista de perfil - Análisis de extensión/flexión"""
        # Seleccionar landmarks según el lado detectado
        if side == 'left':
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
            wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        else:
            shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
            elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
            wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        
        # Obtener coordenadas 2D
        shoulder_2d = self.get_landmarks_2d(shoulder, w, h)
        hip_2d = self.get_landmarks_2d(hip, w, h)
        elbow_2d = self.get_landmarks_2d(elbow, w, h)
        wrist_2d = self.get_landmarks_2d(wrist, w, h)
        
        # Calcular ángulo de extensión/flexión (pasando orientación)
        angle = self.calculate_extension_angle(shoulder_2d, elbow_2d, side, orientation)
        
        # Actualizar estadísticas
        self.current_angle = angle
        
        abs_angle = abs(angle)
        if abs_angle > self.max_angle:
            self.max_angle = abs_angle
        
        # Validar postura (simplificado - mejorar según necesidades)
        self.posture_valid = confidence > 0.6 and abs_angle < 200  # Ángulo razonable
        
        # Dibujar puntos clave
        cv2.circle(image, shoulder_2d, 8, self.color_cache['yellow'], -1, cv2.LINE_4)
        cv2.circle(image, hip_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4)
        cv2.circle(image, elbow_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4)
        
        # Línea de referencia vertical fija
        vertical_length = 150
        vertical_start = (shoulder_2d[0], shoulder_2d[1] - vertical_length)
        vertical_end = (shoulder_2d[0], shoulder_2d[1] + vertical_length)
        cv2.line(image, vertical_start, vertical_end, self.color_cache['green'], 3, cv2.LINE_4)
        
        # Línea del brazo
        cv2.line(image, shoulder_2d, elbow_2d, self.color_cache['blue'], 3, cv2.LINE_4)
        
        # Antebrazo
        cv2.line(image, elbow_2d, wrist_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Mostrar ángulo (usamos 'o' en lugar de '°' porque OpenCV no renderiza bien el símbolo)
        angle_text = f"{abs(angle):.1f}"
        direction_text = "FLEX" if angle > 0 else "EXT" if angle < 0 else ""
        
        # Dibujar el número del ángulo
        cv2.putText(
            image, 
            angle_text, 
            (shoulder_2d[0] - 40, shoulder_2d[1] - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.2, 
            self.color_cache['yellow'], 
            3, 
            cv2.LINE_4
        )
        # Dibujar 'o' pequeña como símbolo de grados (simulando superíndice)
        # Calculamos la posición después del número
        (text_width, _), _ = cv2.getTextSize(angle_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        cv2.putText(
            image,
            "o",
            (shoulder_2d[0] - 40 + text_width + 2, shoulder_2d[1] - 35),  # Posición elevada
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,  # Tamaño más pequeño
            self.color_cache['yellow'],
            2,
            cv2.LINE_4
        )
        
        if direction_text:
            direction_color = self.color_cache['green'] if angle > 0 else self.color_cache['orange']
            cv2.putText(
                image, 
                direction_text, 
                (shoulder_2d[0] - 30, shoulder_2d[1] + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                direction_color, 
                2, 
                cv2.LINE_4
            )
        
        # Panel de información en video (DESHABILITADO - info ya visible en panel web)
        # self._draw_info_panel(image, orientation, confidence, w, h)
    
    def _draw_info_panel(
        self, 
        image: np.ndarray, 
        orientation: str, 
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
            "FLEXION/EXTENSION DE HOMBRO (PERFIL)", 
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            self.color_cache['white'], 
            2, 
            cv2.LINE_4
        )
        
        # Lado detectado
        color_side = self.color_cache['green'] if confidence > 0.7 else self.color_cache['orange']
        cv2.putText(
            image, 
            f"Lado: {self.side}", 
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            color_side, 
            2, 
            cv2.LINE_4
        )
        
        # Orientación
        cv2.putText(
            image, 
            f"Orientacion: {orientation}", 
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            self.color_cache['white'], 
            1, 
            cv2.LINE_4
        )
        
        # Ángulo actual
        angle_color = self._get_angle_color(self.current_angle)
        direction_text = "FLEX" if self.current_angle > 0 else "EXT" if self.current_angle < 0 else ""
        cv2.putText(
            image, 
            f"Angulo: {abs(self.current_angle):.1f}deg {direction_text}", 
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            angle_color, 
            2, 
            cv2.LINE_4
        )
        
        # ROM Máximo
        cv2.putText(
            image, 
            f"ROM Max: {self.max_angle:.1f}deg", 
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            self.color_cache['green'], 
            2, 
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
        panel_y = 10
        
        # Fondo semitransparente
        overlay = image.copy()
        cv2.rectangle(
            overlay, 
            (panel_x - 10, panel_y), 
            (w - 10, panel_y + 80), 
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
    
    def _get_angle_color(self, angle: float) -> Tuple[int, int, int]:
        """Retorna color según el ángulo"""
        abs_angle = abs(angle)
        
        if abs_angle < 15:
            return self.color_cache['white']
        elif abs_angle < 45:
            return self.color_cache['yellow']
        elif abs_angle < 90:
            return self.color_cache['orange']
        elif abs_angle < 135:
            return self.color_cache['magenta']
        else:
            return self.color_cache['green']
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos actuales del análisis
        
        Returns:
            dict: Diccionario con datos actuales:
                - angle: Ángulo actual (float)
                - max_rom: ROM máximo alcanzado (float)
                - side: Lado detectado (str)
                - orientation: Orientación real verificada (str) - 'profile' o 'frontal'
                - confidence: Confianza combinada (detección + calidad posición) (float)
                - posture_valid: Si la postura es válida para análisis (bool)
                - landmarks_detected: Si se detectaron landmarks (bool)
                - is_profile_position: Si está realmente en posición de perfil (bool)
                - orientation_quality: Calidad de la orientación 0-1 (float)
                - fps: FPS actual (float)
        """
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        return {
            'angle': round(self.current_angle, 2),
            'max_rom': round(self.max_angle, 2),
            'side': self.side,
            'orientation': self.orientation,  # Ahora es 'profile' o 'frontal' verificado
            'confidence': round(self.confidence, 2),
            'posture_valid': self.posture_valid,
            'landmarks_detected': self.landmarks_detected,
            'is_profile_position': self.is_profile_position,
            'orientation_quality': round(self.orientation_quality, 2),
            'fps': round(avg_fps, 1),
            'frame_count': self.frame_count
        }
    
    def reset(self):
        """
        Reinicia todas las estadísticas (ROM, ángulos, etc.)
        
        Útil para iniciar una nueva sesión de medición sin recrear el analyzer
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
