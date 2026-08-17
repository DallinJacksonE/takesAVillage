from __future__ import annotations

import logging
import os
import sys
import tempfile
import traceback
from logging.handlers import TimedRotatingFileHandler


class BackendLogger:
    def __init__(self, component: str, game_id: str | None = None):
        self.component = component
        self.game_id = game_id
        self.log_dir = self._resolve_log_dir(component, game_id)

        # Name the logger uniquely so handlers don't overlap in memory
        logger_name = f"{component}_{game_id}" if game_id else component
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        # Format: Time | Component | Level | Message
        formatter = logging.Formatter(
            '%(asctime)s | [%(name)s] %(levelname)s: %(message)s'
        )

        # 1. Stdout Handler (Console)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 2. General File Handler (15 min rotation, 7 days backup)
        log_file = os.path.join(self.log_dir, f"{self.component}_general.log")
        file_handler = TimedRotatingFileHandler(
            filename=log_file, when="M", interval=15,
            backupCount=672, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 3. Dedicated Error File Handler
        err_file = os.path.join(self.log_dir, f"{self.component}_error.log")
        err_handler = TimedRotatingFileHandler(
            filename=err_file, when="M", interval=15,
            backupCount=672, encoding="utf-8"
        )
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(formatter)
        self.logger.addHandler(err_handler)

    @classmethod
    def _resolve_log_dir(cls, component: str, game_id: str | None = None):
        relative_dir = cls._relative_log_dir(component, game_id)
        configured_base = os.environ.get("TAV_LOG_DIR", "logs")
        candidates = [
            os.path.join(configured_base, relative_dir),
            os.path.join(tempfile.gettempdir(), "takesavillage-logs", relative_dir),
        ]
        for candidate in candidates:
            if cls._is_writable_log_dir(candidate):
                return candidate
        raise OSError("No writable log directory available")

    @staticmethod
    def _relative_log_dir(component: str, game_id: str | None = None):
        if component == "game" and game_id:
            return os.path.join("games", game_id)
        if component in ["api", "ws", "db", "orchestrator"]:
            return component
        return "system"

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

    # --- Public API ---

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str, exc: Exception = None):
        if exc:
            self.logger.error(f"{message} | Exception: "
                              f"{exc}\n{traceback.format_exc()}")
        else:
            self.logger.error(message)

    def exception(self, message: str):
        # Natively logs the traceback of an active exception
        self.logger.exception(message)

# --- Global Unhandled Exception Catcher ---


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Catch fatal crashes and dump them into the system error log
    crash_logger = BackendLogger("system")
    crash_logger.logger.critical(
        "UNHANDLED SYSTEM EXCEPTION",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = handle_unhandled_exception
