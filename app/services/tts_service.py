# -*- coding: utf-8 -*-
"""
🔊 TTS SERVICE - Servicio de Text-to-Speech con Edge-TTS (Voz Dalia)
=====================================================================

Servicio SINGLETON para reproducir mensajes de voz durante el análisis ROM.
Usa Microsoft Edge TTS para acceder a voces neurales de alta calidad.

Características:
- SINGLETON: Una única instancia para toda la aplicación
- HILO DAEMON: Se cierra automáticamente cuando Flask termina
- NO BLOQUEA: El análisis continúa mientras se reproduce el audio
- CANCELABLE: Puede interrumpir mensaje actual para reproducir nuevo
- TOGGLE: Puede activarse/desactivarse sin destruir el hilo
- VOZ NATURAL: Usa es-MX-DaliaNeural (voz neuronal de Microsoft)

Requisitos:
    pip install edge-tts pygame

Uso:
    from app.services.tts_service import get_tts_service
    
    tts = get_tts_service()
    tts.speak("Colócate frente a la cámara")
    tts.stop_current()  # Cancela mensaje actual
    tts.toggle_voice()  # Activa/desactiva

Autor: BIOTRACK Team
Fecha: 2025-12-01
"""

import threading
import queue
import logging
import time
import os
import tempfile
import asyncio
import hashlib
from typing import Optional, Dict, Any
from enum import Enum
from pathlib import Path

# Imports de audio (verificar disponibilidad al inicio)
# type: ignore - Los módulos se instalan con: pip install edge-tts pygame
print("\n🔊 [TTS_IMPORT] Intentando importar edge_tts y pygame...")
try:
    import edge_tts  # type: ignore
    print(f"🔊 [TTS_IMPORT] ✅ edge_tts importado: {edge_tts.__file__}")
    import pygame  # type: ignore
    print(f"🔊 [TTS_IMPORT] ✅ pygame importado: {pygame.__file__}")
    AUDIO_AVAILABLE = True
    print("🔊 [TTS_IMPORT] ✅ AUDIO_AVAILABLE = True")
except ImportError as e:
    AUDIO_AVAILABLE = False
    print(f"🔊 [TTS_IMPORT] ❌ ERROR importando: {e}")
    logging.warning(f"[TTSService] Módulos de audio no disponibles: {e}")
except Exception as e:
    AUDIO_AVAILABLE = False
    print(f"🔊 [TTS_IMPORT] ❌ EXCEPCIÓN importando: {type(e).__name__}: {e}")
    logging.warning(f"[TTSService] Error inesperado en import: {e}")

# Logger
logger = logging.getLogger(__name__)


class TTSState(Enum):
    """Estados del servicio TTS"""
    IDLE = "idle"           # Esperando mensajes
    SPEAKING = "speaking"   # Reproduciendo mensaje
    STOPPING = "stopping"   # Deteniendo mensaje actual


# ============================================================================
# MENSAJES PREDEFINIDOS PARA ANÁLISIS ROM (DEBE IR ANTES DE TTSService)
# ============================================================================

