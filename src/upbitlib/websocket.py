from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import uuid
from collections.abc import Iterable, Sequence
from typing import Any, Mapping
from urllib.parse import urlparse

from .auth import UpbitCredentials, create_jwt
from .errors import UpbitAuthError, UpbitWebSocketClosed, UpbitWebSocketError


PUBLIC_WEBSOCKET_URL = "wss://api.upbit.com/websocket/v1"
PRIVATE_WEBSOCKET_URL = "wss://api.upbit.com/websocket/v1/private"
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
FORMAT_VALUES = {"DEFAULT", "SIMPLE", "JSON_LIST", "SIMPLE_LIST"}
CANDLE_UNITS = {"1s", "1m", "3m", "5m", "10m", "15m", "30m", "60m", "240m"}


class UpbitWebSocketClient:
    def __init__(
        self,
        *,
        url: str | None = None,
        private: bool = False,
        credentials: UpbitCredentials | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.url = url or (PRIVATE_WEBSOCKET_URL if private else PUBLIC_WEBSOCKET_URL)
        self.private = private
        self.credentials = credentials
        self.timeout = timeout
        self._socket: ssl.SSLSocket | socket.socket | None = None

    def __enter__(self) -> "UpbitWebSocketClient":
        if self._socket is None:
            self.connect()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def __iter__(self) -> Iterable[Any]:
        while True:
            yield self.recv_json()

    def connect(self) -> None:
        if self._socket is not None:
            return

        parsed = urlparse(self.url)
        if parsed.scheme != "wss":
            raise UpbitWebSocketError("Only wss:// WebSocket URLs are supported")
        if self.private and self.credentials is None:
            raise UpbitAuthError("Private Upbit WebSocket requires credentials")

        host = parsed.hostname
        if host is None:
            raise UpbitWebSocketError(f"Invalid WebSocket URL: {self.url}")
        port = parsed.port or 443
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        raw_socket = socket.create_connection((host, port), timeout=self.timeout)
        context = ssl.create_default_context()
        self._socket = context.wrap_socket(raw_socket, server_hostname=host)

        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            f"GET {path} HTTP/1.1",
            f"Host: {host}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
            "User-Agent: upbitlib/0.1.0",
        ]
        if self.private:
            headers.append(f"Authorization: Bearer {create_jwt(self.credentials)}")
        headers.extend(["", ""])
        self._send_raw("\r\n".join(headers).encode("ascii"))

        response = self._read_http_response()
        _validate_handshake_response(response, key)

    def send_json(self, value: Any) -> None:
        self.send_text(json.dumps(value, separators=(",", ":"), ensure_ascii=False))

    def send_text(self, value: str) -> None:
        self._send_frame(value.encode("utf-8"), opcode=0x1)

    def ping(self, payload: bytes = b"") -> None:
        self._send_frame(payload, opcode=0x9)

    def pong(self, payload: bytes = b"") -> None:
        self._send_frame(payload, opcode=0xA)

    def recv_json(self) -> Any:
        raw = self.recv()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def recv(self) -> str | bytes:
        while True:
            opcode, payload = self._recv_frame()
            if opcode == 0x1:
                return payload.decode("utf-8")
            if opcode == 0x2:
                return payload
            if opcode == 0x8:
                self.close()
                raise UpbitWebSocketClosed("WebSocket connection closed by peer")
            if opcode == 0x9:
                self.pong(payload)
                continue
            if opcode == 0xA:
                continue

    def close(self) -> None:
        if self._socket is None:
            return
        try:
            self._send_frame(b"", opcode=0x8)
        except OSError:
            pass
        try:
            self._socket.close()
        finally:
            self._socket = None

    def _send_frame(self, payload: bytes, *, opcode: int) -> None:
        mask = os.urandom(4)
        first = 0x80 | opcode
        length = len(payload)
        if length < 126:
            header = struct.pack("!BB", first, 0x80 | length)
        elif length <= 0xFFFF:
            header = struct.pack("!BBH", first, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", first, 0x80 | 127, length)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self._send_raw(header + mask + masked)

    def _recv_frame(self) -> tuple[int, bytes]:
        header = self._read_exact(2)
        first, second = header
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]

        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length) if length else b""
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, payload

    def _read_http_response(self) -> bytes:
        chunks = bytearray()
        while b"\r\n\r\n" not in chunks:
            chunk = self._read_exact(1)
            chunks.extend(chunk)
            if len(chunks) > 64_000:
                raise UpbitWebSocketError("WebSocket handshake response is too large")
        return bytes(chunks)

    def _read_exact(self, size: int) -> bytes:
        if self._socket is None:
            raise UpbitWebSocketError("WebSocket is not connected")
        chunks = bytearray()
        while len(chunks) < size:
            chunk = self._socket.recv(size - len(chunks))
            if not chunk:
                raise UpbitWebSocketClosed("WebSocket connection closed")
            chunks.extend(chunk)
        return bytes(chunks)

    def _send_raw(self, data: bytes) -> None:
        if self._socket is None:
            raise UpbitWebSocketError("WebSocket is not connected")
        self._socket.sendall(data)


def build_subscription(
    *channels: Mapping[str, Any],
    ticket: str | None = None,
    format: str | None = None,
) -> list[dict[str, Any]]:
    if not channels:
        raise ValueError("at least one WebSocket channel is required")
    if format is not None and format not in FORMAT_VALUES:
        raise ValueError(f"format must be one of {sorted(FORMAT_VALUES)}")

    request = [{"ticket": ticket or str(uuid.uuid4())}]
    request.extend(dict(channel) for channel in channels)
    if format is not None:
        request.append({"format": format})
    return request


def make_channel(
    type: str,
    *,
    codes: Sequence[str] | None = None,
    level: str | int | float | None = None,
    is_only_snapshot: bool | None = None,
    is_only_realtime: bool | None = None,
) -> dict[str, Any]:
    channel: dict[str, Any] = {"type": type}
    if codes is not None:
        channel["codes"] = list(codes)
    if level is not None:
        channel["level"] = level
    if is_only_snapshot is not None:
        channel["is_only_snapshot"] = is_only_snapshot
    if is_only_realtime is not None:
        channel["is_only_realtime"] = is_only_realtime
    return channel


def normalize_candle_unit(unit: str | int) -> str:
    if isinstance(unit, int):
        unit = f"{unit}m"
    else:
        unit = unit.removeprefix("candle.")
    if unit not in CANDLE_UNITS:
        raise ValueError(f"unit must be one of {sorted(CANDLE_UNITS)}")
    return unit


def _validate_handshake_response(response: bytes, key: str) -> None:
    text = response.decode("iso-8859-1")
    lines = text.split("\r\n")
    if not lines or " 101 " not in lines[0]:
        raise UpbitWebSocketError(f"WebSocket handshake failed: {lines[0] if lines else text}")

    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.lower()] = value.strip()

    expected_accept = base64.b64encode(hashlib.sha1((key + WEBSOCKET_GUID).encode("ascii")).digest())
    actual_accept = headers.get("sec-websocket-accept", "").encode("ascii")
    if actual_accept != expected_accept:
        raise UpbitWebSocketError("WebSocket handshake returned an invalid accept key")
