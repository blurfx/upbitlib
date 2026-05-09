from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlencode

from .errors import UpbitAuthError


ACCESS_KEY_ENV = "UPBIT_ACCESS_KEY"
SECRET_KEY_ENV = "UPBIT_SECRET_KEY"


@dataclass(frozen=True)
class UpbitCredentials:
    access_key: str
    secret_key: str

    @classmethod
    def from_env(cls, *, env_path: str | os.PathLike[str] | None = ".env") -> "UpbitCredentials":
        if env_path is not None:
            load_dotenv(env_path)

        access_key = os.getenv(ACCESS_KEY_ENV)
        secret_key = os.getenv(SECRET_KEY_ENV)
        if not access_key or not secret_key:
            raise UpbitAuthError(
                f"{ACCESS_KEY_ENV} and {SECRET_KEY_ENV} must be set. "
                "Set them in the environment or in .env."
            )
        return cls(access_key=access_key, secret_key=secret_key)


def load_dotenv(path: str | os.PathLike[str] = ".env", *, override: bool = False) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def build_query_string(params: Mapping[str, Any] | Iterable[tuple[str, Any]] | None) -> str:
    if not params:
        return ""

    items = params.items() if isinstance(params, Mapping) else params
    normalized: list[tuple[str, Any]] = []
    for key, value in items:
        if value is None:
            continue
        normalized.append((key, _normalize_query_value(value)))

    return unquote(urlencode(normalized, doseq=True))


def create_jwt(
    credentials: UpbitCredentials,
    *,
    query_string: str = "",
    nonce: str | None = None,
) -> str:
    payload: dict[str, Any] = {
        "access_key": credentials.access_key,
        "nonce": nonce or str(uuid.uuid4()),
    }
    if query_string:
        payload["query_hash"] = hashlib.sha512(query_string.encode("utf-8")).hexdigest()
        payload["query_hash_alg"] = "SHA512"

    header = {"alg": "HS512", "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url_json(header),
            _base64url_json(payload),
        ]
    )
    signature = hmac.new(
        credentials.secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha512,
    ).digest()
    return f"{signing_input}.{_base64url(signature)}"


def _base64url_json(value: Mapping[str, Any]) -> str:
    data = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _base64url(data)


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _normalize_query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return [_normalize_query_value(item) for item in value]
    return value
