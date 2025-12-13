"""
🔌 ARDUINO SERIAL - Comunicación Serial Thread-Safe con Arduino Nano
====================================================================
Gestiona la comunicación serial con Arduino Nano para control de altura de cámara.

CARACTERÍSTICAS:
- Patrón Singleton (solo una instancia en toda la aplicación)
- Thread-safe con locks para acceso concurrente
- Conexión lazy (solo se conecta cuando se necesita)
- No bloquea el hilo principal de Flask
- Manejo robusto de errores de conexión y timeouts
- Reconexión automática si se pierde la conexión

PROTOCOLO DE COMUNICACIÓN:
- Envío: "comando.valor\n"
  - "0.X" → Ir a posición inicial (mínima)
  - "1.XXX" → Ir a altura XXX mm (ej: "1.1200" = 120cm)
  - "2.X" → Detener motor
  - "STATUS" → Solicitar estado actual
  
- Recepción: "STATUS,codigo,altura\n"
  - codigo 0: OK (operación completada)
  - codigo 1: Moviendo
  - codigo 2: Error de altura (fuera de rango)
  - codigo 3: Fin de carrera desconectado
  - codigo 4: Timeout durante movimiento

Autor: BIOTRACK Team
Fecha: 2025-12-01
"""

import threading
import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum

# pyserial es requerido - agregar a requirements.txt si no está
try:
    import serial  # type: ignore
    import serial.tools.list_ports  # type: ignore
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None  # type: ignore

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS Y DATACLASSES
# ============================================================================

class ArduinoStatus(IntEnum):
    """Códigos de estado del Arduino (deben coincidir con camera_height_control.ino)"""
    OK = 0                    # Operación completada exitosamente
    MOVING = 1                # Motor en movimiento
    HEIGHT_ERROR = 2          # Altura solicitada fuera de rango
    LIMIT_SWITCH_ERROR = 3    # Fin de carrera desconectado
    TIMEOUT = 4               # Timeout durante movimiento


@dataclass
class ArduinoResponse:
    """Respuesta parseada del Arduino"""
    status: ArduinoStatus
    current_height_mm: int
    raw_response: str
    success: bool
    error_message: Optional[str] = None


# ============================================================================
# CLASE SINGLETON PARA COMUNICACIÓN SERIAL
# ============================================================================

