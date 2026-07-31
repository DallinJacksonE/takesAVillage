from service.db.mysql.provider import MySQLDB


class MySQLConnection:
    """Small connection owner used by focused MySQL repositories."""

    def __init__(self, config):
        self.provider = MySQLDB(config)

    def connect(self):
        return self.provider.get_connection()
