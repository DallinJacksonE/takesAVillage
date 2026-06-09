from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from bot_multiprocessing import spawn_bot_processes

api_router = APIRouter()


class SpawnBotsRequest(BaseModel):
    gameId: str
    botCount: int
    botSecret: str
    baseGenome: Optional[dict] = None


@api_router.post("/api/spawn_bots")
async def spawn_bots(payload: SpawnBotsRequest):
    if payload.botCount <= 0 or payload.botCount > 100:
        raise HTTPException(status_code=400, detail="Invalid bot count")

    # Pass the sanitized payload over to the process manager
    spawn_bot_processes(
        game_id=payload.gameId,
        bot_count=payload.botCount,
        bot_secret=payload.botSecret,
        base_genome=payload.baseGenome
    )

    return {"status": "success", "message": f"Spawned {payload.botCount} bots"}
