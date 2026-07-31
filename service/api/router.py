from fastapi import APIRouter

from service.api.dependencies import Services
from service.api.routers import (
    games,
    research_games,
    research_genomes,
    research_training,
    research_visualizations,
    sessions,
)


def create_api_router(services: Services) -> APIRouter:
    resolved = services
    router = APIRouter()
    for factory in (
        sessions.create_router,
        games.create_router,
        research_games.create_router,
        research_training.create_router,
        research_genomes.create_router,
        research_visualizations.create_router,
    ):
        router.include_router(factory(resolved))
    return router
