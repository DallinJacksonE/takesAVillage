import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api import api_router
from logger import Logger
from bot_multiprocessing import (
    reap_zombies,
    process_training_data,
    training_data_queue,
    active_bot_processes
)

main_logger = Logger("MAIN_SERVER")


@asynccontextmanager
async def lifespan(app: FastAPI):
    main_logger.info("Starting Bot Server background tasks...")
    reaper_task = asyncio.create_task(reap_zombies())
    aggregator_task = asyncio.create_task(
        process_training_data(training_data_queue))

    yield

    main_logger.info(
        "Shutting down Bot Server. Terminating active child processes...")
    reaper_task.cancel()
    aggregator_task.cancel()
    for p in active_bot_processes:
        p.terminate()
        p.join()
    main_logger.info("Shutdown complete.")

app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
