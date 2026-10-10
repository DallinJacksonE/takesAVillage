from service.db.mysql.provider import MySQLDB


def schema_script() -> str:
    """Return the canonical schema used by the MySQL provider."""
    return MySQLDB({})._get_schema_script()
