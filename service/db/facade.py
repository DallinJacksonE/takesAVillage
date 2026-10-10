from typing import Any


class DatabaseFacade:
    """Stable composite entry point for focused persistence providers."""

    def __init__(self, provider: Any, repositories: list[Any] | None = None):
        self.provider = provider
        self.repositories = list(repositories or [])
        is_mysql_provider = False
        if repositories is None:
            from service.db.mysql.provider import MySQLDB
            is_mysql_provider = isinstance(provider, MySQLDB)

        if is_mysql_provider:
            from service.db.mysql.games import GamesRepository
            from service.db.mysql.genomes import GenomesRepository
            from service.db.mysql.training import TrainingRepository
            from service.db.mysql.users import UsersRepository
            from service.db.mysql.visualizations import VisualizationsRepository

            self.repositories = [
                UsersRepository(provider), TrainingRepository(provider),
                GamesRepository(provider), GenomesRepository(provider),
                VisualizationsRepository(provider),
            ]

    def __getattr__(self, name: str) -> Any:
        for repository in self.repositories:
            try:
                return getattr(repository, name)
            except AttributeError:
                continue
        return getattr(self.provider, name)
