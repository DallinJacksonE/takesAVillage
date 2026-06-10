import os
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from sockets import ws_router, manager
from game_manager import game_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the game loop and pass it the websocket manager on startup
    asyncio.create_task(game_loop(manager))
    yield  # App runs while paused here

app = FastAPI(lifespan=lifespan)

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config.json')

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        secret_key = config_data['flask']['secret_key']
except (FileNotFoundError, KeyError):
    secret_key = 'dev_fallback_key'

# Replaces Flask-SocketIO cors_allowed_origins="*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register HTTP and WebSocket routes
app.include_router(api_router)
app.include_router(ws_router)
