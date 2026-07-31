from service.db.contracts import DatabaseProvider
from service.db.facade import DatabaseFacade
from service.db.factory import get_database, load_config
from service.db.memory import InMemoryDB
from service.db.mysql import MySQLDB

# Default provider for the production application. Tests and app factories inject
# their own provider instead.
db = get_database()

__all__ = [
    "DatabaseFacade", "DatabaseProvider", "InMemoryDB", "MySQLDB", "db",
    "get_database", "load_config",
]
