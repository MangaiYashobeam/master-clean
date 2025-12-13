"""
✋ POSTURE VERIFIER - Verificación de Postura para Análisis
============================================================

Verifica que la postura del paciente sea adecuada para realizar
un análisis biomecánico preciso.

Verificaciones:
- Orientación correcta (perfil/frontal según ejercicio)
- Distancia adecuada a la cámara
- Torso relativamente recto
- Landmarks requeridos visibles

Autor: BIOTRACK Team
Fecha: 2025-11-26
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from app.core.orientation_detector import AdaptiveOrientationDetector


class PostureStatus(Enum):
    """Estados posibles de verificación de postura"""
    OK = "ok"
    WRONG_ORIENTATION = "wrong_orientation"
    TOO_CLOSE = "too_close"
    TOO_FAR = "too_far"
    TORSO_NOT_STRAIGHT = "torso_not_straight"
    LANDMARKS_NOT_VISIBLE = "landmarks_not_visible"
    PARTIAL = "partial"  # Algunos problemas menores


class RequiredOrientation(Enum):
    """Orientaciones requeridas para ejercicios"""
    PROFILE = "SAGITAL"      # Vista de perfil (lado)
    FRONTAL = "FRONTAL"      # Vista frontal (de frente)
    ANY = "ANY"              # Cualquier orientación


class PostureVerifier:
    """
    ✋ Verificador de postura para análisis biomecánico
    
    Verifica que el paciente esté en posición correcta antes
    de iniciar la captura de ROM.
    """
    
    # Configuración por defecto
    DEFAULT_CONFIG = {
        # Distancia: basada en el ancho de hombros normalizado
        'min_shoulder_width': 0.08,   # Muy lejos si < 0.08
        'max_shoulder_width': 0.45,   # Muy cerca si > 0.45
        'ideal_shoulder_width': (0.15, 0.35),  # Rango ideal
        
        # Torso: diferencia vertical entre hombros
        'max_shoulder_tilt': 0.08,    # Máxima inclinación de hombros
        
        # Confianza mínima para orientación
        'min_orientation_confidence': 0.6,
    }
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el verificador de postura.
        
        Args:
            config: Configuración personalizada (opcional)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.orientation_detector = AdaptiveOrientationDetector()
        self._last_verification = None
    
    def verify(
        self,
        landmarks,
        required_orientation: RequiredOrientation = RequiredOrientation.ANY,
        required_landmarks: List[int] = None
    ) -> Dict[str, Any]:
        """
        Verifica la postura del paciente.
        
        Args:
            landmarks: Landmarks de MediaPipe
            required_orientation: Orientación requerida para el ejercicio
            required_landmarks: Lista de índices de landmarks requeridos
            
        Returns:
            Dict con:
                - status: PostureStatus
                - is_valid: bool
                - issues: List[str] - Problemas detectados
                - suggestions: List[str] - Sugerencias para corregir
                - details: Dict - Detalles de cada verificación
        """
        issues = []
        suggestions = []
        details = {}
        
        # 1. Verificar orientación
        orientation_result = self._verify_orientation(landmarks, required_orientation)
        details['orientation'] = orientation_result
        if not orientation_result['is_valid']:
            issues.append(orientation_result['issue'])
            suggestions.append(orientation_result['suggestion'])
        
        # 2. Verificar distancia
        distance_result = self._verify_distance(landmarks)
        details['distance'] = distance_result
        if not distance_result['is_valid']:
            issues.append(distance_result['issue'])
            suggestions.append(distance_result['suggestion'])
        
        # 3. Verificar inclinación de torso
        torso_result = self._verify_torso_alignment(landmarks)
        details['torso'] = torso_result
        if not torso_result['is_valid']:
            issues.append(torso_result['issue'])
            suggestions.append(torso_result['suggestion'])
        
        # 4. Verificar landmarks requeridos
        if required_landmarks:
            landmarks_result = self._verify_required_landmarks(landmarks, required_landmarks)
            details['landmarks'] = landmarks_result
            if not landmarks_result['is_valid']:
                issues.append(landmarks_result['issue'])
                suggestions.append(landmarks_result['suggestion'])
        
        # Determinar estado final
        if not issues:
            status = PostureStatus.OK
            is_valid = True
        elif len(issues) == 1 and 'menor' in issues[0].lower():
            status = PostureStatus.PARTIAL
            is_valid = True  # Permitir con advertencia
        else:
            # Determinar el problema principal
            if not orientation_result['is_valid']:
                status = PostureStatus.WRONG_ORIENTATION
            elif not distance_result['is_valid']:
                status = PostureStatus.TOO_CLOSE if distance_result.get('too_close') else PostureStatus.TOO_FAR
            elif not torso_result['is_valid']:
                status = PostureStatus.TORSO_NOT_STRAIGHT
            else:
                status = PostureStatus.LANDMARKS_NOT_VISIBLE
            is_valid = False
        
        self._last_verification = {
            'status': status,
            'is_valid': is_valid,
            'issues': issues,
            'suggestions': suggestions,
            'details': details
        }
        
        return self._last_verification
    
    def _verify_orientation(
        self,
        landmarks,
        required: RequiredOrientation
    ) -> Dict[str, Any]:
        """Verifica que la orientación sea la correcta"""
        
        if required == RequiredOrientation.ANY:
            return {
                'is_valid': True,
                'current': 'ANY',
                'required': 'ANY',
                'confidence': 1.0
            }
        
        # Detectar orientación actual
        orientation_result = self.orientation_detector.detect_orientation_adaptive(landmarks)
        current_orientation = orientation_result.get('orientation', 'UNKNOWN')
        confidence = orientation_result.get('confidence', 0)
        
        # Comparar con requerida
        required_value = required.value  # "SAGITAL" o "FRONTAL"
        is_valid = current_orientation == required_value
        
        if is_valid:
            return {
                'is_valid': True,
                'current': current_orientation,
                'required': required_value,
                'confidence': confidence
            }
        else:
            if required == RequiredOrientation.PROFILE:
                suggestion = "Colóquese de lado a la cámara (vista de perfil)"
            else:
                suggestion = "Colóquese de frente a la cámara"
            
            return {
                'is_valid': False,
                'current': current_orientation,
                'required': required_value,
                'confidence': confidence,
                'issue': f"Orientación incorrecta: {current_orientation} (requiere {required_value})",
                'suggestion': suggestion
            }
    
    def _verify_distance(self, landmarks) -> Dict[str, Any]:
        """Verifica que la distancia a la cámara sea adecuada"""
        
        # Usar ancho de hombros como proxy de distancia
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        shoulder_width = abs(left_shoulder.x - right_shoulder.x)
        
        min_width = self.config['min_shoulder_width']
        max_width = self.config['max_shoulder_width']
        ideal_min, ideal_max = self.config['ideal_shoulder_width']
        
        if shoulder_width < min_width:
            return {
                'is_valid': False,
                'shoulder_width': shoulder_width,
                'too_far': True,
                'too_close': False,
                'issue': "Está muy lejos de la cámara",
                'suggestion': "Acérquese a la cámara"
            }
        elif shoulder_width > max_width:
            return {
                'is_valid': False,
                'shoulder_width': shoulder_width,
                'too_far': False,
                'too_close': True,
                'issue': "Está muy cerca de la cámara",
                'suggestion': "Aléjese de la cámara"
            }
        elif ideal_min <= shoulder_width <= ideal_max:
            return {
                'is_valid': True,
                'shoulder_width': shoulder_width,
                'distance_quality': 'ideal'
            }
        else:
            # Aceptable pero no ideal
            return {
                'is_valid': True,
                'shoulder_width': shoulder_width,
                'distance_quality': 'acceptable'
            }
    
    def _verify_torso_alignment(self, landmarks) -> Dict[str, Any]:
        """Verifica que el torso esté relativamente recto"""
        
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        # Diferencia vertical entre hombros
        shoulder_tilt = abs(left_shoulder.y - right_shoulder.y)
        max_tilt = self.config['max_shoulder_tilt']
        
        if shoulder_tilt > max_tilt:
            return {
                'is_valid': False,
                'shoulder_tilt': shoulder_tilt,
                'max_allowed': max_tilt,
                'issue': "Hombros muy inclinados",
                'suggestion': "Mantenga los hombros nivelados"
            }
        else:
            return {
                'is_valid': True,
                'shoulder_tilt': shoulder_tilt,
                'alignment_quality': 'good' if shoulder_tilt < max_tilt * 0.5 else 'acceptable'
            }
    
    def _verify_required_landmarks(
        self,
        landmarks,
        required_indices: List[int]
    ) -> Dict[str, Any]:
        """Verifica que los landmarks requeridos estén visibles"""
        
        visible = []
        not_visible = []
        
        for idx in required_indices:
            if idx < len(landmarks) and landmarks[idx].visibility >= 0.5:
                visible.append(idx)
            else:
                not_visible.append(idx)
        
        coverage = len(visible) / len(required_indices)
        
        if coverage >= 0.8:  # 80% visible es aceptable
            return {
                'is_valid': True,
                'visible': visible,
                'not_visible': not_visible,
                'coverage': coverage
            }
        else:
            return {
                'is_valid': False,
                'visible': visible,
                'not_visible': not_visible,
                'coverage': coverage,
                'issue': f"Puntos corporales no visibles ({len(not_visible)} ocultos)",
                'suggestion': "Asegúrese de que todo su cuerpo sea visible"
            }
    
    def get_message_for_status(self, status: PostureStatus) -> str:
        """Retorna mensaje amigable para cada estado"""
        messages = {
            PostureStatus.OK: "✅ Postura correcta",
            PostureStatus.WRONG_ORIENTATION: "📐 Ajuste su orientación",
            PostureStatus.TOO_CLOSE: "↔️ Aléjese de la cámara",
            PostureStatus.TOO_FAR: "↔️ Acérquese a la cámara",
            PostureStatus.TORSO_NOT_STRAIGHT: "🧍 Mantenga el torso recto",
            PostureStatus.LANDMARKS_NOT_VISIBLE: "👁️ Asegúrese de ser visible",
            PostureStatus.PARTIAL: "⚠️ Postura aceptable con advertencias"
        }
        return messages.get(status, "Estado desconocido")
    
    @property
    def last_verification(self) -> Optional[Dict[str, Any]]:
        """Retorna la última verificación realizada"""
        return self._last_verification


# Instancia singleton del verificador (opcional)
_posture_verifier_instance = None

def get_posture_verifier() -> PostureVerifier:
    """Obtiene instancia singleton del PostureVerifier"""
    global _posture_verifier_instance
    if _posture_verifier_instance is None:
        _posture_verifier_instance = PostureVerifier()
    return _posture_verifier_instance
