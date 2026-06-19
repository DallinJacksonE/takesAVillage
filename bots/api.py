from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from pathlib import Path
import json
from bot_multiprocessing import spawn_bot_processes
from logger import Logger

api_router = APIRouter()
api_logger = Logger("API_ROUTER")  # Setup API-specific logger


class SpawnBotsRequest(BaseModel):
    gameId: str
    botCount: int
    botSecret: str
    botModel: str
    baseGenome: Optional[Any] = None


@api_router.post("/api/spawn_bots")
async def spawn_bots(payload: SpawnBotsRequest):
    api_logger.info(f"Received request to spawn "
                    f"{payload.botCount} bots for game {payload.gameId}")

    if payload.botCount <= 0 or payload.botCount > 100:
        api_logger.handled_error(
            f"Invalid bot count requested: {payload.botCount}")
        raise HTTPException(status_code=400, detail="Invalid bot count")

    try:
        spawn_bot_processes(
            game_id=payload.gameId,
            bot_count=payload.botCount,
            bot_secret=payload.botSecret,
            bot_model=payload.botModel,
            base_genome=payload.baseGenome
        )
        api_logger.info("Bot processes spawned successfully.")
        return {"status": "success",
                "message": f"Spawned {payload.botCount} bots"}
    except Exception as e:
        api_logger.stdout_error("Failed to spawn bot processes", exception=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/api/genomes/{game_id}")
async def get_best_genome(game_id: str):
    api_logger.info(f"Fetching best genome for game {game_id}")
    data_file = Path(__file__).resolve().parent / "bot_training_data.jsonl"
    if not data_file.exists():
        api_logger.handled_error(
            "Training data file not found during genome request.")
        raise HTTPException(
            status_code=404, detail="Training data file not found")

    best_entry = None
    with data_file.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("game_id") != game_id:
                continue
            if best_entry is None or (entry.get("fitness", 0)
                                      > best_entry.get("fitness", 0)):
                best_entry = entry

    if not best_entry:
        api_logger.info(f"No genomes found for game {game_id}")
        raise HTTPException(
            status_code=404, detail="No genomes found for that game")

    return {
        "game_id": game_id,
        "best_fitness": best_entry.get("fitness"),
        "genome": best_entry.get("genome")
    }


@api_router.get("/api/genomes/{game_id}/all")
async def get_all_genomes_for_game(game_id: str):
    data_file = Path(__file__).resolve().parent / "bot_training_data.jsonl"
    if not data_file.exists():
        raise HTTPException(
            status_code=404, detail="Training data file not found")

    entries = []
    with data_file.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("game_id") != game_id:
                continue
            entries.append(entry)

    if not entries:
        raise HTTPException(
            status_code=404, detail="No genomes found for that game")

    return {"game_id": game_id, "entries": entries}
