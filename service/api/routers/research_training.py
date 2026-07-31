import asyncio

from fastapi import APIRouter, HTTPException

from service.api.schemas.training import CancelTrainingRequest, TrainingRequest
from service.research.training.service import TrainingConfig


def create_router(services):
    router = APIRouter()

    @router.get("/api/research/training-batches")
    async def batches():
        persisted = services.database.get_training_batches()
        persisted_ids = {item.get("batch_id") for item in persisted}
        active = []
        for session in services.training.list().get("sessions", []):
            if session.get("session_id") not in persisted_ids:
                active.append({"batch_id": session.get("session_id"),
                               "status": "running", **session})
        return {"batches": active + persisted}

    @router.get("/api/research/training-batches/{batch_id}")
    async def batch(batch_id: str):
        item = services.database.get_training_batch(batch_id)
        if not item:
            session = services.training.status(batch_id)
            if not session:
                raise HTTPException(status_code=404, detail="Training batch not found")
            item = {"batch_id": batch_id, "status": "running", **session}
        item["games"] = services.database.get_training_games(batch_id)
        return {**item, "visualizations": services.visualizations.ensure(
            "training_batch", batch_id, item)}

    @router.post("/api/research/training-batches/{batch_id}/cancel")
    async def cancel(batch_id: str, payload: CancelTrainingRequest | None = None):
        reason = payload.reason if payload else "Training cancelled by operator"
        cancelled = await services.training.cancel(batch_id, reason)
        if not cancelled and not services.database.get_training_batch(batch_id):
            raise HTTPException(status_code=404, detail="Training batch not found")
        return {"message": "Training batch cancelled", "batch_id": batch_id}

    @router.post("/api/research/training-batches/{batch_id}/rerun")
    async def rerun(batch_id: str):
        if not services.database.get_training_batch(batch_id):
            raise HTTPException(status_code=404, detail="Training batch not found")
        asyncio.create_task(services.training.rerun(batch_id))
        return {"message": "Training batch rerun initiated", "source_batch_id": batch_id}

    @router.post("/api/research/train")
    async def train(payload: TrainingRequest):
        asyncio.create_task(services.training.start(TrainingConfig(
            ruleset=payload.ruleset, bot_count=payload.botCount,
            generations=payload.generations, base_genome_id=payload.baseGenome,
            bot_model=payload.botModel, mutation_strength=payload.mutationStrength,
            mutation_rate=payload.mutationRate,
            random_immigrant_count=payload.randomImmigrantCount,
            games_per_generation=payload.gamesPerGeneration,
        )))
        return {"message": "Training sequence initiated"}

    @router.get("/api/research/training-sessions")
    async def sessions():
        return services.training.list()

    return router
