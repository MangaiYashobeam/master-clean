"""
🦵 KNEE PROFILE ANALYZER - Análisis de Flexión/Extensión de Rodilla
=====================================================================
Analizador para vista de PERFIL (medición de flexión/extensión de rodilla)

ADAPTADO PARA FLASK:
- Sin cv2.imshow() ni cv2.waitKey()
- Solo procesa frames y retorna frame anotado
- Gestión de estado interno (ángulos, ROM máximo)
- API pública para obtener datos actuales

SISTEMA DE MEDICIÓN:
- Eje FIJO: Vertical absoluto (0, 1) que pasa por la RODILLA
- Brazo MÓVIL: Línea de la pierna (RODILLA → TOBILLO)
- 0° = Pierna extendida (vertical hacia abajo)
- 135-150° = Flexión máxima (talón toca glúteo)

Landmarks utilizados:
- Cadera: LEFT_HIP (23), RIGHT_HIP (24)
- Rodilla: LEFT_KNEE (25), RIGHT_KNEE (26)
- Tobillo: LEFT_ANKLE (27), RIGHT_ANKLE (28)

Autor: BIOTRACK Team
Fecha: 2025-12-07
Basado en: ElbowProfileAnalyzer (estructura) y tests/test_knee_profile.py (lógica)
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


class KneeProfileAnalyzer:
    """
    Analizador de rodilla en vista de PERFIL
    
    Mide:
    - Flexión (pierna doblada, talón hacia glúteo)
    - Extensión (pierna recta)
    - ROM máximo alcanzado
    
    Uso en Flask:
        analyzer = KneeProfileAnalyzer()
        
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
        
        logger.info("[KneeProfileAnalyzer] Inicializado con pose singleton compartido")
    
    def calculate_knee_angle(
        self, 
        hip: Tuple[int, int], 
        knee: Tuple[int, int], 
        ankle: Tuple[int, int],
        orientation: str = ""
    ) -> float:
        """
        Calcula el ángulo de flexión/extensión de rodilla con eje vertical fijo
        
        Sistema goniómetro estándar (según bibliografía AAOS/AMA):
        - Brazo FIJO: Eje vertical absoluto (0, 1) que pasa por la RODILLA
        - Brazo MÓVIL: Línea de la pierna (RODILLA → TOBILLO)
        - 0° = Pierna completamente extendida (vertical hacia abajo)
        - 90° = Rodilla en ángulo recto
        - 135-150° = Flexión máxima (talón cerca del glúteo)
        
        NOTA: A diferencia del codo, la rodilla NO tiene hiperextensión significativa
        en personas sanas. Un ángulo de 0° o ligeramente negativo indica extensión
        completa (normal).
        
        Args:
            hip: Coordenadas (x, y) de la cadera (referencia visual)
            knee: Coordenadas (x, y) de la rodilla (VÉRTICE del ángulo)
            ankle: Coordenadas (x, y) del tobillo
            orientation: Orientación de la persona ('mirando izquierda' o 'mirando derecha')
        
        Returns:
            float: Ángulo en grados (0° a 150°)
        """
        # Vector vertical fijo (referencia 0° - apunta hacia abajo)
        vertical_down_vector = np.array([0, 1])
        
        # Vector de la pierna (RODILLA → TOBILLO) - brazo móvil del goniómetro
        leg_vector = np.array([ankle[0] - knee[0], ankle[1] - knee[1]])
        
        # Normalizar vector de la pierna
        leg_norm = np.linalg.norm(leg_vector)
        
        if leg_norm == 0:
            return 0.0
        
        leg_vector_normalized = leg_vector / leg_norm
        
        # Calcular ángulo entre eje vertical y pierna (magnitud)
        dot_product = np.dot(vertical_down_vector, leg_vector_normalized)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle = np.degrees(np.arccos(dot_product))
        
        # La rodilla normalmente NO tiene hiperextensión significativa
        # Un ángulo pequeño (<5°) se considera extensión completa
        # No retornamos valores negativos como en el codo
        
        return float(angle)
    
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
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        
        # Profundidad promedio (más cerca = más negativo en Z)
        left_depth = (left_hip.z + left_knee.z) / 2
        right_depth = (right_hip.z + right_knee.z) / 2
        
        # Visibilidad promedio
        left_vis = (left_hip.visibility + left_knee.visibility) / 2
        right_vis = (right_hip.visibility + right_knee.visibility) / 2
        
        # Score combinado (profundidad 70%, visibilidad 30%)
        left_score = (-left_depth * 0.7) + (left_vis * 0.3)
        right_score = (-right_depth * 0.7) + (right_vis * 0.3)
        
        # ⚡ CONFIANZA DE DETECCIÓN DE PERSONA (no de orientación)
        # Se basa en la visibilidad promedio de los landmarks clave
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        
        avg_visibility = (left_hip.visibility + right_hip.visibility + 
                         left_knee.visibility + right_knee.visibility + 
                         left_ankle.visibility + right_ankle.visibility +
                         nose.visibility) / 7
        detection_confidence = min(avg_visibility * 1.2, 1.0)  # Escalar ligeramente
        
        hip_center_x = (left_hip.x + right_hip.x) / 2
        
        if left_score > right_score:
            side = 'left'
            orientation = "mirando izquierda" if nose.x < hip_center_x else "mirando derecha"
        else:
            side = 'right'
            orientation = "mirando derecha" if nose.x > hip_center_x else "mirando izquierda"
        
        return side, detection_confidence, orientation
    
    def verify_profile_position(self, landmarks) -> Tuple[bool, float, str]:
        """
        Verifica si la persona está REALMENTE en posición de perfil.
        
        Para estar en perfil:
        - Las caderas deben estar alineadas (diferencia X pequeña)
        - Los hombros deben estar alineados (diferencia X pequeña)
        - Una cadera debe tener visibilidad significativamente mayor que la otra
        
        Args:
            landmarks: Lista de landmarks de MediaPipe
        
        Returns:
            tuple: (is_profile, quality, message)
                - is_profile: True si está en perfil válido
                - quality: float (0-1) calidad de la posición
                - message: Mensaje descriptivo
        """
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # 1. Verificar diferencia de visibilidad entre caderas
        visibility_diff = abs(left_hip.visibility - right_hip.visibility)
        
        # 2. Verificar alineación de caderas (en perfil, están casi en la misma X)
        hip_x_diff = abs(left_hip.x - right_hip.x)
        
        # 3. Verificar alineación de hombros (complementario)
        shoulder_x_diff = abs(left_shoulder.x - right_shoulder.x)
        
        # ⚠️ UMBRALES MUY ESTRICTOS para perfil de RODILLA
        # Problema: Cuando está lejos, las caderas se ven más juntas aunque esté de frente
        # Solución: Umbrales más bajos que HipProfileAnalyzer
        HIP_ALIGNMENT_THRESHOLD = 0.08       # Muy estricto - caderas casi superpuestas
        VISIBILITY_DIFF_THRESHOLD = 0.25     # Una cadera debe ser claramente más visible
        SHOULDER_ALIGNMENT_THRESHOLD = 0.08  # Muy estricto - hombros casi superpuestos
        
        # Calcular scores individuales
        hip_alignment_score = max(0, 1 - (hip_x_diff / HIP_ALIGNMENT_THRESHOLD))
        visibility_score = min(1, visibility_diff / VISIBILITY_DIFF_THRESHOLD)
        shoulder_score = max(0, 1 - (shoulder_x_diff / SHOULDER_ALIGNMENT_THRESHOLD))
        
        # Score total (promedio ponderado - caderas más importantes para rodilla)
        quality = (hip_alignment_score * 0.4 + visibility_score * 0.3 + shoulder_score * 0.3)
        
        # ⚠️ IMPORTANTE: Para ser perfil, AMBOS deben estar alineados (hombros Y caderas)
        # Y además necesitamos un mínimo de calidad
        is_profile = (hip_x_diff < HIP_ALIGNMENT_THRESHOLD and 
                      shoulder_x_diff < SHOULDER_ALIGNMENT_THRESHOLD and
                      quality > 0.4)  # Requiere calidad mínima
        
        # DEBUG: Log cada ~30 frames para ver valores reales
        if self.frame_count % 30 == 0:
            logger.info(f"[KNEE_PROFILE_CHECK] shoulder_x={shoulder_x_diff:.3f} (th={SHOULDER_ALIGNMENT_THRESHOLD}), "
                       f"hip_x={hip_x_diff:.3f} (th={HIP_ALIGNMENT_THRESHOLD}), "
                       f"is_profile={is_profile}, quality={quality:.2f}")
        
        # Generar mensaje descriptivo
        if is_profile:
            if quality > 0.8:
                message = "Perfil excelente"
            elif quality > 0.6:
                message = "Perfil correcto"
            else:
                message = "Perfil aceptable"
        else:
            message = "Gire más hacia un lado"
        
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
            
            # ⚡ Verificar si realmente está en posición de perfil
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
        Procesa vista de perfil - Análisis de flexión/extensión de rodilla
        
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
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            side_display = "IZQUIERDA"  # Para mostrar en pantalla
        else:
            hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
            side_display = "DERECHA"  # Para mostrar en pantalla
        
        # IMPORTANTE: self.side debe ser 'left' o 'right' para compatibilidad con DB
        self.side = side  # Mantener 'left'/'right' para el sistema
        
        # Obtener coordenadas 2D
        hip_2d = self.get_landmarks_2d(hip, w, h)
        knee_2d = self.get_landmarks_2d(knee, w, h)
        ankle_2d = self.get_landmarks_2d(ankle, w, h)
        
        # Calcular ángulo de flexión de rodilla
        angle = self.calculate_knee_angle(hip_2d, knee_2d, ankle_2d, orientation)
        
        # Actualizar estadísticas
        self.current_angle = angle
        
        # Para ROM máximo
        if angle > self.max_angle:
            self.max_angle = angle
        
        # ===== VISUALIZACIÓN =====
        
        # Dibujar puntos clave
        cv2.circle(image, knee_2d, 12, self.color_cache['yellow'], -1, cv2.LINE_4)  # RODILLA (vértice)
        cv2.circle(image, hip_2d, 8, self.color_cache['magenta'], -1, cv2.LINE_4)   # CADERA
        cv2.circle(image, ankle_2d, 8, self.color_cache['cyan'], -1, cv2.LINE_4)    # TOBILLO
        
        # Borde negro para mayor visibilidad
        cv2.circle(image, knee_2d, 14, (0, 0, 0), 2, cv2.LINE_4)
        
        # Línea de referencia vertical fija que pasa por la RODILLA
        vertical_length = 150
        vertical_start = (knee_2d[0], knee_2d[1] - vertical_length)
        vertical_end = (knee_2d[0], knee_2d[1] + vertical_length)
        cv2.line(image, vertical_start, vertical_end, self.color_cache['green'], 3, cv2.LINE_4)
        
        # Etiqueta del eje vertical (0°)
        cv2.putText(
            image, "0", 
            (knee_2d[0] + 10, knee_2d[1] + vertical_length - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color_cache['green'], 1, cv2.LINE_4
        )
        cv2.putText(
            image, "o", 
            (knee_2d[0] + 22, knee_2d[1] + vertical_length - 18),  # Posición elevada (superíndice)
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, self.color_cache['green'], 1, cv2.LINE_4
        )
        
        # Línea de la pierna (RODILLA → TOBILLO) - brazo móvil del goniómetro
        leg_color = self._get_angle_color(angle)
        cv2.line(image, knee_2d, ankle_2d, leg_color, 4, cv2.LINE_4)
        
        # Muslo (CADERA → RODILLA) - referencia visual
        cv2.line(image, hip_2d, knee_2d, self.color_cache['blue'], 2, cv2.LINE_4)
        
        # Dibujar arco del ángulo
        self._draw_angle_arc(image, knee_2d, angle)
        
        # Mostrar ángulo junto a la rodilla
        angle_num = f"{angle:.1f}"
        text_pos = (knee_2d[0] + 20, knee_2d[1] - 30)
        
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
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, leg_color, 2, cv2.LINE_4
        )
        # Símbolo 'o' superíndice
        cv2.putText(
            image, "o", (text_pos[0] + text_w + 2, text_pos[1] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, leg_color, 1, cv2.LINE_4
        )
    
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
            center: Centro del arco (posición de la rodilla)
            angle: Ángulo a representar
            radius: Radio del arco
        """
        # El arco va desde la vertical (90° en coordenadas OpenCV) hacia la pierna
        # En OpenCV, 0° es hacia la derecha, 90° hacia abajo
        start_angle = 90  # Vertical hacia abajo
        end_angle = 90 - angle  # Hacia donde apunta la pierna
        
        if angle != 0:
            color = self._get_angle_color(angle)
            cv2.ellipse(
                image, center, (radius, radius),
                0, min(start_angle, end_angle), max(start_angle, end_angle),
                color, 2, cv2.LINE_4
            )
    
    def _get_angle_color(self, angle: float) -> Tuple[int, int, int]:
        """
        Retorna color según el ángulo de flexión de rodilla
        
        Args:
            angle: Ángulo en grados
        
        Returns:
            tuple: Color BGR
        """
        if angle < 15:
            return self.color_cache['white']   # Extensión casi completa
        elif angle < 45:
            return self.color_cache['yellow']  # Flexión leve
        elif angle < 90:
            return self.color_cache['orange']  # Flexión moderada
        elif angle < 120:
            return self.color_cache['magenta'] # Flexión significativa
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
        # Para rodilla: <15° es extensión, >15° es flexión
        if self.current_angle < 15:
            movement = 'extension'   # Pierna casi extendida
        else:
            movement = 'flexion'     # Flexión
        
        return {
            # Campos ESTÁNDAR (compatibles con todos los analyzers)
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
            # Campos adicionales
            'current_angle': round(self.current_angle, 1),
            'max_angle': round(self.max_angle, 1),
            'processing_time_ms': round(avg_processing, 1),
            'rom_max': round(self.max_angle, 1),
            'rom_min': 0.0,
            'analysis_type': 'knee_profile',
            'movement_type': movement,
            'segment': 'knee',
            'joint_type': 'knee_profile',
            # Campos específicos (compatibilidad con elbow)
            'is_hyperextension': False,  # Rodilla normalmente no tiene hiperextensión significativa
            'hyperextension_angle': 0.0
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
        logger.info("[KneeProfileAnalyzer] Estadísticas reiniciadas")
    
    def cleanup(self):
        """
        Limpia recursos del analyzer
        
        NOTA: NO cerrar el pose porque es compartido (singleton)
        """
        logger.info("[KneeProfileAnalyzer] Cleanup - pose compartido NO se cierra")
        # NO hacer self.pose.close() porque es singleton compartido
        pass