class TTSMessages:
    """
    📢 Mensajes predefinidos para cada estado del análisis.
    """
    
    # === DETECCIÓN DE PERSONA ===
    DETECTING_PERSON = "Colócate frente a la cámara"
    DETECTING_RETRY = "No te detecto. Asegúrate de estar visible"
    
    # === ORIENTACIÓN ===
    ORIENTATION_PROFILE = "Gira de lado"
    ORIENTATION_FRONTAL = "Colócate de frente"
    
    # === POSTURA ===
    CHECKING_POSTURE = "Brazos relajados a los lados"
    POSTURE_VERIFIED = "Postura correcta"
    
    # === INSTRUCCIONES POR EJERCICIO ===
    # Hombro
    INSTRUCTION_SHOULDER_FLEXION = "Levanta el brazo hacia adelante y arriba, lo más que puedas"
    INSTRUCTION_SHOULDER_EXTENSION = "Lleva el brazo hacia atrás, lo más que puedas"
    INSTRUCTION_SHOULDER_ABDUCTION = "Levanta ambos brazos hacia los lados, lo más que puedas"
    
    # Codo
    INSTRUCTION_ELBOW_FLEXION = "Dobla el codo llevando la mano hacia el hombro"
    INSTRUCTION_ELBOW_EXTENSION = "Estira el codo completamente"
    
    # Cadera
    INSTRUCTION_HIP_FLEXION = "Levanta la rodilla hacia el pecho"
    INSTRUCTION_HIP_EXTENSION = "Lleva la pierna hacia atrás"
    INSTRUCTION_HIP_ABDUCTION = "Separa las piernas hacia los lados"
    
    # Rodilla
    INSTRUCTION_KNEE_FLEXION = "Dobla la rodilla llevando el talón hacia el glúteo"
    INSTRUCTION_KNEE_EXTENSION = "Estira la rodilla completamente"
    
    # Tobillo
    INSTRUCTION_ANKLE_DORSIFLEXION = "Lleva la punta del pie hacia arriba"
    INSTRUCTION_ANKLE_PLANTARFLEXION = "Lleva la punta del pie hacia abajo"
    
    # === CUENTA REGRESIVA ===
    COUNTDOWN_3 = "Tres"
    COUNTDOWN_2 = "Dos"
    COUNTDOWN_1 = "Uno"
    
    # === ANÁLISIS ===
    ANALYZING_START = "¡Ahora! Realiza el movimiento"
    ANALYZING_HOLD = "Mantén la posición"
    
    # === COMPLETADO ===
    COMPLETED_RELAX = "Puedes relajarte"
    
    @staticmethod
    def get_exercise_instruction(joint_type: str, movement_type: str) -> str:
        """
        Obtiene la instrucción específica para un ejercicio.
        
        Args:
            joint_type: Tipo de articulación ('shoulder', 'elbow', etc.)
            movement_type: Tipo de movimiento ('flexion', 'extension', etc.)
        
        Returns:
            Instrucción de voz para el ejercicio
        """
        key = f"INSTRUCTION_{joint_type.upper()}_{movement_type.upper()}"
        instruction = getattr(TTSMessages, key, None)
        
        if instruction:
            return instruction
        
        # Instrucción genérica si no hay específica
        return f"Realiza el movimiento de {movement_type} de {joint_type}"
    
    @staticmethod
    def completed_result(rom_value: float, classification: str, 
                         left_rom: float = None, right_rom: float = None) -> str:
        """
        Genera mensaje de resultado personalizado.
        
        Args:
            rom_value: Valor ROM principal en grados
            classification: Clasificación del resultado
            left_rom: ROM del lado izquierdo (bilateral)
            right_rom: ROM del lado derecho (bilateral)
        """
        classification_map = {
            'Normal': 'Rango normal',
            'Limitación Leve': 'Limitación leve',
            'Limitación Moderada': 'Limitación moderada', 
            'Limitación Severa': 'Limitación severa',
            'Hipermovilidad Leve': 'Hipermovilidad leve',
            'Hipermovilidad Moderada': 'Hipermovilidad moderada',
            'Hipermovilidad Severa': 'Hipermovilidad severa',
            'INCREASED': 'Aumentado, posible hiperlaxitud',
            'OPTIMAL': 'Óptimo',
            'FUNCTIONAL': 'Funcional',
            'LIMITED': 'Limitado',
            'VERY_LIMITED': 'Muy Limitado',
            'Aumentado': 'Aumentado, posible hiperlaxitud',  # Title case from level_display
            'Optimo': 'Óptimo',                              # Title case from level_display
            'Funcional': 'Funcional',                        # Title case from level_display
            'Limitado': 'Limitado',                          # Title case from level_display
            'Muy Limitado': 'Muy Limitado',                  # Title case from level_display
            'aumentado': 'Aumentado, posible hiperlaxitud',
            'óptimo': 'Óptimo',
            'funcional': 'Funcional',
            'limitado': 'Limitado',
            'muy_limitado': 'Muy Limitado',
        }
        
        spoken_class = classification_map.get(classification, classification)
        
        # Si es bilateral, decir ambos valores
        if left_rom is not None and right_rom is not None:
            left_int = int(round(left_rom))
            right_int = int(round(right_rom))
            return f"Lado izquierdo {left_int} grados. Lado derecho {right_int} grados. {spoken_class}"
        
        # Unilateral
        rom_int = int(round(rom_value))
        return f"Rango de {rom_int} grados. {spoken_class}"
    
    @staticmethod
    def error_message(error_type: str) -> str:
        """Genera mensaje de error"""
        error_map = {
            'no_person': 'No se detecta persona',
            'wrong_orientation': 'Orientación incorrecta',
            'bad_posture': 'Ajusta tu postura',
            'timeout': 'Tiempo agotado',
            'generic': 'Ocurrió un error'
        }
        return error_map.get(error_type, error_map['generic'])


