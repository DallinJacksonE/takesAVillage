from __future__ import annotations

from copy import deepcopy
from typing import Any


class TrainingSessionStore:
    def __init__(self, sessions: dict[str, dict[str, Any]] | None = None):
        self._sessions = sessions if sessions is not None else {}

    def add(self, session_id: str, session: dict[str, Any]) -> None:
        self._sessions[session_id] = session

    def get(self, session_id: str, default=None):
        return self._sessions.get(session_id, default)

    def remove(self, session_id: str):
        return self._sessions.pop(session_id, None)

    def list(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._sessions)

    def contains(self, session_id: str) -> bool:
        return session_id in self._sessions

    def _runtime_sessions(self) -> dict[str, dict[str, Any]]:
        """Return mutable state only for the owning training runtime."""
        return self._sessions
