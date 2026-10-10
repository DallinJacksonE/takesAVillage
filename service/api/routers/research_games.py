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
        game_getter = getattr(services.database, "get_game", None)
        game_row = game_getter(game_id) if game_getter else None
        if not game_row:
            for g in services.database.get_all_games():
                if g.get("game_id") == game_id:
                    game_row = g
                    break
        if game_row:
            return {**game_row, "visualizations": services.visualizations.ensure(
                "game", game_id, game_row)}
        raise HTTPException(status_code=404, detail="Game not found")

    return router
