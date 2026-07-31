import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from service.api.router import create_api_router
from service.api.websocket.game_router import create_router as create_game_ws_router
from service.api.websocket.training_router import create_router as create_training_ws_router
from service.container import AppContainer
from service.game_manager.loop import GameLoop
from service.game_manager.persistence import persist_completed_game




def create_app(database=None, start_background_tasks: bool = True) -> FastAPI:
    container = AppContainer(database)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        container.database.initialize_database()
        tasks = []
        if start_background_tasks:
            loop = GameLoop(
                registry=container.registry,
                persist_completed=lambda game: persist_completed_game(
                    container.database, game),
                broadcaster=container.connections,
                training_completion_callback=container.training.handle_game_ended,
            )
            tasks = [
                asyncio.create_task(loop.run()),
                asyncio.create_task(container.training.watchdog_loop()),
            ]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    application = FastAPI(lifespan=lifespan)
    application.state.container = container
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(create_api_router(container.api_services()))
    application.include_router(create_game_ws_router(
        container.registry, container.connections, container.database,
        container.bot_client))
    application.include_router(create_training_ws_router(
        container.training, container.training.runtime.update_hub))
    return application


app = create_app()