from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from yasar_nuri_api.api.deps import verify_api_key
from yasar_nuri_api.config.settings import Settings, get_settings

router = APIRouter(prefix="/client")


@router.get("/speech-config")
async def speech_config(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[None, Depends(verify_api_key)],
) -> dict[str, Any]:
    prov = getattr(request.app.state, "speech_config", None)
    if prov is None:
        return {
            "local_tts_enabled_default": settings.feature_local_tts_default,
            "speech_input_enabled_default": settings.feature_speech_input_default,
            "server_voice_streaming": False,
        }
    return prov.client_hints()