# ============================================================================
# SERVICIO TTS SINGLETON
# ============================================================================


class TTSService:
    """
    🔊 Servicio de Text-to-Speech con Edge-TTS (Singleton)
    
    Implementa patrón Singleton para garantizar una única instancia.
    Usa un hilo daemon para reproducción asíncrona.
    Utiliza Microsoft Edge TTS con voz Dalia (español México).
    
    IMPORTANTE:
    - NO crear instancia directamente, usar get_tts_service()
    - El hilo es daemon=True, muere automáticamente con Flask
    - Los analyzers NO deben usar este servicio directamente
    - Solo AnalysisSession debe llamar a speak()
    """
    
    # Singleton - única instancia
    _instance: Optional['TTSService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implementación del patrón Singleton thread-safe"""
        if cls._instance is None:
            with cls._lock:
                # Doble verificación para thread-safety
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance
    
    def __init__(self):
        """
        Inicializa el servicio TTS.
        Solo se ejecuta una vez gracias al flag _initialized.
        """
        # Evitar re-inicialización
        if self._initialized:
            return
        
        self._initialized = True
        
        # Verificar disponibilidad de módulos
        if not AUDIO_AVAILABLE:
            logger.error("[TTSService] edge-tts o pygame no instalados. TTS deshabilitado.")
            self._voice_enabled = False
            self._state = TTSState.IDLE
            self._thread = None
            return
        
        # Estado
        self._state = TTSState.IDLE
        self._voice_enabled = True
        self._pygame_initialized = False
        
        # Cola de mensajes (tamaño aumentado para manejar transiciones rápidas)
        self._message_queue: queue.Queue = queue.Queue(maxsize=15)
        
        # Control del hilo
        self._stop_event = threading.Event()
        self._skip_current = threading.Event()
        
        # Configuración de voz Edge-TTS
        self._voice_config = {
            'voice': 'es-MX-DaliaNeural',  # Voz Dalia (español México)
            'rate': '+10%',                 # Un poco más rápido para fluidez
            'volume': '+0%',                # Volumen normal
            'pitch': '+0Hz',                # Tono normal
        }
        
        # Directorio de caché para audios (persistente entre reinicios)
        self._cache_dir = Path(__file__).parent.parent / "static" / "audio_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Caché de rutas: mensaje -> ruta archivo
        self._audio_cache: Dict[str, str] = {}
        
        # Iniciar hilo worker (daemon para que muera con Flask)
        self._thread: Optional[threading.Thread] = None
        self._start_worker_thread()
        
        # Pre-generar caché de mensajes comunes (en background)
        self._cache_thread = threading.Thread(
            target=self._generate_cache,
            name="TTSCacheGenerator",
            daemon=True
        )
        self._cache_thread.start()
        
        logger.info("🔊 [TTSService] ✅ Servicio inicializado - Voz: Dalia (es-MX)")
        print("🔊 [TTSService] ✅ Servicio TTS inicializado - Voz: Dalia")  # Print directo para asegurar visibilidad
    
    def _generate_cache(self):
        """Pre-genera audios para mensajes comunes (en background)"""
        print("🔊 [TTS_CACHE] Iniciando pre-generación de caché...")
        
        # Lista de mensajes a pre-generar
        messages = [
            TTSMessages.DETECTING_PERSON,
            TTSMessages.DETECTING_RETRY,
            TTSMessages.ORIENTATION_PROFILE,
            TTSMessages.ORIENTATION_FRONTAL,
            TTSMessages.CHECKING_POSTURE,
            TTSMessages.COUNTDOWN_3,
            TTSMessages.COUNTDOWN_2,
            TTSMessages.COUNTDOWN_1,
            TTSMessages.ANALYZING_START,
            TTSMessages.COMPLETED_RELAX,
            # Instrucciones de ejercicios
            TTSMessages.INSTRUCTION_SHOULDER_FLEXION,
            TTSMessages.INSTRUCTION_SHOULDER_EXTENSION,
            TTSMessages.INSTRUCTION_SHOULDER_ABDUCTION,
            TTSMessages.INSTRUCTION_ELBOW_FLEXION,
            TTSMessages.INSTRUCTION_ELBOW_EXTENSION,
            TTSMessages.INSTRUCTION_HIP_FLEXION,
            TTSMessages.INSTRUCTION_HIP_EXTENSION,
            TTSMessages.INSTRUCTION_HIP_ABDUCTION,
            TTSMessages.INSTRUCTION_KNEE_FLEXION,
            TTSMessages.INSTRUCTION_ANKLE_DORSIFLEXION,
        ]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        generated = 0
        for msg in messages:
            audio_path = self._get_audio_path(msg)
            if os.path.exists(audio_path):
                generated += 1
                continue
            
            try:
                # Countdown numbers con rate +30% (más rápido)
                rate = "+30%" if msg in ["Tres", "Dos", "Uno"] else self._voice_config['rate']
                communicate = edge_tts.Communicate(
                    msg, 
                    self._voice_config['voice'],
                    rate=rate
                )
                loop.run_until_complete(communicate.save(audio_path))
                generated += 1
                print(f"🔊 [TTS_CACHE] ✅ '{msg[:25]}...' (rate={rate})")
            except Exception as e:
                print(f"🔊 [TTS_CACHE] ❌ Error: {msg[:20]}... -> {e}")
        
        loop.close()
        print(f"🔊 [TTS_CACHE] ✅ Caché listo: {generated}/{len(messages)} audios")
    
    def _start_worker_thread(self):
        """Inicia el hilo worker si no está corriendo"""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._worker_loop,
                name="TTSWorker",
                daemon=True  # CRÍTICO: daemon=True para que muera con Flask
            )
            self._thread.start()
            logger.debug("[TTSService] Hilo worker iniciado (daemon)")
    
    def _init_pygame_mixer(self) -> bool:
        """
        Inicializa pygame mixer para reproducción de audio.
        Lazy initialization para no bloquear el inicio de Flask.
        """
        if self._pygame_initialized:
            return True
        
        try:
            pygame.mixer.init()
            self._pygame_initialized = True
            logger.debug("[TTSService] Pygame mixer inicializado")
            return True
        except Exception as e:
            logger.error(f"[TTSService] Error inicializando pygame: {e}")
            return False
    
    def _worker_loop(self):
        """
        Loop principal del hilo worker.
        Espera mensajes en la cola y los reproduce.
        """
        logger.info("🔊 [TTSService] Worker loop INICIADO")
        print("🔊 [TTSService] Worker loop INICIADO")  # Print directo
        
        # Crear event loop para asyncio en este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while not self._stop_event.is_set():
                try:
                    # Esperar mensaje con timeout (permite verificar stop_event)
                    message = self._message_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Log cuando recibe mensaje
                logger.info(f"🔊 [TTS Worker] Recibido mensaje: '{message}'")
                print(f"🔊 [TTS Worker] Reproduciendo: '{message}'")  # Print directo
                
                # Verificar si la voz está habilitada
                if not self._voice_enabled:
                    self._message_queue.task_done()
                    continue
                
                # Reproducir mensaje
                try:
                    loop.run_until_complete(self._speak_async(message))
                    logger.info(f"🔊 [TTS Worker] Mensaje reproducido OK")
                except Exception as e:
                    logger.error(f"🔊 [TTSService] Error en speak_async: {e}")
                finally:
                    self._message_queue.task_done()
        finally:
            loop.close()
            logger.debug("[TTSService] Worker loop terminado")
    
    def _get_audio_path(self, message: str) -> str:
        """
        Genera ruta única para un mensaje (basada en hash).
        Esto permite caché persistente entre reinicios.
        """
        msg_hash = hashlib.md5(message.encode()).hexdigest()[:12]
        return str(self._cache_dir / f"tts_{msg_hash}.mp3")
    
    async def _speak_async(self, message: str):
        """
        Reproduce un mensaje usando Edge-TTS con caché.
        
        Args:
            message: Texto a reproducir
        """
        if not message or not self._voice_enabled:
            return
        
        print(f"🔊 [TTS_ASYNC] Iniciando: '{message}'")
        
        # Limpiar flag de skip
        self._skip_current.clear()
        self._state = TTSState.SPEAKING
        
        try:
            # Inicializar pygame si es necesario
            if not self._init_pygame_mixer():
                print("🔊 [TTS_ASYNC] ❌ Pygame mixer no inicializado")
                self._state = TTSState.IDLE
                return
            
            # Obtener ruta de audio (única por mensaje)
            audio_path = self._get_audio_path(message)
            
            # Verificar si ya existe en caché
            if not os.path.exists(audio_path):
                print(f"🔊 [TTS_ASYNC] Generando audio...")
                # Números de countdown con +30%, resto con config normal
                rate = "+30%" if message in ["Tres", "Dos", "Uno"] else self._voice_config['rate']
                # Generar audio con Edge-TTS
                communicate = edge_tts.Communicate(
                    message, 
                    self._voice_config['voice'],
                    rate=rate,
                    volume=self._voice_config['volume'],
                    pitch=self._voice_config['pitch']
                )
                await communicate.save(audio_path)
                print(f"🔊 [TTS_ASYNC] ✅ Audio guardado en caché (rate={rate})")
            else:
                print(f"🔊 [TTS_ASYNC] ✅ Usando audio en caché")
            
            # Verificar si se canceló durante la generación
            if self._skip_current.is_set():
                print("🔊 [TTS_ASYNC] ⚠️ Cancelado")
                self._state = TTSState.IDLE
                return
            
            # Reproducir con pygame
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Esperar a que termine (con posibilidad de cancelar)
            while pygame.mixer.music.get_busy():
                if self._skip_current.is_set():
                    pygame.mixer.music.stop()
                    print("🔊 [TTS_ASYNC] ⚠️ Reproducción cancelada")
                    break
                await asyncio.sleep(0.05)
            
            print("🔊 [TTS_ASYNC] ✅ Completado")
            
        except Exception as e:
            print(f"🔊 [TTS_ASYNC] ❌ ERROR: {type(e).__name__}: {e}")
            logger.error(f"[TTSService] Error reproduciendo: {e}")
        finally:
            self._state = TTSState.IDLE
    
    @property
    def is_speaking(self) -> bool:
        """Indica si se está reproduciendo audio actualmente."""
        return self._state == TTSState.SPEAKING
    
    @property
    def is_queue_empty(self) -> bool:
        """Indica si la cola de mensajes está vacía."""
        return self._message_queue.empty()
    
    @property
    def is_idle(self) -> bool:
        """Indica si el TTS está completamente libre (no hablando y cola vacía)."""
        return self._state == TTSState.IDLE and self._message_queue.empty()
    
    def speak(self, message: str, interrupt: bool = False):
        """
        Agrega un mensaje a la cola para ser reproducido.
        
        Por defecto, agrega a la cola SIN interrumpir mensajes anteriores.
        Si interrupt=True, cancela cualquier mensaje en reproducción.
        
        Args:
            message: Texto a reproducir
            interrupt: Si True, cancela mensaje actual y limpia cola
        """
        # Log para diagnosticar
        print(f"\n🔊 [TTS] speak() LLAMADO con mensaje: '{message}'")
        logger.info(f"🔊 [TTS] speak() llamado: '{message[:50]}...'")
        
        if not AUDIO_AVAILABLE:
            print("🔊 [TTS] ❌ AUDIO_AVAILABLE=False, no hay módulos de audio")
            logger.warning("🔊 [TTS] AUDIO_AVAILABLE=False, no hay módulos de audio")
            return
        
        if not self._voice_enabled:
            print("🔊 [TTS] ⚠️ Voz desactivada, ignorando mensaje")
            logger.info(f"🔊 [TTS] Voz desactivada, ignorando mensaje")
            return
        
        print(f"🔊 [TTS] ✅ Procesando mensaje... thread_alive={self._thread.is_alive() if self._thread else False}")
        
        # Solo interrumpir si se solicita explícitamente
        if interrupt:
            print("🔊 [TTS] ⚡ Modo INTERRUPT: cancelando mensajes anteriores")
            self._clear_queue()
            if self._state == TTSState.SPEAKING:
                self.stop_current()
        
        # Agregar nuevo mensaje
        try:
            self._message_queue.put_nowait(message)
            print(f"🔊 [TTS] ✅ Mensaje agregado a cola (queue_size={self._message_queue.qsize()})")
            logger.info(f"🔊 [TTS] Mensaje en cola: '{message}' (queue_size={self._message_queue.qsize()})")
        except queue.Full:
            logger.warning("🔊 [TTS] Cola llena, mensaje descartado")
    
    def stop_current(self):
        """
        Detiene el mensaje que se está reproduciendo actualmente.
        No detiene el hilo worker, solo el mensaje actual.
        """
        if not AUDIO_AVAILABLE:
            return
        
        self._skip_current.set()
        
        try:
            if self._pygame_initialized:
                pygame.mixer.music.stop()
        except Exception as e:
            logger.error(f"[TTSService] Error deteniendo: {e}")
        
        self._state = TTSState.IDLE
    
    def _clear_queue(self):
        """Limpia todos los mensajes pendientes en la cola"""
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
                self._message_queue.task_done()
            except queue.Empty:
                break
    
    def toggle_voice(self) -> bool:
        """
        Activa/desactiva la voz.
        
        Returns:
            bool: Nuevo estado de la voz (True=activada)
        """
        self._voice_enabled = not self._voice_enabled
        
        if not self._voice_enabled:
            self.stop_current()
            self._clear_queue()
        
        logger.info(f"[TTSService] Voz {'ACTIVADA' if self._voice_enabled else 'DESACTIVADA'}")
        return self._voice_enabled
    
    def set_voice_enabled(self, enabled: bool):
        """Establece el estado de la voz directamente"""
        if self._voice_enabled != enabled:
            self._voice_enabled = enabled
            if not enabled:
                self.stop_current()
                self._clear_queue()
            logger.info(f"[TTSService] Voz {'ACTIVADA' if enabled else 'DESACTIVADA'}")
    
    def is_voice_enabled(self) -> bool:
        """Retorna si la voz está activada"""
        return self._voice_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del servicio TTS"""
        return {
            'enabled': self._voice_enabled,
            'state': self._state.value,
            'voice': self._voice_config['voice'],
            'audio_available': AUDIO_AVAILABLE,
            'thread_alive': self._thread.is_alive() if self._thread else False,
            'queue_size': self._message_queue.qsize() if hasattr(self, '_message_queue') else 0,
        }
    
    def set_voice(self, voice_name: str):
        """Cambia la voz a usar (ej: 'es-MX-DaliaNeural')"""
        self._voice_config['voice'] = voice_name
        logger.info(f"[TTSService] Voz cambiada a: {voice_name}")
    
    def set_rate(self, rate: str):
        """Cambia la velocidad (ej: '+10%', '-20%', '+0%')"""
        self._voice_config['rate'] = rate


# ============================================================================
# FUNCIÓN GLOBAL PARA OBTENER INSTANCIA (única forma de acceder)
# ============================================================================

def get_tts_service() -> TTSService:
    """
    Obtiene la instancia singleton del servicio TTS.
    
    Returns:
        TTSService: Instancia única del servicio
    
    Ejemplo:
        tts = get_tts_service()
        tts.speak("Hola mundo")
    """
    return TTSService()


def shutdown_tts():
    """
    Apaga el servicio TTS de forma limpia.
    Normalmente no es necesario (daemon thread se cierra solo).
    """
    if TTSService._instance:
        TTSService._instance.stop_current()
        TTSService._instance._stop_event.set()
        logger.info("[TTSService] Servicio apagado")
