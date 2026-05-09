from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .auth import UpbitCredentials, build_query_string, create_jwt
from .errors import UpbitAPIError, UpbitAuthError


DEFAULT_REST_URL = "https://api.upbit.com"


class UpbitHTTPClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_REST_URL,
        credentials: UpbitCredentials | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        auth: bool = False,
    ) -> Any:
        method = method.upper()
        clean_params = _clean_params(params)
        clean_body = _clean_params(json_body)
        query_string = build_query_string(clean_params)
        url = f"{self.base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        body_bytes = None
        headers = {
            "Accept": "application/json",
            "User-Agent": "upbitlib/0.1.0",
        }
        if clean_body is not None:
            body_bytes = json.dumps(clean_body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if auth:
            headers["Authorization"] = f"Bearer {self._jwt_for(method, clean_params, clean_body)}"

        request = Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raise _api_error_from_http_error(exc) from exc

    def _jwt_for(
        self,
        method: str,
        params: Mapping[str, Any] | None,
        json_body: Mapping[str, Any] | None,
    ) -> str:
        if self.credentials is None:
            raise UpbitAuthError("This Upbit API requires credentials.")

        query_source = json_body if method in {"POST", "PUT", "PATCH"} else params
        query_string = build_query_string(query_source)
        return create_jwt(self.credentials, query_string=query_string)


def _clean_params(params: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if params is None:
        return None
    return {key: value for key, value in params.items() if value is not None}


def _api_error_from_http_error(exc: HTTPError) -> UpbitAPIError:
    raw = exc.read()
    if not raw:
        return UpbitAPIError(exc.code, exc.reason)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return UpbitAPIError(exc.code, raw.decode("utf-8", errors="replace"))

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = error.get("message") or error.get("name") or str(payload)
    else:
        message = str(payload)
    return UpbitAPIError(exc.code, message, payload=payload)
