"""FastAPI transport factories; application state is injected by `main`."""

from service.api.dependencies import Services
from service.api.router import create_api_router

__all__ = ["Services", "create_api_router"]