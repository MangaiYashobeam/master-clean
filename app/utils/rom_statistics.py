"""
📊 ROM STATISTICS - Calculadora de Estadísticas de Rango de Movimiento
=======================================================================

Calcula estadísticas precisas para mediciones ROM:
- Percentil 95 para ROM máximo (robusto contra outliers)
- Detección de meseta (estabilidad del ángulo)
- Calidad de medición basada en estabilidad
- Clasificación según estándares clínicos

NO crea hilos ni procesos adicionales.
NO crea instancias de MediaPipe.

Autor: BIOTRACK Team
Fecha: 2025-11-26
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from enum import Enum


class MeasurementQuality(Enum):
    """Calidad de la medición basada en estabilidad"""
    EXCELLENT = "excelente"   # Desv. < 3°, muestras >= 10
    GOOD = "buena"            # Desv. < 5°, muestras >= 5
    ACCEPTABLE = "aceptable"  # Desv. < 10°, muestras >= 3
    LOW = "baja"              # Desv. >= 10° o pocas muestras


class ROMClassification(Enum):
    """
    Clasificación clínica del ROM
    
    Basado en estándares goniométricos internacionales:
    - AAOS (American Academy of Orthopaedic Surgeons) - Joint Motion
    - Beighton Scale - Criterios de hiperlaxitud articular
    - Nordin & Frankel - Basic Biomechanics of the Musculoskeletal System
    - Kapandji - Fisiología Articular
    
    Clasificación:
    - Muy Limitado: <50% del rango normal - Restricción severa
    - Limitado: 50-69% - Restricción moderada  
    - Funcional: 70-89% - Rango aceptable para AVD
    - Óptimo: 90-100% - Rango normal completo
    - Aumentado: >100% - Hiperlaxitud/Hipermovilidad
    
    NOTA CLÍNICA: "Aumentado" NO significa "mejor". La hiperlaxitud indica:
    - Laxitud ligamentosa constitucional
    - Mayor demanda de control neuromuscular
    - Posible riesgo de inestabilidad articular
    
    Referencia: Según AAOS y Beighton Scale, superar el rango normal
    fisiológico máximo constituye hiperlaxitud articular.
    """
    INCREASED = "aumentado"        # > 100% del rango normal (hiperlaxitud)
    OPTIMAL = "óptimo"             # 90-100% del rango normal
    FUNCTIONAL = "funcional"       # 70-89% del rango normal
    LIMITED = "limitado"           # 50-69% del rango normal
    VERY_LIMITED = "muy_limitado"  # < 50% del rango normal


class ROMStatisticsCalculator:
    """
    📊 Calculadora de estadísticas ROM
    
    Características:
    - Recolecta ángulos durante el análisis
    - Calcula percentil 95 (robusto contra outliers)
    - Detecta meseta (ángulo estable por tiempo)
    - Evalúa calidad de medición
    - Clasifica según estándares clínicos
    
    NO crea hilos, procesos ni instancias de MediaPipe.
    """
    
    # Configuración por defecto
    DEFAULT_CONFIG = {
        # Ventana de captura
        'capture_window_start': 10.0,   # Segundo donde inicia captura
        'capture_window_end': 12.0,     # Segundo donde termina captura
        'buffer_zone_start': 12.0,      # Buffer de seguridad
        
        # Detección de meseta
        'plateau_threshold': 5.0,       # ±5° para considerar estable
        'plateau_duration': 3.0,        # Segundos estable para meseta (antes: 2.0)
        
        # Calidad de medición
        'excellent_std': 3.0,           # Desv. estándar para "excelente"
        'good_std': 5.0,                # Desv. estándar para "buena"
        'acceptable_std': 10.0,         # Desv. estándar para "aceptable"
        'min_samples_excellent': 10,
        'min_samples_good': 5,
        'min_samples_acceptable': 3,
    }
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el calculador de estadísticas.
        
        Args:
            config: Configuración personalizada (opcional)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        # Almacenamiento de datos
        self._all_angles: List[Tuple[float, float]] = []  # (timestamp, angle)
        self._capture_window_angles: List[float] = []
        self._plateau_detected = False
        self._plateau_angle: Optional[float] = None
        self._start_time: Optional[float] = None
        
        # Resultado calculado
        self._result: Optional[Dict[str, Any]] = None
    
    def reset(self):
        """Reinicia el calculador para una nueva sesión"""
        self._all_angles = []
        self._capture_window_angles = []
        self._plateau_detected = False
        self._plateau_angle = None
        self._start_time = None
        self._result = None
    
    def start_session(self):
        """Marca el inicio de una sesión de captura"""
        import time
        self.reset()
        self._start_time = time.time()
    
    def add_angle(self, angle: float, timestamp: float = None):
        """
        Agrega un ángulo a la colección.
        
        Args:
            angle: Ángulo medido en grados
            timestamp: Timestamp opcional (usa tiempo actual si no se proporciona)
        """
        import time
        
        if timestamp is None:
            if self._start_time is None:
                self._start_time = time.time()
            timestamp = time.time() - self._start_time
        
        self._all_angles.append((timestamp, angle))
        
        # Verificar si está en ventana de captura
        if (self.config['capture_window_start'] <= timestamp < 
            self.config['capture_window_end']):
            self._capture_window_angles.append(angle)
        
        # Detectar meseta
        self._check_plateau()
    
    def _check_plateau(self):
        """Verifica si se ha alcanzado una meseta (ángulo estable)"""
        if self._plateau_detected:
            return
        
        if len(self._all_angles) < 10:  # Mínimo para evaluar
            return
        
        # Tomar últimos N segundos
        duration = self.config['plateau_duration']
        threshold = self.config['plateau_threshold']
        
        # Filtrar ángulos en la ventana de tiempo
        if self._all_angles:
            current_time = self._all_angles[-1][0]
            window_start = current_time - duration
            
            window_angles = [
                angle for ts, angle in self._all_angles 
                if ts >= window_start
            ]
            
            if len(window_angles) >= 5:  # Mínimo para evaluar estabilidad
                std = np.std(window_angles)
                if std <= threshold:
                    self._plateau_detected = True
                    self._plateau_angle = np.median(window_angles)
    
    def calculate_rom(self) -> Dict[str, Any]:
        """
        Calcula el ROM final y estadísticas.
        
        Prioridad de cálculo:
        1. Percentil 95 de ventana de captura (si hay suficientes datos)
        2. Ángulo de meseta (si se detectó)
        3. Percentil 95 de todos los datos (fallback)
        
        Returns:
            Dict con ROM calculado, calidad, clasificación, etc.
        """
        if not self._all_angles:
            return self._empty_result("No hay datos de ángulos")
        
        all_angles = [angle for _, angle in self._all_angles]
        
        # Método 1: Ventana de captura (preferido)
        if len(self._capture_window_angles) >= 3:
            rom_value = float(np.percentile(self._capture_window_angles, 95))
            method = "capture_window_p95"
            sample_count = len(self._capture_window_angles)
            std_dev = float(np.std(self._capture_window_angles))
        
        # Método 2: Meseta detectada
        elif self._plateau_detected and self._plateau_angle is not None:
            rom_value = self._plateau_angle
            method = "plateau_detection"
            sample_count = len(all_angles)
            std_dev = float(np.std(all_angles[-10:]))  # Últimas 10 muestras
        
        # Método 3: Fallback - todos los datos
        else:
            rom_value = float(np.percentile(all_angles, 95))
            method = "all_data_p95"
            sample_count = len(all_angles)
            std_dev = float(np.std(all_angles))
        
        # Calcular calidad
        quality = self._calculate_quality(std_dev, sample_count)
        
        # Calcular estadísticas adicionales
        self._result = {
            'rom': round(rom_value, 1),
            'method': method,
            'quality': quality.value,
            'quality_score': self._quality_to_score(quality),
            'sample_count': sample_count,
            'std_dev': round(std_dev, 2),
            'plateau_detected': self._plateau_detected,
            'statistics': {
                'min': round(float(np.min(all_angles)), 1),
                'max': round(float(np.max(all_angles)), 1),
                'mean': round(float(np.mean(all_angles)), 1),
                'median': round(float(np.median(all_angles)), 1),
                'p25': round(float(np.percentile(all_angles, 25)), 1),
                'p75': round(float(np.percentile(all_angles, 75)), 1),
                'p95': round(float(np.percentile(all_angles, 95)), 1),
            }
        }
        
        return self._result
    
    def classify_rom(
        self, 
        rom_value: float, 
        normal_range: Tuple[float, float],
        hypermobility_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Clasifica el ROM según el rango normal del movimiento articular.
        
        Referencias bibliográficas:
        - AAOS (American Academy of Orthopaedic Surgeons) - Joint Motion
        - Beighton Scale - Criterios de hiperlaxitud (>10° en codo/rodilla)
        - Nordin & Frankel - Basic Biomechanics (5th ed.)
        
        Clasificación:
        - Muy Limitado: <50% del rango normal
        - Limitado: 50-69% del rango normal
        - Funcional: 70-89% del rango normal
        - Óptimo: 90-100% del rango normal
        - Aumentado: >100% del rango normal (hiperlaxitud)
        
        Justificación del umbral >100%:
        Según AAOS, el rango normal representa el máximo fisiológico esperado.
        Superar este límite indica hiperlaxitud articular (Beighton Scale).
        
        Args:
            rom_value: Valor ROM medido en grados
            normal_range: (min_normal, max_normal) del movimiento
            hypermobility_threshold: Umbral explícito para hiperlaxitud (opcional)
            
        Returns:
            Dict con clasificación, porcentaje y metadata
        """
        min_normal, max_normal = normal_range
        range_size = max_normal - min_normal
        
        if range_size <= 0:
            return {
                'classification': ROMClassification.FUNCTIONAL.value,
                'percentage': 100,
                'message': "Rango normal no definido"
            }
        
        # Calcular porcentaje del rango normal alcanzado
        # Para ROM que excede el máximo, el porcentaje puede ser >100%
        if rom_value <= min_normal:
            percentage = 0
        else:
            percentage = ((rom_value - min_normal) / range_size) * 100
        
        # Determinar umbral de hiperlaxitud
        # Prioridad: umbral explícito > máximo normal (100%)
        # Nota: Usamos 100.5% para evitar errores de precisión de punto flotante
        # (ej: 150.0/150.0*100 = 100.00000000000001 técnicamente > 100)
        if hypermobility_threshold is not None:
            is_hypermobile = rom_value > hypermobility_threshold
        else:
            # Umbral por defecto: >100% del rango normal (supera máximo fisiológico)
            # Según AAOS: superar el rango normal = hiperlaxitud
            is_hypermobile = percentage > 100.5
        
        # Clasificar según porcentaje
        if is_hypermobile:
            classification = ROMClassification.INCREASED
            message = "ROM aumentado - Posible hiperlaxitud articular"
        elif percentage >= 90:
            classification = ROMClassification.OPTIMAL
            message = "Rango de movimiento óptimo"
        elif percentage >= 70:
            classification = ROMClassification.FUNCTIONAL
            message = "Rango de movimiento funcional"
        elif percentage >= 50:
            classification = ROMClassification.LIMITED
            message = "Rango de movimiento limitado"
        else:
            classification = ROMClassification.VERY_LIMITED
            message = "Rango de movimiento muy limitado"
        
        return {
            'classification': classification.value,
            'percentage': round(percentage, 1),
            'message': message,
            'rom_value': rom_value,
            'normal_range': normal_range,
            'hypermobility_threshold': hypermobility_threshold,
            'is_hypermobile': is_hypermobile
        }
    
    def _calculate_quality(
        self, 
        std_dev: float, 
        sample_count: int
    ) -> MeasurementQuality:
        """Calcula la calidad de medición"""
        config = self.config
        
        if (std_dev < config['excellent_std'] and 
            sample_count >= config['min_samples_excellent']):
            return MeasurementQuality.EXCELLENT
        
        if (std_dev < config['good_std'] and 
            sample_count >= config['min_samples_good']):
            return MeasurementQuality.GOOD
        
        if (std_dev < config['acceptable_std'] and 
            sample_count >= config['min_samples_acceptable']):
            return MeasurementQuality.ACCEPTABLE
        
        return MeasurementQuality.LOW
    
    def _quality_to_score(self, quality: MeasurementQuality) -> int:
        """Convierte calidad a score numérico (0-100)"""
        scores = {
            MeasurementQuality.EXCELLENT: 95,
            MeasurementQuality.GOOD: 80,
            MeasurementQuality.ACCEPTABLE: 60,
            MeasurementQuality.LOW: 40
        }
        return scores.get(quality, 0)
    
    def _empty_result(self, message: str) -> Dict[str, Any]:
        """Retorna resultado vacío con mensaje de error"""
        return {
            'rom': 0,
            'method': 'none',
            'quality': MeasurementQuality.LOW.value,
            'quality_score': 0,
            'sample_count': 0,
            'std_dev': 0,
            'plateau_detected': False,
            'error': message,
            'statistics': {}
        }
    
    @property
    def angle_count(self) -> int:
        """Número de ángulos recolectados"""
        return len(self._all_angles)
    
    @property
    def capture_window_count(self) -> int:
        """Número de ángulos en ventana de captura"""
        return len(self._capture_window_angles)
    
    @property
    def is_plateau_detected(self) -> bool:
        """Si se detectó meseta"""
        return self._plateau_detected
    
    @property
    def current_stats(self) -> Dict[str, Any]:
        """Estadísticas actuales (sin calcular ROM final)"""
        if not self._all_angles:
            return {'count': 0}
        
        angles = [a for _, a in self._all_angles]
        return {
            'count': len(angles),
            'current': angles[-1] if angles else 0,
            'max': max(angles),
            'mean': np.mean(angles),
            'plateau_detected': self._plateau_detected
        }

    # =========================================================================
    # ALIAS DE MÉTODOS - Compatibilidad con analysis_session.py
    # =========================================================================
    
    def add_measurement(self, angle: float, timestamp: float = None):
        """Alias de add_angle() para compatibilidad con analysis_session.py"""
        self.add_angle(angle, timestamp)
    
    def detect_plateau(self) -> bool:
        """Alias de is_plateau_detected para compatibilidad con analysis_session.py"""
        return self._plateau_detected
    
    def get_capture_window_stats(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas de la ventana de captura.
        Compatible con analysis_session.py
        
        Returns:
            Dict con estadísticas o None si no hay suficientes datos
        """
        if len(self._all_angles) < 3:
            return None
        
        # Calcular ROM usando el método principal
        result = self.calculate_rom()
        
        if 'error' in result:
            return None
        
        # Formatear en el formato esperado por analysis_session.py
        return {
            'percentile_95': result['rom'],
            'mean': result['statistics'].get('mean', 0),
            'std': result['std_dev'],
            'samples': result['sample_count'],
            'quality': result['quality_score'] / 100.0,  # Convertir a 0.0-1.0
            'plateau_detected': result['plateau_detected']
        }
    
    @property
    def _measurements(self) -> List[Tuple[float, float]]:
        """Alias de _all_angles para compatibilidad"""
        return self._all_angles
