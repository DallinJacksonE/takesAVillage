from fastapi import APIRouter, HTTPException


def create_router(services):
    router = APIRouter()

    @router.get("/api/research/games")
    async def list_games(search: str | None = None, sort: str = "time_desc"):
        games = services.database.get_all_games()
        if search:
            query = search.lower()
            games = [game for game in games if any(
                query in str(game.get(key, "")).lower()
                for key in ("game_id", "game_type", "training_batch_id")
            )]
        if sort in ("name_asc", "name_desc"):
            games = sorted(games, key=lambda game: game.get("game_id", ""),
                           reverse=sort == "name_desc")
        return games

    @router.get("/api/research/games/{game_id}")
    async def game_detail(game_id: str):
        for game in services.database.get_all_games():
            if game.get("game_id") == game_id:
                return {**game, "visualizations": services.visualizations.ensure(
                    "game", game_id, game)}
        raise HTTPException(status_code=404, detail="Game not found")

    return router