class ArduinoSerial:
    """
    Singleton thread-safe para comunicación serial con Arduino Nano.
    
    Esta clase gestiona la conexión única con el Arduino que controla
    el motor de altura de cámara.
    
    Uso básico:
        from hardware.arduino_serial import arduino_serial
        
        # Conectar (si no está conectado)
        arduino_serial.connect()
        
        # Mover a altura
        response = arduino_serial.move_to_height(1200)  # 120cm
        
        # Verificar resultado
        if response.success:
            print(f"Cámara en {response.current_height_mm}mm")
        
        # Desconectar (opcional, se hace automáticamente al cerrar la app)
        arduino_serial.disconnect()
    """
    
    _instance: Optional['ArduinoSerial'] = None
    _lock = threading.Lock()
    
    # Configuración por defecto
    # NOTA: Cambiar DEFAULT_PORT si el Arduino está en otro puerto
    # Puedes verificar el puerto en Administrador de Dispositivos > Puertos (COM & LPT)
    DEFAULT_PORT = 'COM10'  # Puerto típico para Arduino Nano con CH340
    DEFAULT_BAUDRATE = 115200
    READ_TIMEOUT = 2.0        # Segundos para timeout de lectura
    COMMAND_TIMEOUT = 35.0    # Segundos para esperar que el motor complete movimiento
    ARDUINO_RESET_DELAY = 2.0 # Segundos a esperar después de conectar (Arduino se reinicia)
    
    # Palabras clave para auto-detectar Arduino en los puertos
    ARDUINO_KEYWORDS = ['CH340', 'CH341', 'Arduino', 'USB-SERIAL', 'FTDI']
    
    def __new__(cls):
        """Implementación del patrón Singleton"""
        if cls._instance is None:
            with cls._lock:
                # Doble verificación para thread-safety
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicialización (solo se ejecuta una vez)"""
        if self._initialized:
            return
        
        self._serial = None  # Optional[serial.Serial] - inicializado como None
        self._serial_lock = threading.Lock()
        self._connected = False
        self._port = self.DEFAULT_PORT
        self._baudrate = self.DEFAULT_BAUDRATE
        self._last_known_height = 0  # Última altura conocida (para evitar comandos innecesarios)
        self._stop_requested = False  # Flag para interrumpir comandos en curso
        
        self._initialized = True
        logger.info("ArduinoSerial: Singleton inicializado")
    
    # ========================================================================
    # CONEXIÓN Y DESCONEXIÓN
    # ========================================================================
    
    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> Tuple[bool, str]:
        """
        Conecta con el Arduino.
        
        Si no se especifica puerto, intenta auto-detectar el Arduino.
        
        Args:
            port: Puerto COM (ej: 'COM10'). Si es None, intenta auto-detectar.
            baudrate: Velocidad (default: 115200)
            
        Returns:
            tuple: (éxito, mensaje)
        """
        if not SERIAL_AVAILABLE:
            return False, "Módulo pyserial no instalado. Ejecute: pip install pyserial"
        
        with self._serial_lock:
            if self._connected and self._serial and self._serial.is_open:
                return True, f"Ya conectado en {self._port}"
            
            # Auto-detectar puerto si no se especifica
            if port is None:
                detected_port = self.auto_detect_arduino_port()
                if detected_port:
                    port = detected_port
                    logger.info(f"ArduinoSerial: Puerto auto-detectado: {port}")
                else:
                    port = self._port  # Usar puerto por defecto
                    logger.info(f"ArduinoSerial: No se detectó Arduino, usando puerto por defecto: {port}")
            
            baudrate = baudrate or self._baudrate
            
            try:
                logger.info(f"ArduinoSerial: Conectando a {port} @ {baudrate} baudios...")
                
                self._serial = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=self.READ_TIMEOUT
                )
                
                # Esperar a que Arduino se reinicie (hace reset al abrir puerto serial)
                logger.debug(f"ArduinoSerial: Esperando {self.ARDUINO_RESET_DELAY}s para reset de Arduino...")
                time.sleep(self.ARDUINO_RESET_DELAY)
                
                # Limpiar buffers
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
                
                self._connected = True
                self._port = port
                
                # Enviar comando HOME (0.0) y ESPERAR a que termine
                logger.info("ArduinoSerial: Enviando comando HOME automático y esperando...")
                self._serial.write(b"0.0\n")
                
                # Esperar respuesta del HOME (máximo 30 segundos)
                home_timeout = 30.0
                start_time = time.time()
                home_completed = False
                
                while time.time() - start_time < home_timeout:
                    if self._serial.in_waiting:
                        line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                        logger.debug(f"ArduinoSerial: Respuesta HOME: '{line}'")
                        
                        # Buscar respuesta con formato "codigo,altura"
                        if "," in line:
                            parts = line.split(",")
                            if len(parts) == 2:
                                try:
                                    codigo = int(parts[0])
                                    altura = int(parts[1])
                                    self._last_known_height = altura
                                    # codigo 0 = OK, HOME completado
                                    if codigo == 0:
                                        home_completed = True
                                        logger.info(f"ArduinoSerial: HOME completado, altura: {altura}mm")
                                        break
                                except ValueError:
                                    pass
                    else:
                        time.sleep(0.1)  # Pequeña pausa para no saturar CPU
                
                if home_completed:
                    logger.info(f"ArduinoSerial: ✅ Conectado en {port} - HOME completado")
                    return True, f"Conectado en {port} - Posición inicial OK"
                else:
                    logger.warning(f"ArduinoSerial: ✅ Conectado en {port} - HOME timeout (puede seguir moviéndose)")
                    return True, f"Conectado en {port} - Inicializando..."
                
            except serial.SerialException as e:
                logger.error(f"ArduinoSerial: Error de conexión en {port}: {e}")
                self._connected = False
                return False, f"Error de conexión: {e}"
            except Exception as e:
                logger.error(f"ArduinoSerial: Error inesperado: {e}")
                self._connected = False
                return False, f"Error inesperado: {e}"
    
    def disconnect(self) -> Tuple[bool, str]:
        """
        Desconecta del Arduino.
        
        Returns:
            tuple: (éxito, mensaje)
        """
        with self._serial_lock:
            if not self._connected or not self._serial:
                return True, "No estaba conectado"
            
            try:
                self._serial.close()
                self._connected = False
                logger.info("ArduinoSerial: Desconectado")
                return True, "Desconectado correctamente"
            except Exception as e:
                logger.error(f"ArduinoSerial: Error al desconectar: {e}")
                self._connected = False
                return False, f"Error al desconectar: {e}"
    
    def is_connected(self) -> bool:
        """Verifica si está conectado y el puerto está abierto"""
        with self._serial_lock:
            return (
                self._connected and 
                self._serial is not None and 
                self._serial.is_open
            )
    
    def is_connected_fast(self) -> bool:
        """
        Verificación rápida de conexión SIN usar lock.
        Usar solo para STOP u operaciones que no pueden esperar.
        """
        return (
            self._connected and 
            self._serial is not None and 
            self._serial.is_open
        )
    
    # ========================================================================
    # ENVÍO DE COMANDOS
    # ========================================================================
    
    def _send_command(self, command: str, wait_for_completion: bool = True) -> ArduinoResponse:
        """
        Envía un comando al Arduino y espera respuesta.
        
        Args:
            command: Comando a enviar (ej: "1.1200" para ir a 1200mm)
            wait_for_completion: Si True, espera hasta que el movimiento termine
            
        Returns:
            ArduinoResponse con el resultado
        """
        # Resetear flag de stop al iniciar comando
        self._stop_requested = False
        
        # Respuesta de error por defecto
        error_response = ArduinoResponse(
            status=ArduinoStatus.OK,
            current_height_mm=self._last_known_height,
            raw_response="",
            success=False
        )
        
        if not self.is_connected():
            error_response.error_message = "No conectado al Arduino"
            return error_response
        
        try:
            with self._serial_lock:
                # Limpiar buffers COMPLETAMENTE antes de enviar
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
                time.sleep(0.05)  # Pequeña pausa para asegurar limpieza
                
                # Enviar comando con terminador de línea
                cmd_bytes = f"{command}\n".encode('utf-8')
                self._serial.write(cmd_bytes)
                self._serial.flush()  # Asegurar que se envió
                logger.debug(f"ArduinoSerial: Comando enviado: '{command}'")
                
                # Esperar y procesar respuestas
                start_time = time.time()
                last_response = None
                timeout = self.COMMAND_TIMEOUT if wait_for_completion else self.READ_TIMEOUT
                
                while time.time() - start_time < timeout:
                    # IMPORTANTE: Verificar si se solicitó STOP
                    if self._stop_requested:
                        logger.info("ArduinoSerial: Comando interrumpido por STOP")
                        return ArduinoResponse(
                            status=ArduinoStatus.OK,
                            current_height_mm=self._last_known_height,
                            raw_response="INTERRUPTED",
                            success=True,  # El STOP es exitoso
                            error_message="Interrumpido por STOP"
                        )
                    
                    if self._serial.in_waiting:
                        line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                        
                        if not line:
                            continue
                        
                        logger.debug(f"ArduinoSerial: Respuesta: '{line}'")
                        
                        # Ignorar mensajes READY
                        if line == "READY":
                            continue
                        
                        # Parsear respuesta de estado (formato: "codigo,altura")
                        if "," in line:
                            last_response = self._parse_status(line)
                            
                            # Guardar última altura conocida
                            if last_response.current_height_mm > 0:
                                self._last_known_height = last_response.current_height_mm
                            
                            # Si no esperamos completar, retornar primera respuesta
                            if not wait_for_completion:
                                return last_response
                            
                            # Si el código es 0 (OK), el movimiento terminó
                            if last_response.status == ArduinoStatus.OK:
                                return last_response
                    
                    time.sleep(0.02)  # Polling rápido
                
                # Timeout alcanzado
                if last_response:
                    if last_response.status != ArduinoStatus.OK:
                        last_response.error_message = "Timeout esperando fin de movimiento"
                    return last_response
                
                # No se recibió ninguna respuesta válida
                error_response.status = ArduinoStatus.TIMEOUT
                error_response.error_message = "Timeout: No se recibió respuesta del Arduino"
                return error_response
                
        except serial.SerialException as e:
            logger.error(f"ArduinoSerial: Error de comunicación: {e}")
            self._connected = False
            error_response.error_message = f"Error de comunicación: {e}"
            return error_response
        except Exception as e:
            logger.error(f"ArduinoSerial: Error inesperado: {e}")
            error_response.error_message = f"Error inesperado: {e}"
            return error_response
    
    def _parse_status(self, response: str) -> ArduinoResponse:
        """
        Parsea respuesta del Arduino.
        
        Formato del Arduino original: "codigo,altura"
        Ejemplo: "0,1200" = OK, altura actual 1200mm
        
        También acepta formato extendido: "STATUS,codigo,altura"
        """
        try:
            parts = response.split(",")
            
            # Formato original del Arduino: "codigo,altura" (2 partes)
            if len(parts) == 2:
                status_code = int(parts[0])
                height = int(parts[1])
                
                return ArduinoResponse(
                    status=ArduinoStatus(status_code) if status_code <= 4 else ArduinoStatus.OK,
                    current_height_mm=height,
                    raw_response=response,
                    success=(status_code == 0)
                )
            
            # Formato extendido: "STATUS,codigo,altura" (3 partes)
            elif len(parts) >= 3 and parts[0].upper() == "STATUS":
                status_code = int(parts[1])
                height = int(parts[2])
                
                return ArduinoResponse(
                    status=ArduinoStatus(status_code) if status_code <= 4 else ArduinoStatus.OK,
                    current_height_mm=height,
                    raw_response=response,
                    success=(status_code == 0)
                )
                
        except (ValueError, IndexError) as e:
            logger.error(f"ArduinoSerial: Error parseando respuesta '{response}': {e}")
        
        return ArduinoResponse(
            status=ArduinoStatus.OK,
            current_height_mm=0,
            raw_response=response,
            success=False,
            error_message=f"Respuesta no válida: {response}"
        )
    
    # ========================================================================
    # COMANDOS DE ALTO NIVEL
    # ========================================================================
    
    def move_to_height(self, height_mm: int) -> ArduinoResponse:
        """
        Mueve la cámara a la altura especificada.
        
        Args:
            height_mm: Altura objetivo en milímetros (200-1700)
            
        Returns:
            ArduinoResponse con el resultado del movimiento
        """
        # Validar rango antes de enviar
        if not (200 <= height_mm <= 1700):
            return ArduinoResponse(
                status=ArduinoStatus.HEIGHT_ERROR,
                current_height_mm=0,
                raw_response="",
                success=False,
                error_message=f"Altura fuera de rango válido (200-1700mm): {height_mm}mm"
            )
        
        logger.info(f"ArduinoSerial: Moviendo cámara a {height_mm}mm...")
        command = f"1.{height_mm}"
        return self._send_command(command, wait_for_completion=True)
    
    def go_to_initial_position(self) -> ArduinoResponse:
        """
        Mueve la cámara a la posición inicial (altura mínima).
        
        Returns:
            ArduinoResponse con el resultado
        """
        logger.info("ArduinoSerial: Moviendo a posición inicial...")
        return self._send_command("0.0", wait_for_completion=True)
    
    def stop(self) -> ArduinoResponse:
        """
        Detiene el movimiento del motor INMEDIATAMENTE.
        
        CRÍTICO: Este método NO usa locks ni verificaciones que bloqueen.
        Solo escribe "2.0\n" al puerto y lee la respuesta con la altura.
        
        Returns:
            ArduinoResponse con el resultado y altura actual
        """
        # Activar flag para interrumpir _send_command si está corriendo
        self._stop_requested = True
        
        try:
            # Verificación directa SIN lock
            if self._serial and self._serial.is_open:
                # Limpiar buffer de entrada antes de enviar
                self._serial.reset_input_buffer()
                
                # Escribir directamente - igual que en monitor serie
                self._serial.write(b"2.0\n")
                logger.info("ArduinoSerial: ⏹️ STOP enviado")
                
                # Esperar para que Arduino procese STOP y envíe altura
                import time
                time.sleep(0.3)  # 300ms para que Arduino detenga motor y mida
                
                current_height = self._last_known_height
                
                # Intentar leer la respuesta del Arduino (puede haber múltiples líneas)
                attempts = 0
                while self._serial.in_waiting > 0 and attempts < 5:
                    attempts += 1
                    try:
                        response_line = self._serial.readline().decode('utf-8').strip()
                        if response_line:
                            logger.debug(f"ArduinoSerial: STOP respuesta #{attempts}: '{response_line}'")
                            parsed = self._parse_status(response_line)
                            if parsed.current_height_mm > 0:
                                current_height = parsed.current_height_mm
                                self._last_known_height = current_height
                                logger.info(f"ArduinoSerial: STOP - altura actual: {current_height}mm")
                    except Exception as e:
                        logger.debug(f"ArduinoSerial: No se pudo leer respuesta STOP: {e}")
                
                return ArduinoResponse(
                    status=ArduinoStatus.OK,
                    current_height_mm=current_height,
                    raw_response="STOP",
                    success=True
                )
            else:
                return ArduinoResponse(
                    status=ArduinoStatus.OK,
                    current_height_mm=0,
                    raw_response="",
                    success=False,
                    error_message="Puerto no disponible"
                )
        except Exception as e:
            logger.error(f"ArduinoSerial: Error en STOP: {e}")
            return ArduinoResponse(
                status=ArduinoStatus.OK,
                current_height_mm=0,
                raw_response="",
                success=False,
                error_message=str(e)
            )
    
    def get_status(self) -> ArduinoResponse:
        """
        Obtiene el estado actual del sistema.
        
        IMPORTANTE: Este método NO envía comandos al Arduino para evitar
        interferir con operaciones en curso. Retorna la última altura conocida.
        
        Returns:
            ArduinoResponse con la información actual
        """
        # Retornar última altura conocida sin enviar comandos
        return ArduinoResponse(
            status=ArduinoStatus.OK,
            current_height_mm=self._last_known_height,
            raw_response="cached",
            success=True
        )
    
    def query_status(self) -> ArduinoResponse:
        """
        Consulta activamente el estado al Arduino (envía comando STOP).
        
        Usar solo cuando se necesite actualizar la altura real.
        PRECAUCIÓN: Esto detendrá cualquier movimiento en curso.
        
        Returns:
            ArduinoResponse con la información actual
        """
        return self._send_command("2.0", wait_for_completion=False)
    
    def get_current_height(self) -> Tuple[int, bool]:
        """
        Obtiene la última altura conocida de la cámara (sin enviar comandos).
        
        Returns:
            tuple: (altura_mm, éxito)
        """
        return self._last_known_height, self._last_known_height > 0
    
    def get_last_known_height(self) -> int:
        """
        Obtiene la última altura conocida.
        
        Returns:
            int: Altura en mm
        """
        return self._last_known_height
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    @staticmethod
    def list_available_ports() -> list:
        """
        Lista los puertos COM disponibles en el sistema.
        
        Returns:
            Lista de diccionarios con información de cada puerto
        """
        if not SERIAL_AVAILABLE:
            return []
        
        ports = serial.tools.list_ports.comports()
        return [
            {
                "port": p.device,
                "description": p.description,
                "manufacturer": p.manufacturer or "N/A",
                "is_arduino": any(kw in (p.description or '') for kw in ArduinoSerial.ARDUINO_KEYWORDS)
            } 
            for p in ports
        ]
    
    @staticmethod
    def auto_detect_arduino_port() -> Optional[str]:
        """
        Intenta auto-detectar el puerto del Arduino basándose en la descripción.
        
        Busca puertos con chips típicos de Arduino: CH340, CH341, FTDI, etc.
        
        Returns:
            Nombre del puerto (ej: 'COM10') o None si no se encuentra
        """
        if not SERIAL_AVAILABLE:
            return None
        
        ports = serial.tools.list_ports.comports()
        for p in ports:
            description = (p.description or '').upper()
            for keyword in ArduinoSerial.ARDUINO_KEYWORDS:
                if keyword.upper() in description:
                    logger.info(f"Arduino auto-detectado en {p.device}: {p.description}")
                    return p.device
        
        return None
    
    def get_connection_info(self) -> dict:
        """
        Obtiene información sobre la conexión actual.
        
        Returns:
            Diccionario con información de la conexión
        """
        return {
            "connected": self.is_connected(),
            "port": self._port if self._connected else None,
            "baudrate": self._baudrate,
            "serial_available": SERIAL_AVAILABLE
        }


# ============================================================================
# INSTANCIA SINGLETON GLOBAL
# ============================================================================

# Esta es la instancia que deben importar otros módulos
arduino_serial = ArduinoSerial()
