from __future__ import annotations

import logging
import os
import tempfile
import traceback
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(
            self, bot_id: str, game_id: str | None = None,
            log_dir: str = "logs"):
        self.bot_id = bot_id
        self.log_dir = self._resolve_log_dir(log_dir, game_id)

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
            filename=log_file, when="M", interval=15,
            backupCount=672, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _setup_error_file_handler(self):
        err_file = os.path.join(self.log_dir, f"{self.bot_id}_ERRORS.log")
        err_handler = TimedRotatingFileHandler(
            filename=err_file, when="M", interval=15,
            backupCount=672, encoding="utf-8"
        )
        err_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s\n')
        err_handler.setFormatter(formatter)
        self.logger.addHandler(err_handler)

    @classmethod
    def _resolve_log_dir(cls, log_dir: str, game_id: str | None = None):
        relative_dir = game_id or ""
        configured_base = os.environ.get("TAV_BOT_LOG_DIR", log_dir)
        candidates = [
            os.path.join(configured_base, relative_dir),
            os.path.join(tempfile.gettempdir(), "takesavillage-logs", "bots",
                         relative_dir),
        ]
        for candidate in candidates:
            if cls._is_writable_log_dir(candidate):
                return candidate
        raise OSError("No writable bot log directory available")

    @staticmethod
    def _is_writable_log_dir(path: str):
        try:
            os.makedirs(path, exist_ok=True)
            probe = os.path.join(path, ".write-test")
            with open(probe, "a", encoding="utf-8"):
                pass
            os.remove(probe)
            return True
        except OSError:
            return False

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
