"""Compatibility FastAPI entry point for the directed-evolution service.

The supported API implementation lives in :mod:`agents.api`.
"""

from agents.api import app


def create_app():
    """Return the same application used by the Docker and ASGI entry points."""
    return app
