"""
Módulo de sesión de análisis ROM.
Implementa la máquina de estados para el flujo controlado de análisis.

Estados:
- IDLE: Sin sesión activa
- DETECTING_PERSON: Buscando persona en el frame
- CHECKING_ORIENTATION: Verificando orientación (frontal/perfil)
- CHECKING_POSTURE: Verificando postura adecuada
- COUNTDOWN: Cuenta regresiva antes de análisis
- ANALYZING: Capturando mediciones ROM
- COMPLETED: Análisis completado

NO crea hilos adicionales. Usa singletons existentes.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, Callable
from datetime import datetime
import time
import numpy as np
import logging

# Logger para este módulo
logger = logging.getLogger(__name__)

# Usar singletons existentes
from app.core.pose_singleton import get_shared_pose
from app.utils.rom_statistics import ROMStatisticsCalculator

# Servicio TTS (singleton) para guía de voz
from app.services.tts_service import get_tts_service, TTSMessages


class AnalysisState(Enum):
    """Estados de la sesión de análisis."""
    IDLE = auto()
    DETECTING_PERSON = auto()
    CHECKING_ORIENTATION = auto()
    CHECKING_POSTURE = auto()
    COUNTDOWN = auto()
    ANALYZING = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class StateTransition:
    """Representa una transición de estado."""
    from_state: AnalysisState
    to_state: AnalysisState
    timestamp: float = field(default_factory=time.time)
    reason: str = ""


@dataclass
class AnalysisResult:
    """Resultado final del análisis ROM."""
    joint_type: str
    movement_type: str
    orientation: str  # 'frontal' o 'profile'
    side: str  # 'left', 'right', o 'bilateral' - lado analizado
    
    # Valores ROM
    rom_value: float
    rom_percentile_95: float
    rom_quality: float  # 0.0 - 1.0
    
    # Clasificación
    classification: str  # 'NORMAL', 'LIMITADO', etc.
    normal_range: Tuple[float, float]
    
    # Metadatos
    session_duration: float
    analysis_duration: float
    samples_collected: int
    plateau_detected: bool
    
    # Datos bilaterales (solo para frontal)
    left_max_rom: Optional[float] = None
    right_max_rom: Optional[float] = None
    is_bilateral: bool = False
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        result = {
            'joint_type': self.joint_type,
            'movement_type': self.movement_type,
            'orientation': self.orientation,
            'side': self.side,  # Lado analizado: 'left', 'right', o 'bilateral'
            'rom_value': round(self.rom_value, 1),
            'rom_percentile_95': round(self.rom_percentile_95, 1),
            'max_rom': round(self.rom_percentile_95, 1),  # Alias para frontend
            'rom_quality': round(self.rom_quality, 2),
            'classification': self.classification,
            'normal_range': self.normal_range,
            'session_duration': round(self.session_duration, 2),
            'analysis_duration': round(self.analysis_duration, 2),
            'samples_collected': self.samples_collected,
            'plateau_detected': self.plateau_detected,
            'timestamp': self.timestamp.isoformat(),
            'is_bilateral': self.is_bilateral
        }
        
        # Agregar datos bilaterales si existen
        if self.is_bilateral:
            result['left_max_rom'] = round(self.left_max_rom, 1) if self.left_max_rom is not None else None
            result['right_max_rom'] = round(self.right_max_rom, 1) if self.right_max_rom is not None else None
        
        # =====================================================================
        # VERIFICACIÓN DE MEDICIÓN SOSPECHOSA
        # Advierte al usuario si la medición parece ser un error
        # =====================================================================
        from app.utils.rom_standards import is_suspicious_measurement
        
        suspicious_check = is_suspicious_measurement(
            segment=self.joint_type,
            exercise=self.movement_type,
            angle=self.rom_percentile_95
        )
        
        result['is_suspicious'] = suspicious_check.get('is_suspicious', False)
        if suspicious_check.get('is_suspicious'):
            result['suspicious_reason'] = suspicious_check.get('reason')
            result['suspicious_recommendation'] = suspicious_check.get('recommendation')
            result['suspicious_severity'] = suspicious_check.get('severity')  # 'warning' o 'error'
            result['suspicious_expected_range'] = suspicious_check.get('expected_range')
        
        return result


class AnalysisSession:
    """
    Controlador de sesión de análisis ROM.
    
    Implementa máquina de estados para flujo controlado:
    IDLE → DETECTING → ORIENTATION → POSTURE → COUNTDOWN → ANALYZING → COMPLETED
    
    NO crea hilos adicionales. Usa los singletons:
    - get_shared_pose() para MediaPipe
    - get_person_detector() para detección de persona
    - get_posture_verifier() para verificación de postura
    """
    
    # Configuración de tiempos
    COUNTDOWN_DURATION = 3.0  # Segundos de cuenta regresiva
    ANALYSIS_DURATION = 10.0  # Segundos de captura ROM (antes 5s, ahora 10s)
    MIN_SAMPLES_REQUIRED = 15  # Mínimo de muestras para resultado válido
    
    # Tiempos mínimos por estado (para dar feedback visual al usuario)
    # IMPORTANTE: Estos tiempos aseguran que el usuario tenga tiempo de posicionarse
    MIN_DETECTING_TIME = 2.0   # Mínimo 2 segundos buscando persona (para confirmar detección estable)
    MIN_ORIENTATION_TIME = 2.0  # Mínimo 2 segundos verificando orientación (debe mantenerse)
    MIN_POSTURE_TIME = 1.5     # Mínimo 1.5 segundos verificando postura
    
    # Umbrales de confianza
    MIN_CONFIDENCE = 0.6       # Confianza mínima para considerar detección válida
    
    # Configuración de reintentos
    MAX_DETECTION_RETRIES = 3
    POSTURE_TIMEOUT = 10.0  # Segundos máximos esperando postura correcta
    
    def __init__(
        self,
        joint_type: str,
        movement_type: str,
        required_orientation: str = "profile"
    ):
        """
        Inicializa una sesión de análisis.
        
        Args:
            joint_type: Tipo de articulación ('shoulder', 'elbow', 'knee', etc.)
            movement_type: Tipo de movimiento ('flexion', 'extension', etc.)
            required_orientation: Orientación requerida ('frontal' o 'profile')
        """
        self.joint_type = joint_type
        self.movement_type = movement_type
        self.required_orientation = required_orientation
        
        # Estado actual
        self._state = AnalysisState.IDLE
        self._state_message = "Sesión no iniciada"
        self._state_progress = 0.0  # 0.0 - 1.0
        
        # Historial de transiciones
        self._transitions: list[StateTransition] = []
        
        # Tiempos
        self._session_start_time: Optional[float] = None
        self._state_start_time: Optional[float] = None
        self._analysis_start_time: Optional[float] = None
        
        # Calculadora de estadísticas ROM (usa config por defecto)
        self._rom_calculator = ROMStatisticsCalculator()
        
        # Calculadores bilaterales para análisis frontal (percentil 95 por lado)
        self._left_rom_calculator = ROMStatisticsCalculator()
        self._right_rom_calculator = ROMStatisticsCalculator()
        
        # Resultado
        self._result: Optional[AnalysisResult] = None
        
        # Contadores
        self._detection_retries = 0
        self._last_angle: Optional[float] = None
        
        # Datos bilaterales (para frontal)
        self._left_max_rom: float = 0.0
        self._right_max_rom: float = 0.0
        self._is_bilateral: bool = (required_orientation.lower() == 'frontal')
        
        # Lado detectado (para perfil: 'left' o 'right', para frontal: 'bilateral')
        self._detected_side: str = 'bilateral' if self._is_bilateral else 'right'
        
        # Contadores de frames consecutivos exitosos (para verificar estabilidad)
        self._consecutive_detections = 0
        self._consecutive_orientation_ok = 0
        self._consecutive_posture_ok = 0
        self._last_confidence: float = 0.0
        
        # 🔊 TTS: Tracking del último countdown hablado (para no repetir)
        self._last_spoken_countdown: int = 0
        
        # 🔊 TTS: Control de repetición de mensajes
        self._last_detection_reminder: float = 0.0  # Tiempo del último recordatorio
        self._detection_reminder_interval: float = 5.0  # Repetir cada 5 segundos
        
        # 🔊 TTS: Control de instrucción pre-ejercicio
        self._instruction_spoken: bool = False  # Ya se dijo la instrucción
        self._instruction_start_time: float = 0.0  # Cuándo se dijo
        self._instruction_wait_time: float = 3.0  # Esperar 3 segundos después de instrucción
        self._countdown_start_time: Optional[float] = None  # Cuándo empezó el countdown real
        self._countdown_phase: str = 'instruction'  # 'instruction', 'waiting', 'counting'
        self._current_countdown_value: int = 3  # Valor visual actual del countdown
        
        # 🦵 Modo bilateral secuencial: Suprimir TTS hasta resultado final
        self.suppress_tts_result: bool = False
        
        # Callbacks (opcionales)
        self._on_state_change: Optional[Callable[[AnalysisState, str], None]] = None
        self._on_countdown: Optional[Callable[[int], None]] = None
        self._on_progress: Optional[Callable[[float], None]] = None
    
    @property
    def state(self) -> AnalysisState:
        """Estado actual de la sesión."""
        return self._state
    
    @property
    def state_message(self) -> str:
        """Mensaje descriptivo del estado actual."""
        return self._state_message
    
    @property
    def state_progress(self) -> float:
        """Progreso del estado actual (0.0 - 1.0)."""
        return self._state_progress
    
    @property
    def result(self) -> Optional[AnalysisResult]:
        """Resultado del análisis (None si no completado)."""
        return self._result
    
    @property
    def is_active(self) -> bool:
        """Indica si hay una sesión activa."""
        return self._state not in (AnalysisState.IDLE, AnalysisState.COMPLETED, AnalysisState.ERROR)
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable[[AnalysisState, str], None]] = None,
        on_countdown: Optional[Callable[[int], None]] = None,
        on_progress: Optional[Callable[[float], None]] = None
    ):
        """Configura callbacks opcionales para eventos."""
        self._on_state_change = on_state_change
        self._on_countdown = on_countdown
        self._on_progress = on_progress
    
    def update_bilateral_data(self, left_angle: float, right_angle: float):
        """
        Actualiza los datos de ROM bilateral (para análisis frontal).
        Ahora usa calculadores de estadísticas para percentil 95.
        
        Args:
            left_angle: Ángulo ACTUAL del lado izquierdo (no el máximo)
            right_angle: Ángulo ACTUAL del lado derecho (no el máximo)
        """
        self._is_bilateral = True
        
        # Agregar a calculadores de estadísticas (para percentil 95)
        if left_angle > 0:
            self._left_rom_calculator.add_measurement(left_angle)
        if right_angle > 0:
            self._right_rom_calculator.add_measurement(right_angle)
        
        # Mantener tracking del máximo instantáneo (para display en tiempo real)
        if left_angle > self._left_max_rom:
            self._left_max_rom = left_angle
        if right_angle > self._right_max_rom:
            self._right_max_rom = right_angle
    
    def _transition_to(self, new_state: AnalysisState, reason: str = ""):
        """
        Realiza una transición de estado.
        
        Args:
            new_state: Nuevo estado
            reason: Razón de la transición
        """
        old_state = self._state
        
        # ⚡ LOG de transición
        logger.info(f"⚡ TRANSICIÓN: {old_state.name} → {new_state.name} | Razón: {reason}")
        
        # Registrar transición
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            reason=reason
        )
        self._transitions.append(transition)
        
        # Actualizar estado
        self._state = new_state
        self._state_start_time = time.time()
        self._state_progress = 0.0
        
        # Reset de variables de countdown cuando se entra al estado COUNTDOWN
        if new_state == AnalysisState.COUNTDOWN:
            self._countdown_phase = 'instruction'
            self._instruction_spoken = False
            self._countdown_start_time = None
            self._last_spoken_countdown = 4  # 4 = "ninguno dicho aún", forzará decir "3" primero
            self._current_countdown_value = 3  # Visual siempre empieza en 3
        
        # Actualizar mensaje según estado
        self._update_state_message()
        
        # 🔊 Reproducir mensaje de voz para el nuevo estado
        self._speak_state_message(new_state, reason)
        
        # Callback
        if self._on_state_change:
            self._on_state_change(new_state, self._state_message)
    
    def _speak_state_message(self, state: AnalysisState, reason: str = ""):
        """
        Reproduce el mensaje de voz correspondiente al estado.
        
        Args:
            state: Estado actual
            reason: Razón de la transición (puede afectar el mensaje)
        """
        print(f"\n[ANALYSIS_SESSION] _speak_state_message llamado para estado: {state.name}")
        try:
            print(f"[ANALYSIS_SESSION] Obteniendo TTS service...")
            tts = get_tts_service()
            print(f"[ANALYSIS_SESSION] TTS service obtenido: {tts}")
            
            if state == AnalysisState.DETECTING_PERSON:
                print(f"[ANALYSIS_SESSION] Hablando: DETECTING_PERSON -> {TTSMessages.DETECTING_PERSON}")
                tts.speak(TTSMessages.DETECTING_PERSON)
            
            elif state == AnalysisState.CHECKING_ORIENTATION:
                if self.required_orientation == 'profile':
                    tts.speak(TTSMessages.ORIENTATION_PROFILE)
                else:
                    tts.speak(TTSMessages.ORIENTATION_FRONTAL)
            
            elif state == AnalysisState.CHECKING_POSTURE:
                tts.speak(TTSMessages.CHECKING_POSTURE)
            
            elif state == AnalysisState.ANALYZING:
                tts.speak(TTSMessages.ANALYZING_START)
            
            elif state == AnalysisState.COMPLETED:
                # 1. Primero decir "puedes relajarte"
                tts.speak(TTSMessages.COMPLETED_RELAX)
                
                # Debug para ver el resultado
                print(f"\n🔊 [COMPLETED] self._result = {self._result}")
                if self._result:
                    print(f"🔊 [COMPLETED] is_bilateral={self._result.is_bilateral}, left={self._result.left_max_rom}, right={self._result.right_max_rom}")
                
                # 2. Luego decir el resultado (después de un breve delay implícito por la cola)
                if self._result:
                    rom_value = self._result.rom_percentile_95
                    classification = self._result.classification
                    
                    # Para bilateral, pasar ambos valores
                    if self._result.is_bilateral:
                        self._speak_result(
                            rom_value, 
                            classification,
                            left_rom=self._result.left_max_rom,
                            right_rom=self._result.right_max_rom
                        )
                    else:
                        self._speak_result(rom_value, classification)
                else:
                    print(f"🔊 [COMPLETED] ⚠️ NO HAY RESULTADO!")
            
            elif state == AnalysisState.IDLE:
                # Al volver a IDLE (detener), cancelar cualquier mensaje
                tts.stop_current()
            
            elif state == AnalysisState.ERROR:
                tts.speak(TTSMessages.error_message('generic'))
                
        except Exception as e:
            logger.warning(f"[TTS] Error reproduciendo mensaje: {e}")
    
    def _speak_countdown(self, value: int):
        """
        Reproduce el número del countdown (pre-generado con rate +30%).
        
        Args:
            value: Valor del countdown (3, 2, 1)
        """
        try:
            tts = get_tts_service()
            
            if value == 3:
                tts.speak(TTSMessages.COUNTDOWN_3)
            elif value == 2:
                tts.speak(TTSMessages.COUNTDOWN_2)
            elif value == 1:
                tts.speak(TTSMessages.COUNTDOWN_1)
                
        except Exception as e:
            logger.warning(f"[TTS] Error en countdown: {e}")
    
    def _speak_result(self, rom_value: float, classification: str, left_rom: float = None, right_rom: float = None):
        """
        Reproduce el mensaje de resultado.
        
        Args:
            rom_value: Valor ROM en grados
            classification: Clasificación del resultado
            left_rom: ROM del lado izquierdo (para bilateral)
            right_rom: ROM del lado derecho (para bilateral)
        """
        try:
            # 🦵 Si estamos en modo bilateral secuencial y suppress_tts_result está activo,
            # no hablar el resultado (el frontend lo hablará al combinar ambas piernas)
            if self.suppress_tts_result:
                print(f"🔊 [_speak_result] SUPRIMIDO - modo bilateral secuencial")
                return
            
            tts = get_tts_service()
            
            # Debug para ver qué valores llegan
            print(f"\n🔊 [_speak_result] rom={rom_value}, class={classification}, left={left_rom}, right={right_rom}, bilateral={self._is_bilateral}")
            
            # Para bilateral, decir ambos valores
            if left_rom is not None and right_rom is not None:
                message = TTSMessages.completed_result(
                    rom_value, 
                    classification,
                    left_rom=left_rom,
                    right_rom=right_rom
                )
                print(f"🔊 [_speak_result] Mensaje bilateral: {message}")
            else:
                message = TTSMessages.completed_result(rom_value, classification)
                print(f"🔊 [_speak_result] Mensaje unilateral: {message}")
            
            tts.speak(message)
        except Exception as e:
            logger.warning(f"[TTS] Error en resultado: {e}")
            print(f"🔊 [_speak_result] ERROR: {e}")
    
    def _speak_plateau(self):
        """Reproduce mensaje cuando se detecta plateau."""
        try:
            tts = get_tts_service()
            tts.speak(TTSMessages.ANALYZING_HOLD)
        except Exception as e:
            logger.warning(f"[TTS] Error en plateau: {e}")
    
    def _update_state_message(self):
        """Actualiza el mensaje según el estado actual."""
        messages = {
            AnalysisState.IDLE: "Sesión no iniciada",
            AnalysisState.DETECTING_PERSON: "Buscando persona...",
            AnalysisState.CHECKING_ORIENTATION: f"Posiciónese de {self.required_orientation}",
            AnalysisState.CHECKING_POSTURE: "Ajuste su postura",
            AnalysisState.COUNTDOWN: "Comenzamos en...",
            AnalysisState.ANALYZING: "Capturando movimiento...",
            AnalysisState.COMPLETED: "Análisis completado",
            AnalysisState.ERROR: "Error en el análisis"
        }
        self._state_message = messages.get(self._state, "Estado desconocido")
    
    def start(self) -> bool:
        """
        Inicia la sesión de análisis.
        
        Returns:
            True si se inició correctamente
        """
        if self._state != AnalysisState.IDLE:
            return False
        
        self._session_start_time = time.time()
        self._detection_retries = 0
        self._rom_calculator.reset()
        self._result = None
        
        self._transition_to(AnalysisState.DETECTING_PERSON, "Sesión iniciada")
        return True
    
    def stop(self) -> Dict[str, Any]:
        """
        Detiene la sesión actual.
        
        Returns:
            Diccionario con información del estado final
        """
        final_state = self._state
        
        if self._state == AnalysisState.ANALYZING:
            # Si estábamos analizando, intentar generar resultado parcial
            self._try_generate_partial_result()
        
        self._transition_to(AnalysisState.IDLE, "Sesión detenida por usuario")
        
        return {
            'stopped_from_state': final_state.name,
            'session_duration': time.time() - self._session_start_time if self._session_start_time else 0,
            'result': self._result.to_dict() if self._result else None
        }
    
    def process_frame(
        self,
        landmarks: Any,
        current_angle: Optional[float] = None,
        detected_orientation: Optional[str] = None,
        confidence: float = 0.0,
        side: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un frame y avanza la máquina de estados.
        
        Este método debe ser llamado por cada frame capturado.
        NO crea hilos - es síncrono y debe ser llamado desde el loop principal.
        
        Args:
            landmarks: Landmarks de MediaPipe (True/False o objeto)
            current_angle: Ángulo actual medido (si aplica)
            detected_orientation: Orientación detectada ('frontal' o 'profile')
            confidence: Confianza de la detección (0.0 - 1.0)
            side: Lado detectado ('left', 'right', o 'bilateral')
        
        Returns:
            Diccionario con estado actual y datos relevantes
        """
        # Guardar confianza
        self._last_confidence = confidence
        
        # Actualizar lado detectado (si se proporciona y es válido)
        if side and side in ('left', 'right', 'bilateral'):
            self._detected_side = side
        
        result = {
            'state': self._state.name,
            'message': self._state_message,
            'progress': self._state_progress,
            'can_proceed': False
        }
        
        if self._state == AnalysisState.IDLE:
            return result
        
        # Procesar según estado actual
        if self._state == AnalysisState.DETECTING_PERSON:
            result = self._process_detecting_person(landmarks, confidence)
            
        elif self._state == AnalysisState.CHECKING_ORIENTATION:
            result = self._process_checking_orientation(landmarks, detected_orientation, confidence)
            
        elif self._state == AnalysisState.CHECKING_POSTURE:
            result = self._process_checking_posture(landmarks, confidence)
            
        elif self._state == AnalysisState.COUNTDOWN:
            result = self._process_countdown(landmarks)
            
        elif self._state == AnalysisState.ANALYZING:
            result = self._process_analyzing(landmarks, current_angle)
        
        return result
    
    def _process_detecting_person(self, landmarks: Any, confidence: float = 0.0) -> Dict[str, Any]:
        """Procesa el estado DETECTING_PERSON."""
        elapsed = time.time() - self._state_start_time if self._state_start_time else 0
        
        # Verificar detección válida (landmarks + confianza mínima)
        detection_valid = landmarks is not None and landmarks and confidence >= self.MIN_CONFIDENCE
        
        if detection_valid:
            self._consecutive_detections += 1
            
            # Calcular progreso basado en tiempo Y frames consecutivos
            time_progress = elapsed / self.MIN_DETECTING_TIME
            frames_required = 4  # Mínimo 4 frames consecutivos (~2 segundos a 2Hz de polling)
            frames_progress = self._consecutive_detections / frames_required
            
            # Ambos deben cumplirse
            if elapsed >= self.MIN_DETECTING_TIME and self._consecutive_detections >= frames_required:
                self._detection_retries = 0
                self._consecutive_detections = 0  # Reset para siguiente estado
                self._transition_to(AnalysisState.CHECKING_ORIENTATION, "Persona detectada")
                return {
                    'state': self._state.name,
                    'message': self._state_message,
                    'progress': 1.0,
                    'can_proceed': True
                }
            else:
                # Persona detectada pero esperando estabilidad
                progress = min(time_progress, frames_progress)
                return {
                    'state': self._state.name,
                    'message': f"Persona detectada, verificando... ({self._consecutive_detections}/{frames_required})",
                    'progress': progress,
                    'can_proceed': False,
                    'confidence': confidence
                }
        else:
            # No hay detección válida - resetear contador consecutivo
            self._consecutive_detections = 0
            self._state_message = "Buscando persona... Asegúrese de estar visible"
            
            # 🔊 TTS: Repetir recordatorio cada X segundos si no detecta persona
            current_time = time.time()
            if current_time - self._last_detection_reminder >= self._detection_reminder_interval:
                self._last_detection_reminder = current_time
                try:
                    tts = get_tts_service()
                    tts.speak(TTSMessages.DETECTING_RETRY)
                except Exception as e:
                    logger.warning(f"[TTS] Error en recordatorio detección: {e}")
            
            return {
                'state': self._state.name,
                'message': self._state_message,
                'progress': 0.0,
                'can_proceed': False,
                'confidence': confidence
            }

    
    def _process_checking_orientation(
        self,
        landmarks: Any,
        detected_orientation: Optional[str],
        confidence: float = 0.0
    ) -> Dict[str, Any]:
        """Procesa el estado CHECKING_ORIENTATION."""
        elapsed = time.time() - self._state_start_time if self._state_start_time else 0
        frames_required = 4  # Mínimo 4 frames consecutivos con orientación correcta
        
        # Si no hay orientación detectada, resetear contador
        if detected_orientation is None or not landmarks:
            self._consecutive_orientation_ok = 0
            return {
                'state': self._state.name,
                'message': f"Posiciónese de {self.required_orientation}",
                'progress': 0.0,
                'can_proceed': False
            }
        
        # Verificar si la orientación coincide con la requerida
        orientation_matches = detected_orientation.lower() == self.required_orientation.lower()
        
        if orientation_matches and confidence >= self.MIN_CONFIDENCE:
            self._consecutive_orientation_ok += 1
            
            # Calcular progreso
            time_progress = elapsed / self.MIN_ORIENTATION_TIME
            frames_progress = self._consecutive_orientation_ok / frames_required
            
            # Ambos deben cumplirse
            if elapsed >= self.MIN_ORIENTATION_TIME and self._consecutive_orientation_ok >= frames_required:
                self._consecutive_orientation_ok = 0  # Reset para siguiente estado
                self._transition_to(AnalysisState.CHECKING_POSTURE, "Orientación correcta")
                return {
                    'state': self._state.name,
                    'message': "Orientación correcta",
                    'progress': 1.0,
                    'can_proceed': True,
                    'orientation': detected_orientation
                }
            else:
                progress = min(time_progress, frames_progress)
                return {
                    'state': self._state.name,
                    'message': f"Orientación correcta, mantenga posición... ({self._consecutive_orientation_ok}/{frames_required})",
                    'progress': progress,
                    'can_proceed': False,
                    'orientation': detected_orientation
                }
        else:
            # Orientación incorrecta - resetear contador
            self._consecutive_orientation_ok = 0
            
            if self.required_orientation == "profile":
                instruction = "Gire hacia un lado para quedar de perfil"
            else:
                instruction = "Gire hacia la cámara para quedar de frente"
        
            return {
                'state': self._state.name,
                'message': instruction,
                'progress': 0.3,
                'can_proceed': False,
                'current_orientation': detected_orientation,
                'required_orientation': self.required_orientation
            }
    
    def _process_checking_posture(self, landmarks: Any, confidence: float = 0.0) -> Dict[str, Any]:
        """
        Procesa el estado CHECKING_POSTURE.
        
        Verifica que tengamos landmarks estables antes de iniciar el countdown.
        """
        elapsed = time.time() - self._state_start_time if self._state_start_time else 0
        frames_required = 3  # Mínimo 3 frames consecutivos con postura correcta
        
        # Verificar postura válida
        posture_valid = landmarks and confidence >= self.MIN_CONFIDENCE
        
        if posture_valid:
            self._consecutive_posture_ok += 1
            
            # Calcular progreso
            time_progress = elapsed / self.MIN_POSTURE_TIME
            frames_progress = self._consecutive_posture_ok / frames_required
            
            # Ambos deben cumplirse
            if elapsed >= self.MIN_POSTURE_TIME and self._consecutive_posture_ok >= frames_required:
                self._consecutive_posture_ok = 0  # Reset
                self._transition_to(AnalysisState.COUNTDOWN, "Postura correcta")
                return {
                    'state': self._state.name,
                    'message': "Postura correcta - Prepárese",
                    'progress': 1.0,
                    'can_proceed': True
                }
            else:
                progress = min(time_progress, frames_progress)
                return {
                    'state': self._state.name,
                    'message': f"Verificando postura... ({self._consecutive_posture_ok}/{frames_required})",
                    'progress': progress,
                    'can_proceed': False
                }
        else:
            # Postura no válida - resetear contador
            self._consecutive_posture_ok = 0
        
        # Timeout de postura
        if elapsed > self.POSTURE_TIMEOUT:
            self._transition_to(AnalysisState.ERROR, "Timeout de postura")
            return {
                'state': self._state.name,
                'message': "Tiempo agotado. Por favor reintente.",
                'progress': 0.0,
                'can_proceed': False,
                'error': 'posture_timeout'
            }
        
        # Sin postura válida - esperar
        return {
            'state': self._state.name,
            'message': "Mantenga la posición...",
            'progress': min(elapsed / self.POSTURE_TIMEOUT, 0.9),
            'can_proceed': False
        }
    
    def _process_countdown(self, landmarks: Any) -> Dict[str, Any]:
        """
        Procesa el estado COUNTDOWN.
        
        Flujo SINCRONIZADO con fases separadas:
        1. PHASE 'instruction': Decir la instrucción del ejercicio (visual muestra "3")
        2. PHASE 'waiting': Esperar a que termine la instrucción (visual sigue en "3")
        3. PHASE 'counting': Countdown 3 → 2 → 1 sincronizado voz + visual
        """
        
        # === FASE 1: INSTRUCTION - Decir la instrucción (una sola vez) ===
        if self._countdown_phase == 'instruction':
            if not self._instruction_spoken:
                try:
                    tts = get_tts_service()
                    instruction = TTSMessages.get_exercise_instruction(self.joint_type, self.movement_type)
                    tts.speak(instruction)
                    print(f"\n🔊 [COUNTDOWN] FASE 1: Instrucción enviada: '{instruction}'")
                except Exception as e:
                    logger.warning(f"[TTS] Error en instrucción: {e}")
                
                self._instruction_spoken = True
                self._instruction_start_time = time.time()
                self._countdown_start_time = None
                self._last_spoken_countdown = 4  # Valor imposible para forzar "3"
            
            # Pasar a fase de espera
            self._countdown_phase = 'waiting'
            self._current_countdown_value = 3  # Visual siempre en 3 durante instrucción
            print(f"🔊 [COUNTDOWN] Transición a FASE 2: waiting")
            
            return {
                'state': self._state.name,
                'message': "Escucha la instrucción...",
                'progress': 0.0,
                'can_proceed': False,
                'countdown': 3,
                'phase': 'instruction'
            }
        
        # === FASE 2: WAITING - Esperar a que termine la instrucción ===
        if self._countdown_phase == 'waiting':
            try:
                tts = get_tts_service()
                is_speaking = tts.is_speaking
                is_queue_empty = tts.is_queue_empty
                tts_busy = is_speaking or not is_queue_empty
            except Exception as e:
                print(f"🔊 [COUNTDOWN] TTS check error: {e}")
                tts_busy = False
            
            time_since_instruction = time.time() - self._instruction_start_time
            min_instruction_time = 4.0  # Mínimo 4 segundos para la instrucción
            
            # Esperar hasta que: (TTS no esté hablando) Y (haya pasado tiempo mínimo)
            if tts_busy or time_since_instruction < min_instruction_time:
                wait_progress = min(time_since_instruction / min_instruction_time, 0.95)
                print(f"🔊 [COUNTDOWN] FASE 2 ESPERANDO: time={time_since_instruction:.1f}s, min={min_instruction_time}s, tts_busy={tts_busy}")
                self._current_countdown_value = 3  # Visual siempre en 3 durante espera
                return {
                    'state': self._state.name,
                    'message': "Prepárate...",
                    'progress': wait_progress * 0.2,
                    'can_proceed': False,
                    'countdown': 3,
                    'phase': 'waiting_instruction'
                }
            
            # Condiciones cumplidas -> pasar a counting
            self._countdown_phase = 'counting'
            self._countdown_start_time = time.time()
            print(f"\n🔊 [COUNTDOWN] Transición a FASE 3: counting (countdown_start_time set)")
        
        # === FASE 3: COUNTING - Countdown sincronizado 3-2-1 ===
        # Sistema basado en: decir número → esperar que termine → siguiente número
        if self._countdown_phase == 'counting':
            # Obtener estado de TTS
            try:
                tts = get_tts_service()
                tts_busy = tts.is_speaking or not tts.is_queue_empty
            except:
                tts_busy = False
            
            # Determinar qué número mostrar basado en last_spoken
            # last_spoken: 4=ninguno, 3=dijo tres, 2=dijo dos, 1=dijo uno, 0=terminado
            current_display = self._last_spoken_countdown if self._last_spoken_countdown <= 3 else 3
            
            # Si no hemos dicho nada aún (last=4), decir "3"
            if self._last_spoken_countdown == 4:
                self._last_spoken_countdown = 3
                self._current_countdown_value = 3
                self._speak_countdown(3)
                print(f"🔊 [COUNTDOWN] >>> DICIENDO: 3 <<<")
                return {
                    'state': self._state.name,
                    'message': "Comenzamos en... 3",
                    'progress': 0.3,
                    'can_proceed': False,
                    'countdown': 3,
                    'phase': 'countdown'
                }
            
            # Si TTS está ocupado, mantener el número actual
            if tts_busy:
                print(f"🔊 [COUNTDOWN] Esperando TTS... mostrando {current_display}")
                self._current_countdown_value = current_display
                progress = 0.2 + ((4 - current_display) / 3.0) * 0.6
                return {
                    'state': self._state.name,
                    'message': f"Prepárese... {current_display}",
                    'progress': progress,
                    'can_proceed': False,
                    'countdown': current_display,
                    'phase': 'countdown'
                }
            
            # TTS libre - pasar al siguiente número
            next_number = self._last_spoken_countdown - 1
            print(f"🔊 [COUNTDOWN] TTS libre, next={next_number}, last={self._last_spoken_countdown}")
            
            if next_number >= 1:
                # Decir siguiente número
                self._last_spoken_countdown = next_number
                self._current_countdown_value = next_number
                self._speak_countdown(next_number)
                print(f"🔊 [COUNTDOWN] >>> DICIENDO: {next_number} <<<")
                progress = 0.2 + ((4 - next_number) / 3.0) * 0.6
                return {
                    'state': self._state.name,
                    'message': f"Prepárese... {next_number}",
                    'progress': progress,
                    'can_proceed': False,
                    'countdown': next_number,
                    'phase': 'countdown'
                }
            else:
                # Countdown terminado (next_number = 0)
                print(f"🔊 [COUNTDOWN] ====== COUNTDOWN TERMINADO ======")
                self._analysis_start_time = time.time()
                self._current_countdown_value = 0
                
                # Resetear para próxima sesión
                self._last_spoken_countdown = 0
                self._instruction_spoken = False
                self._countdown_start_time = None
                self._countdown_phase = 'instruction'
                
                # Resetear calculadores
                self._rom_calculator.reset()
                self._left_rom_calculator.reset()
                self._right_rom_calculator.reset()
                self._left_max_rom = 0.0
                self._right_max_rom = 0.0
                
                self._transition_to(AnalysisState.ANALYZING, "Cuenta regresiva completada")
                return {
                    'state': self._state.name,
                    'message': "¡Comenzando análisis!",
                    'progress': 1.0,
                    'can_proceed': True,
                    'countdown': 0,
                    'phase': 'done'
                }
        
        # Fallback (no debería llegar aquí)
        self._current_countdown_value = 3
        return {
            'state': self._state.name,
            'message': "Preparando...",
            'progress': 0.0,
            'can_proceed': False,
            'countdown': 3,
            'phase': 'unknown'
        }
    
    def _process_analyzing(
        self,
        landmarks: Any,
        current_angle: Optional[float]
    ) -> Dict[str, Any]:
        """Procesa el estado ANALYZING."""
        elapsed = time.time() - self._analysis_start_time if self._analysis_start_time else 0
        progress = min(elapsed / self.ANALYSIS_DURATION, 1.0)
        self._state_progress = progress
        
        # Callback de progreso
        if self._on_progress:
            self._on_progress(progress)
        
        # Agregar medición si hay ángulo
        if current_angle is not None:
            self._last_angle = current_angle
            self._rom_calculator.add_measurement(current_angle)
        
        # Verificar si completamos el análisis
        if elapsed >= self.ANALYSIS_DURATION:
            self._generate_result()
            self._transition_to(AnalysisState.COMPLETED, "Análisis completado")
            return {
                'state': self._state.name,
                'message': "Análisis completado",
                'progress': 1.0,
                'can_proceed': True,
                'result': self._result.to_dict() if self._result else None
            }
        
        # Verificar plateau (podemos terminar antes si hay plateau estable)
        # Para perfil: verificar calculador principal
        # Para frontal: verificar AMBOS calculadores bilaterales
        plateau_detected = False
        
        if self._is_bilateral:
            # Frontal: ambos lados deben estar estables
            left_plateau = self._left_rom_calculator.detect_plateau()
            right_plateau = self._right_rom_calculator.detect_plateau()
            left_samples = len(self._left_rom_calculator._measurements)
            right_samples = len(self._right_rom_calculator._measurements)
            
            # Plateau bilateral: ambos estables Y suficientes muestras en cada uno
            if left_plateau and right_plateau and left_samples >= 5 and right_samples >= 5:
                plateau_detected = True
        else:
            # Perfil: solo calculador principal
            if self._rom_calculator.detect_plateau():
                samples = len(self._rom_calculator._measurements)
                if samples >= self.MIN_SAMPLES_REQUIRED:
                    plateau_detected = True
        
        if plateau_detected:
            self._generate_result()
            self._transition_to(AnalysisState.COMPLETED, "Plateau detectado")
            return {
                'state': self._state.name,
                'message': "Medición estabilizada",
                'progress': 1.0,
                'can_proceed': True,
                'result': self._result.to_dict() if self._result else None,
                'early_completion': True
            }
        
        # Mostrar ángulo actual
        angle_display = f"{current_angle:.1f}°" if current_angle else "---"
        
        return {
            'state': self._state.name,
            'message': f"Capturando... {angle_display}",
            'progress': progress,
            'can_proceed': False,
            'current_angle': current_angle,
            'samples_collected': len(self._rom_calculator._measurements),
            'time_remaining': self.ANALYSIS_DURATION - elapsed
        }
    
    def _generate_result(self):
        """Genera el resultado final del análisis usando percentil 95."""
        stats = self._rom_calculator.get_capture_window_stats()
        
        # Log para debugging
        logger.info(f"[GENERATE_RESULT] stats={stats}, last_angle={self._last_angle}, samples={len(self._rom_calculator._measurements)}")
        logger.info(f"[GENERATE_RESULT] bilateral={self._is_bilateral}, left_max={self._left_max_rom}, right_max={self._right_max_rom}")
        
        # Si no hay stats pero tenemos un último ángulo, crear resultado mínimo
        if stats is None:
            if self._last_angle is not None and self._last_angle > 0:
                logger.info(f"[GENERATE_RESULT] Usando último ángulo: {self._last_angle}")
                stats = {
                    'percentile_95': self._last_angle,
                    'mean': self._last_angle,
                    'quality': 0.5,
                    'samples': 1,
                    'plateau_detected': False
                }
            else:
                logger.warning("[GENERATE_RESULT] No hay datos de ángulos")
                self._result = None
                return
        
        # Calcular ROM bilateral con percentil 95 (para frontal)
        final_left_rom = None
        final_right_rom = None
        
        if self._is_bilateral:
            left_stats = self._left_rom_calculator.get_capture_window_stats()
            right_stats = self._right_rom_calculator.get_capture_window_stats()
            
            logger.info(f"[GENERATE_RESULT] left_stats={left_stats}")
            logger.info(f"[GENERATE_RESULT] right_stats={right_stats}")
            
            # Usar percentil 95 si hay suficientes datos, sino fallback al máximo
            if left_stats and left_stats.get('samples', 0) >= 3:
                final_left_rom = left_stats['percentile_95']
            else:
                final_left_rom = self._left_max_rom
                
            if right_stats and right_stats.get('samples', 0) >= 3:
                final_right_rom = right_stats['percentile_95']
            else:
                final_right_rom = self._right_max_rom
            
            # Para bilateral, el ROM principal es el mayor de los dos lados
            if final_left_rom > 0 or final_right_rom > 0:
                stats['percentile_95'] = max(final_left_rom or 0, final_right_rom or 0)
                stats['mean'] = (final_left_rom + final_right_rom) / 2 if final_left_rom and final_right_rom else stats['percentile_95']
        
        # Obtener clasificación
        from app.utils.rom_standards import get_rom_classification
        
        classification_data = get_rom_classification(
            segment=self.joint_type,
            exercise=self.movement_type,
            angle=stats['percentile_95']
        )
        
        # Extraer clasificación y rango normal
        classification = classification_data.get('level_display', 'Desconocido')
        normal_max = classification_data.get('normal_max', 0)
        normal_range = (0, normal_max)
        
        # Calcular duración del análisis
        analysis_duration = time.time() - self._analysis_start_time if self._analysis_start_time else 0
        session_duration = time.time() - self._session_start_time if self._session_start_time else 0
        
        self._result = AnalysisResult(
            joint_type=self.joint_type,
            movement_type=self.movement_type,
            orientation=self.required_orientation,
            side=self._detected_side,  # Lado detectado durante el análisis
            rom_value=stats['mean'],
            rom_percentile_95=stats['percentile_95'],
            rom_quality=stats['quality'],
            classification=classification,
            normal_range=normal_range,
            session_duration=session_duration,
            analysis_duration=analysis_duration,
            samples_collected=stats['samples'],
            plateau_detected=stats['plateau_detected'],
            # Datos bilaterales con percentil 95 (para frontal)
            left_max_rom=final_left_rom if self._is_bilateral else None,
            right_max_rom=final_right_rom if self._is_bilateral else None,
            is_bilateral=self._is_bilateral
        )
        
        # 🔊 TTS: El resultado se anuncia desde _speak_state_message(COMPLETED)
        # después de decir "puedes relajarte" para el orden correcto
        
        logger.info(f"[GENERATE_RESULT] Resultado: ROM={stats['percentile_95']}, samples={stats['samples']}, left_p95={final_left_rom}, right_p95={final_right_rom}")
    
    def _try_generate_partial_result(self):
        """Intenta generar un resultado parcial con los datos disponibles."""
        stats = self._rom_calculator.get_capture_window_stats()
        
        if stats and stats['samples'] >= 10:  # Mínimo para resultado parcial
            self._generate_result()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo de la sesión.
        
        Returns:
            Diccionario con estado completo
        """
        # Usar el valor de countdown guardado por _process_countdown
        countdown = None
        if self._state == AnalysisState.COUNTDOWN:
            countdown = self._current_countdown_value
        
        return {
            'state': self._state.name,
            'message': self._state_message,
            'progress': self._state_progress,
            'is_active': self.is_active,
            'joint_type': self.joint_type,
            'movement_type': self.movement_type,
            'required_orientation': self.required_orientation,
            'session_duration': time.time() - self._session_start_time if self._session_start_time else 0,
            'transitions_count': len(self._transitions),
            'countdown': countdown,
            'result': self._result.to_dict() if self._result else None
        }


# -----------------------------------------------------------------------------
# Singleton - Una sola sesión activa a la vez
# -----------------------------------------------------------------------------
_current_session: Optional[AnalysisSession] = None


def create_analysis_session(
    joint_type: str,
    movement_type: str,
    required_orientation: str = "profile"
) -> AnalysisSession:
    """
    Crea una nueva sesión de análisis.
    
    Si hay una sesión activa, la detiene primero.
    
    Args:
        joint_type: Tipo de articulación
        movement_type: Tipo de movimiento
        required_orientation: Orientación requerida
    
    Returns:
        Nueva instancia de AnalysisSession
    """
    global _current_session
    
    # Detener sesión anterior si existe
    if _current_session and _current_session.is_active:
        _current_session.stop()
    
    # Crear nueva sesión
    _current_session = AnalysisSession(
        joint_type=joint_type,
        movement_type=movement_type,
        required_orientation=required_orientation
    )
    
    return _current_session


def get_current_session() -> Optional[AnalysisSession]:
    """
    Obtiene la sesión de análisis actual.
    
    Returns:
        Sesión actual o None si no hay sesión
    """
    return _current_session


def clear_current_session():
    """Limpia la sesión actual."""
    global _current_session
    if _current_session:
        _current_session.stop()
    _current_session = None
