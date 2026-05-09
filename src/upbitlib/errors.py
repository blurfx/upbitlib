from __future__ import annotations

from typing import Any


class UpbitError(Exception):
    """Base exception for upbitlib."""


class UpbitAuthError(UpbitError):
    """Raised when API credentials are required but unavailable."""


class UpbitAPIError(UpbitError):
    def __init__(self, status_code: int, message: str, *, payload: Any = None) -> None:
        super().__init__(f"Upbit API error {status_code}: {message}")
        self.status_code = status_code
        self.payload = payload


class UpbitWebSocketError(UpbitError):
    """Raised for WebSocket protocol or connection failures."""


class UpbitWebSocketClosed(UpbitWebSocketError):
    """Raised when the WebSocket peer closes the connection."""
