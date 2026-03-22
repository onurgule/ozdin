from fastapi import APIRouter

from yasar_nuri_api.api.routes.v1 import admin, chat, client_config, feedback, query, sources

api_router = APIRouter(prefix="/v1")
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(query.router, tags=["query"])
api_router.include_router(sources.router, tags=["sources"])
api_router.include_router(feedback.router, tags=["feedback"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(client_config.router, tags=["client"])
