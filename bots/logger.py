import logging
import os
import traceback
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(self, bot_id: str, game_id: str = None, log_dir: str = "logs"):
        self.bot_id = bot_id

        # Dynamically append the game_id as a sub-directory if provided
        if game_id:
            self.log_dir = os.path.join(log_dir, game_id)
        else:
            self.log_dir = log_dir

        # Create the nested directory tree if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        self.logger = logging.getLogger(f"BotLogger_{self.bot_id}")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if instantiated multiple times
        if not self.logger.handlers:
            self._setup_stdout_handler()
            self._setup_file_handler()
            self._setup_error_file_handler()

    def _setup_stdout_handler(self):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | [%(name)s] %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self):
        log_file = os.path.join(self.log_dir, f"{self.bot_id}_general.log")
        file_handler = TimedRotatingFileHandler(
            filename=log_file, when="M", interval=15, backupCount=672, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _setup_error_file_handler(self):
        err_file = os.path.join(self.log_dir, f"{self.bot_id}_ERRORS.log")
        err_handler = TimedRotatingFileHandler(
            filename=err_file, when="M", interval=15, backupCount=672, encoding="utf-8"
        )
        err_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s\n')
        err_handler.setFormatter(formatter)
        self.logger.addHandler(err_handler)

    # ---------------------------------------
    # PUBLIC API
    # ---------------------------------------

    def info(self, message: str):
        self.logger.info(message)

    def stdout_error(self, message: str, exception: Exception = None):
        if exception:
            self.logger.error(f"{message} | Exception: "
                              f"{exception}\n{traceback.format_exc()}")
        else:
            self.logger.error(message)

    def handled_error(self, message: str, exception: Exception = None):
        if exception:
            self.logger.warning(f"HANDLED: {message} | Exception: {exception}")
        else:
            self.logger.warning(f"HANDLED: {message}")
