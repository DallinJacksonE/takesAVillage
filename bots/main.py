import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api import api_router
from bot_multiprocessing import (
    reap_zombies,
    process_training_data,
    training_data_queue,
    active_bot_processes
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background tasks
    reaper_task = asyncio.create_task(reap_zombies())
    aggregator_task = asyncio.create_task(
        process_training_data(training_data_queue))

    yield

    # Graceful shutdown: terminate all child processes
    reaper_task.cancel()
    aggregator_task.cancel()
    for p in active_bot_processes:
        p.terminate()
        p.join()

app = FastAPI(lifespan=lifespan)

# Mount the decoupled API routes
app.include_router(api_router)
