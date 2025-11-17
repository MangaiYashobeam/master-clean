"""
📡 CLIENT SIDE FRAME RECEIVER - CORE SERVICE
===========================================
Recibe frames enviados por el navegador del cliente y los deja disponibles para
el pipeline de análisis biomecánico.
"""

import base64
import logging
import time
from threading import Lock

import cv2
import numpy as np


logger = logging.getLogger(__name__)


class ClientFrameReceiver:
	"""Maneja la recepción y almacenamiento temporal de frames del cliente."""

	def __init__(self):
		self.current_frame = None
		self.frame_lock = Lock()
		self.last_frame_time = 0.0
		self.frame_count = 0
		self.is_active = False
		self.last_warning_time = 0.0
		self.camera_metadata = {
			'width': 0,
			'height': 0,
			'device_label': '',
			'needs_mirror': False,
		}
		self.mirror_detection_done = False

	def start_receiving(self) -> None:
		"""Activa el receptor y reinicia el contador."""
		self.is_active = True
		self.frame_count = 0
		logger.info("🎥 Client frame receiver iniciado")

	def stop_receiving(self) -> None:
		"""Detiene el receptor y limpia el frame actual."""
		self.is_active = False
		with self.frame_lock:
			self.current_frame = None
		logger.info("⏹️ Client frame receiver detenido")

	def update_camera_metadata(self, width: int, height: int, device_label: str = "") -> None:
		"""Actualiza metadata de cámara y decide si se necesita espejo."""
		self.camera_metadata.update({
			'width': width,
			'height': height,
			'device_label': device_label,
		})

		# Para uploads cliente el navegador ya entrega la imagen con orientación correcta,
		# así que evitamos invertir para no duplicar el mirror.
		self.camera_metadata['needs_mirror'] = False
		logger.info(
			"🔍 Metadata cámara recibida: %sx%s | label='%s' | mirror=%s",
			width,
			height,
			device_label,
			self.camera_metadata['needs_mirror'],
		)

	def receive_frame(self, frame_data, timestamp=None, metadata=None) -> bool:
		"""Recibe un frame codificado en base64 y lo deja disponible."""
		if not self.is_active:
			logger.warning("⚠️ Receiver no está activo")
			return False

		try:
			raw_frame = self._decode_frame(frame_data)
			if raw_frame is None:
				return False

			frame = cv2.imdecode(np.frombuffer(raw_frame, np.uint8), cv2.IMREAD_COLOR)
			if frame is None:
				logger.error("❌ cv2.imdecode devolvió None")
				return False

			frame_h, frame_w = frame.shape[:2]

			if not self.mirror_detection_done:
				device_label = metadata.get('device_label', '') if metadata else ''
				self.update_camera_metadata(frame_w, frame_h, device_label)
				self.mirror_detection_done = True

			if self.camera_metadata['needs_mirror']:
				frame = cv2.flip(frame, 1)

			with self.frame_lock:
				self.current_frame = frame
				self.last_frame_time = (timestamp / 1000.0) if timestamp else time.time()
				self.frame_count += 1

			if self.frame_count % 30 == 0:
				logger.info("✅ Frame #%s (%sx%s) recibido", self.frame_count, frame_w, frame_h)

			return True

		except Exception as exc:  # pragma: no cover - logging
			logger.error("❌ Error procesando frame del cliente: %s", exc, exc_info=True)
			return False

	def get_current_frame(self):
		"""Devuelve el frame actual si es reciente."""
		with self.frame_lock:
			if self.current_frame is None:
				return None, None

			age = time.time() - self.last_frame_time
			if age > 5.0:
				now = time.time()
				if now - self.last_warning_time > 10.0:
					logger.warning("⚠️ Frame muy viejo: %.1fs - cliente inactivo", age)
					self.last_warning_time = now
				return None, None

			return self.current_frame.copy(), self.last_frame_time

	def has_recent_frame(self, max_age_seconds: float = 2.0) -> bool:
		"""Indica si existe un frame reciente."""
		if not self.is_active:
			return False
		age = time.time() - self.last_frame_time
		return self.current_frame is not None and age <= max_age_seconds

	def get_stats(self) -> dict:
		"""Devuelve estadísticas del receptor."""
		return {
			'is_active': self.is_active,
			'frame_count': self.frame_count,
			'last_frame_age': time.time() - self.last_frame_time if self.last_frame_time else None,
		}

	def _decode_frame(self, frame_data):
		"""Decodifica el payload base64 (con o sin prefijo data:image)."""
		if isinstance(frame_data, str):
			if frame_data.startswith('data:image'):
				frame_data = frame_data.split(',', 1)[1]
			try:
				return base64.b64decode(frame_data)
			except Exception as exc:
				logger.error("❌ Error decodificando frame base64: %s", exc)
				return None
		if isinstance(frame_data, bytes):
			return frame_data
		logger.error("❌ Tipo de frame no soportado: %s", type(frame_data))
		return None


client_frame_receiver = ClientFrameReceiver()

