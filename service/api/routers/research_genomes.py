import httpx
from fastapi import APIRouter


def create_router(services):
    router = APIRouter()

    @router.get("/api/research/genomes")
    async def genomes():
        models = ["genetic"]
        if services.bot_client:
            client = services.bot_client() if callable(services.bot_client) else services.bot_client
            if hasattr(client, "fetch_models"):
                result = await client.fetch_models()
                if result:
                    models = result
        else:
            import os
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{os.environ.get('BOT_SERVICE_URL', 'http://bots:8001')}/api/models",
                        timeout=3.0)
                    if response.status_code == 200:
                        models = response.json().get("models", models)
            except Exception:
                pass
        return {"genomes": services.database.get_all_genomes(), "models": models}

    return router
