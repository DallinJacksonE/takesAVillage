from fastapi import APIRouter, HTTPException, Response


def create_router(services):
    router = APIRouter()

    @router.get("/api/research/visualizations/{visualization_id}")
    async def visualization(visualization_id: str):
        item = services.database.get_research_visualization(visualization_id)
        if not item:
            raise HTTPException(status_code=404, detail="Visualization not found")
        return Response(content=item["image_bytes"],
                        media_type=item.get("mime_type", "image/png"))

    return router
