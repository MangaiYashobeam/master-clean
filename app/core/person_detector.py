"""
👤 PERSON DETECTOR - Detección de Persona en Frame
====================================================

Detecta si hay una persona visible en el frame usando MediaPipe Pose.
Utiliza el singleton compartido para no crear instancias adicionales.

Responsabilidades:
- Detectar presencia de persona
- Verificar visibilidad mínima de landmarks clave
- Reportar confianza de detección

Autor: BIOTRACK Team
Fecha: 2025-11-26
"""

from typing import Dict, Any, Optional, Tuple
from app.core.pose_singleton import get_shared_pose


class PersonDetector:
    """
    👤 Detector de persona usando MediaPipe Pose Singleton
    
    Verifica que haya una persona visible con landmarks suficientes
    para realizar un análisis biomecánico.
    """
    
    # Landmarks mínimos requeridos para considerar "persona detectada"
    # Usamos torso + caderas (los más estables)
    ESSENTIAL_LANDMARKS = {
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_hip': 23,
        'right_hip': 24,
    }
    
    # Landmarks adicionales que mejoran la detección
    OPTIONAL_LANDMARKS = {
        'nose': 0,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,
        'left_knee': 25,
        'right_knee': 26,
    }
    
    # Umbral mínimo de visibilidad para considerar un landmark "visible"
    VISIBILITY_THRESHOLD = 0.5
    
    # Porcentaje mínimo de landmarks esenciales visibles
    MIN_ESSENTIAL_COVERAGE = 0.75  # 3 de 4 landmarks esenciales
    
    def __init__(self):
        """Inicializa el detector usando el singleton de MediaPipe"""
        self.pose = get_shared_pose()
        self._last_detection = None
    
    def detect(self, frame) -> Dict[str, Any]:
        """
        Detecta si hay una persona en el frame.
        
        Args:
            frame: Frame BGR de OpenCV
            
        Returns:
            Dict con:
                - detected: bool - Si hay persona detectada
                - confidence: float - Confianza de detección (0-1)
                - landmarks: objeto landmarks de MediaPipe (o None)
                - essential_visible: int - Cantidad de landmarks esenciales visibles
                - message: str - Mensaje descriptivo
        """
        import cv2
        
        if frame is None:
            return self._no_detection("Frame vacío")
        
        # Convertir BGR a RGB para MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Procesar con MediaPipe
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return self._no_detection("No se detecta persona")
        
        landmarks = results.pose_landmarks.landmark
        
        # Evaluar landmarks esenciales
        essential_eval = self._evaluate_essential_landmarks(landmarks)
        
        if not essential_eval['sufficient']:
            return self._partial_detection(
                landmarks=results.pose_landmarks,
                essential_visible=essential_eval['visible_count'],
                message=essential_eval['message']
            )
        
        # Evaluar landmarks opcionales para calcular confianza
        optional_eval = self._evaluate_optional_landmarks(landmarks)
        
        # Calcular confianza general
        confidence = self._calculate_confidence(essential_eval, optional_eval)
        
        self._last_detection = {
            'detected': True,
            'confidence': confidence,
            'landmarks': results.pose_landmarks,
            'essential_visible': essential_eval['visible_count'],
            'optional_visible': optional_eval['visible_count'],
            'message': "Persona detectada correctamente",
            'details': {
                'essential': essential_eval,
                'optional': optional_eval
            }
        }
        
        return self._last_detection
    
    def _evaluate_essential_landmarks(self, landmarks) -> Dict[str, Any]:
        """Evalúa visibilidad de landmarks esenciales"""
        visible_count = 0
        visibility_scores = {}
        
        for name, idx in self.ESSENTIAL_LANDMARKS.items():
            if idx < len(landmarks):
                visibility = landmarks[idx].visibility
                visibility_scores[name] = visibility
                if visibility >= self.VISIBILITY_THRESHOLD:
                    visible_count += 1
        
        total = len(self.ESSENTIAL_LANDMARKS)
        coverage = visible_count / total
        sufficient = coverage >= self.MIN_ESSENTIAL_COVERAGE
        
        if not sufficient:
            if visible_count == 0:
                message = "No se detectan puntos corporales clave"
            else:
                message = f"Visibilidad insuficiente ({visible_count}/{total} puntos)"
        else:
            message = f"Puntos esenciales OK ({visible_count}/{total})"
        
        return {
            'visible_count': visible_count,
            'total': total,
            'coverage': coverage,
            'sufficient': sufficient,
            'visibility_scores': visibility_scores,
            'message': message
        }
    
    def _evaluate_optional_landmarks(self, landmarks) -> Dict[str, Any]:
        """Evalúa visibilidad de landmarks opcionales"""
        visible_count = 0
        visibility_scores = {}
        
        for name, idx in self.OPTIONAL_LANDMARKS.items():
            if idx < len(landmarks):
                visibility = landmarks[idx].visibility
                visibility_scores[name] = visibility
                if visibility >= self.VISIBILITY_THRESHOLD:
                    visible_count += 1
        
        return {
            'visible_count': visible_count,
            'total': len(self.OPTIONAL_LANDMARKS),
            'coverage': visible_count / len(self.OPTIONAL_LANDMARKS),
            'visibility_scores': visibility_scores
        }
    
    def _calculate_confidence(self, essential: Dict, optional: Dict) -> float:
        """
        Calcula confianza de detección basada en landmarks visibles.
        
        Fórmula: 70% esenciales + 30% opcionales
        """
        essential_score = essential['coverage']
        optional_score = optional['coverage']
        
        confidence = (essential_score * 0.7) + (optional_score * 0.3)
        return round(confidence, 2)
    
    def _no_detection(self, message: str) -> Dict[str, Any]:
        """Retorna resultado cuando no hay detección"""
        return {
            'detected': False,
            'confidence': 0.0,
            'landmarks': None,
            'essential_visible': 0,
            'message': message
        }
    
    def _partial_detection(self, landmarks, essential_visible: int, message: str) -> Dict[str, Any]:
        """Retorna resultado cuando hay detección parcial insuficiente"""
        return {
            'detected': False,
            'confidence': 0.0,
            'landmarks': landmarks,  # Incluimos landmarks para debug
            'essential_visible': essential_visible,
            'message': message
        }
    
    @property
    def last_detection(self) -> Optional[Dict[str, Any]]:
        """Retorna la última detección realizada"""
        return self._last_detection


# Instancia singleton del detector (opcional, para uso directo)
_person_detector_instance = None

def get_person_detector() -> PersonDetector:
    """
    Obtiene instancia singleton del PersonDetector.
    
    Útil para evitar crear múltiples instancias en diferentes partes del código.
    """
    global _person_detector_instance
    if _person_detector_instance is None:
        _person_detector_instance = PersonDetector()
    return _person_detector_instance
