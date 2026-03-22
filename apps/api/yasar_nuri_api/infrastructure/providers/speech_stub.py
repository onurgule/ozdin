from __future__ import annotations

from typing import Any

from yasar_nuri_api.config.settings import Settings
from yasar_nuri_api.infrastructure.providers.base import BaseSpeechConfigProvider


class DeviceSpeechConfigProvider(BaseSpeechConfigProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def client_hints(self) -> dict[str, Any]:
        return {
            "local_tts_enabled_default": self._settings.feature_local_tts_default,
            "speech_input_enabled_default": self._settings.feature_speech_input_default,
            "server_voice_streaming": False,
        }
