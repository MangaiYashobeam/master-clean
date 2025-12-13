# -*- coding: utf-8 -*-
"""
Módulo de servicios de la aplicación.
Contiene servicios singleton como TTS.
"""

from .tts_service import TTSService, get_tts_service

__all__ = ['TTSService', 'get_tts_service']
