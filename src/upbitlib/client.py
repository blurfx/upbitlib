from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Mapping

from .auth import UpbitCredentials
from .http import UpbitHTTPClient
from .websocket import (
    UpbitWebSocketClient,
    build_subscription,
    make_channel,
    normalize_candle_unit,
)


MINUTE_UNITS = {1, 3, 5, 10, 15, 30, 60, 240}


class UpbitClient:
    def __init__(
        self,
        *,
        credentials: UpbitCredentials | None = None,
        http_client: UpbitHTTPClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.credentials = credentials
        self.http = http_client or UpbitHTTPClient(credentials=credentials, timeout=timeout)

    @classmethod
    def from_env(cls, *, env_path: str | None = ".env", timeout: float = 10.0) -> "UpbitClient":
        credentials = UpbitCredentials.from_env(env_path=env_path)
        return cls(credentials=credentials, timeout=timeout)

    def list_trading_pairs(self, *, is_details: bool | None = None) -> Any:
        return self.http.request("GET", "/v1/market/all", params={"is_details": is_details})

    list_markets = list_trading_pairs

    def get_candles_seconds(
        self,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
    ) -> Any:
        return self.http.request(
            "GET",
            "/v1/candles/seconds",
            params={"market": market, "to": to, "count": count},
        )

    def get_candles_minutes(
        self,
        unit: int,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
    ) -> Any:
        if unit not in MINUTE_UNITS:
            raise ValueError(f"unit must be one of {sorted(MINUTE_UNITS)}")
        return self.http.request(
            "GET",
            f"/v1/candles/minutes/{unit}",
            params={"market": market, "to": to, "count": count},
        )

    def get_candles_days(
        self,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
        converting_price_unit: str | None = None,
    ) -> Any:
        return self.http.request(
            "GET",
            "/v1/candles/days",
            params={
                "market": market,
                "to": to,
                "count": count,
                "converting_price_unit": converting_price_unit,
            },
        )

    def get_candles_weeks(
        self,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
    ) -> Any:
        return self._get_period_candles("weeks", market, to=to, count=count)

    def get_candles_months(
        self,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
    ) -> Any:
        return self._get_period_candles("months", market, to=to, count=count)

    def get_candles_years(
        self,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
    ) -> Any:
        return self._get_period_candles("years", market, to=to, count=count)

    def get_trades_ticks(
        self,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
        cursor: str | None = None,
        days_ago: int | None = None,
    ) -> Any:
        return self.http.request(
            "GET",
            "/v1/trades/ticks",
            params={
                "market": market,
                "to": to,
                "count": count,
                "cursor": cursor,
                "days_ago": days_ago,
            },
        )

    def get_tickers(self, markets: str | Sequence[str]) -> Any:
        return self.http.request("GET", "/v1/ticker", params={"markets": _csv(markets)})

    def get_all_tickers(self, quote_currencies: str | Sequence[str]) -> Any:
        return self.http.request(
            "GET",
            "/v1/ticker/all",
            params={"quote_currencies": _csv(quote_currencies)},
        )

    def get_orderbooks(
        self,
        markets: str | Sequence[str],
        *,
        level: str | int | None = None,
        count: int | None = None,
    ) -> Any:
        return self.http.request(
            "GET",
            "/v1/orderbook",
            params={"markets": _csv(markets), "level": level, "count": count},
        )

    def get_orderbook_instruments(self, markets: str | Sequence[str]) -> Any:
        return self.http.request(
            "GET",
            "/v1/orderbook/instruments",
            params={"markets": _csv(markets)},
        )

    def get_accounts(self) -> Any:
        return self.http.request("GET", "/v1/accounts", auth=True)

    def create_order(
        self,
        market: str,
        side: str,
        *,
        ord_type: str = "limit",
        volume: str | float | None = None,
        price: str | float | None = None,
        identifier: str | None = None,
        time_in_force: str | None = None,
        smp_type: str | None = None,
    ) -> Any:
        return self.http.request(
            "POST",
            "/v1/orders",
            json_body=_order_body(
                market=market,
                side=side,
                volume=volume,
                price=price,
                ord_type=ord_type,
                identifier=identifier,
                time_in_force=time_in_force,
                smp_type=smp_type,
            ),
            auth=True,
        )

    def test_order(
        self,
        market: str,
        side: str,
        *,
        ord_type: str = "limit",
        volume: str | float | None = None,
        price: str | float | None = None,
        identifier: str | None = None,
        time_in_force: str | None = None,
        smp_type: str | None = None,
    ) -> Any:
        return self.http.request(
            "POST",
            "/v1/orders/test",
            json_body=_order_body(
                market=market,
                side=side,
                volume=volume,
                price=price,
                ord_type=ord_type,
                identifier=identifier,
                time_in_force=time_in_force,
                smp_type=smp_type,
            ),
            auth=True,
        )

    def cancel_order(self, *, uuid: str | None = None, identifier: str | None = None) -> Any:
        _require_any("uuid or identifier", uuid, identifier)
        return self.http.request(
            "DELETE",
            "/v1/order",
            params={"uuid": uuid, "identifier": identifier},
            auth=True,
        )

    def cancel_orders_by_ids(
        self,
        *,
        uuids: Sequence[str] | None = None,
        identifiers: Sequence[str] | None = None,
    ) -> Any:
        _require_exactly_one("uuids or identifiers", uuids, identifiers)
        return self.http.request(
            "DELETE",
            "/v1/orders/uuids",
            params={"uuids[]": uuids, "identifiers[]": identifiers},
            auth=True,
        )

    def batch_cancel_orders(
        self,
        *,
        quote_currencies: str | Sequence[str] | None = None,
        cancel_side: str | None = None,
        count: int | None = None,
        order_by: str | None = None,
        pairs: str | Sequence[str] | None = None,
        exclude_pairs: str | Sequence[str] | None = None,
    ) -> Any:
        if quote_currencies is not None and pairs is not None:
            raise ValueError("quote_currencies and pairs cannot be used together")
        return self.http.request(
            "DELETE",
            "/v1/orders/open",
            params={
                "quote_currencies": _csv_or_none(quote_currencies),
                "cancel_side": cancel_side,
                "count": count,
                "order_by": order_by,
                "pairs": _csv_or_none(pairs),
                "exclude_pairs": _csv_or_none(exclude_pairs),
            },
            auth=True,
        )

    def cancel_and_new_order(
        self,
        *,
        new_ord_type: str,
        prev_order_uuid: str | None = None,
        prev_order_identifier: str | None = None,
        new_volume: str | float | None = None,
        new_price: str | float | None = None,
        new_identifier: str | None = None,
        new_time_in_force: str | None = None,
        new_smp_type: str | None = None,
    ) -> Any:
        _require_any("prev_order_uuid or prev_order_identifier", prev_order_uuid, prev_order_identifier)
        return self.http.request(
            "POST",
            "/v1/orders/cancel_and_new",
            json_body={
                "prev_order_uuid": prev_order_uuid,
                "prev_order_identifier": prev_order_identifier,
                "new_ord_type": new_ord_type,
                "new_volume": _string_or_none(new_volume),
                "new_price": _string_or_none(new_price),
                "new_identifier": new_identifier,
                "new_time_in_force": new_time_in_force,
                "new_smp_type": new_smp_type,
            },
            auth=True,
        )

    def get_order(self, *, uuid: str | None = None, identifier: str | None = None) -> Any:
        _require_any("uuid or identifier", uuid, identifier)
        return self.http.request(
            "GET",
            "/v1/order",
            params={"uuid": uuid, "identifier": identifier},
            auth=True,
        )

    def get_orders_by_ids(
        self,
        *,
        market: str | None = None,
        uuids: Sequence[str] | None = None,
        identifiers: Sequence[str] | None = None,
        order_by: str | None = None,
    ) -> Any:
        _require_exactly_one("uuids or identifiers", uuids, identifiers)
        return self.http.request(
            "GET",
            "/v1/orders/uuids",
            params={
                "market": market,
                "uuids[]": uuids,
                "identifiers[]": identifiers,
                "order_by": order_by,
            },
            auth=True,
        )

    def get_order_chance(self, market: str) -> Any:
        return self.http.request(
            "GET",
            "/v1/orders/chance",
            params={"market": market},
            auth=True,
        )

    def get_open_orders(
        self,
        *,
        market: str | None = None,
        state: str | None = None,
        states: Sequence[str] | None = None,
        page: int | None = None,
        limit: int | None = None,
        order_by: str | None = None,
    ) -> Any:
        if state is not None and states is not None:
            raise ValueError("state and states cannot be used together")
        return self.http.request(
            "GET",
            "/v1/orders/open",
            params={
                "market": market,
                "state": state,
                "states[]": states,
                "page": page,
                "limit": limit,
                "order_by": order_by,
            },
            auth=True,
        )

    def get_closed_orders(
        self,
        *,
        market: str | None = None,
        state: str | None = None,
        states: Sequence[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int | None = None,
        order_by: str | None = None,
    ) -> Any:
        if state is not None and states is not None:
            raise ValueError("state and states cannot be used together")
        return self.http.request(
            "GET",
            "/v1/orders/closed",
            params={
                "market": market,
                "state": state,
                "states[]": states,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
                "order_by": order_by,
            },
            auth=True,
        )

    def connect_websocket(
        self,
        *channels: Mapping[str, Any],
        private: bool = False,
        ticket: str | None = None,
        format: str | None = None,
        timeout: float = 10.0,
    ) -> UpbitWebSocketClient:
        websocket = UpbitWebSocketClient(
            private=private,
            credentials=self.credentials if private else None,
            timeout=timeout,
        )
        websocket.connect()
        websocket.send_json(build_subscription(*channels, ticket=ticket, format=format))
        return websocket

    def subscribe_ticker(
        self,
        codes: Sequence[str],
        *,
        is_only_snapshot: bool | None = None,
        is_only_realtime: bool | None = None,
        format: str | None = None,
        ticket: str | None = None,
    ) -> UpbitWebSocketClient:
        return self.connect_websocket(
            make_channel(
                "ticker",
                codes=codes,
                is_only_snapshot=is_only_snapshot,
                is_only_realtime=is_only_realtime,
            ),
            ticket=ticket,
            format=format,
        )

    def subscribe_trade(
        self,
        codes: Sequence[str],
        *,
        is_only_snapshot: bool | None = None,
        is_only_realtime: bool | None = None,
        format: str | None = None,
        ticket: str | None = None,
    ) -> UpbitWebSocketClient:
        return self.connect_websocket(
            make_channel(
                "trade",
                codes=codes,
                is_only_snapshot=is_only_snapshot,
                is_only_realtime=is_only_realtime,
            ),
            ticket=ticket,
            format=format,
        )

    def subscribe_orderbook(
        self,
        codes: Sequence[str],
        *,
        level: str | int | float | None = None,
        is_only_snapshot: bool | None = None,
        is_only_realtime: bool | None = None,
        format: str | None = None,
        ticket: str | None = None,
    ) -> UpbitWebSocketClient:
        return self.connect_websocket(
            make_channel(
                "orderbook",
                codes=codes,
                level=level,
                is_only_snapshot=is_only_snapshot,
                is_only_realtime=is_only_realtime,
            ),
            ticket=ticket,
            format=format,
        )

    def subscribe_candle(
        self,
        unit: str | int,
        codes: Sequence[str],
        *,
        is_only_snapshot: bool | None = None,
        is_only_realtime: bool | None = None,
        format: str | None = None,
        ticket: str | None = None,
    ) -> UpbitWebSocketClient:
        return self.connect_websocket(
            make_channel(
                f"candle.{normalize_candle_unit(unit)}",
                codes=codes,
                is_only_snapshot=is_only_snapshot,
                is_only_realtime=is_only_realtime,
            ),
            ticket=ticket,
            format=format,
        )

    def subscribe_my_asset(
        self,
        *,
        format: str | None = None,
        ticket: str | None = None,
    ) -> UpbitWebSocketClient:
        return self.connect_websocket(
            make_channel("myAsset"),
            private=True,
            ticket=ticket,
            format=format,
        )

    def subscribe_my_order(
        self,
        codes: Sequence[str] | None = None,
        *,
        format: str | None = None,
        ticket: str | None = None,
    ) -> UpbitWebSocketClient:
        return self.connect_websocket(
            make_channel("myOrder", codes=codes),
            private=True,
            ticket=ticket,
            format=format,
        )

    def _get_period_candles(
        self,
        period: str,
        market: str,
        *,
        to: str | None = None,
        count: int | None = None,
    ) -> Any:
        return self.http.request(
            "GET",
            f"/v1/candles/{period}",
            params={"market": market, "to": to, "count": count},
        )


def _csv(value: str | Sequence[str]) -> str:
    if isinstance(value, str):
        return value
    return ",".join(value)


def _csv_or_none(value: str | Sequence[str] | None) -> str | None:
    if value is None:
        return None
    return _csv(value)


def _order_body(
    *,
    market: str,
    side: str,
    volume: str | float | None,
    price: str | float | None,
    ord_type: str,
    identifier: str | None,
    time_in_force: str | None,
    smp_type: str | None,
) -> dict[str, Any]:
    return {
        "market": market,
        "side": side,
        "volume": _string_or_none(volume),
        "price": _string_or_none(price),
        "ord_type": ord_type,
        "identifier": identifier,
        "time_in_force": time_in_force,
        "smp_type": smp_type,
    }


def _string_or_none(value: str | float | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _require_any(name: str, *values: object) -> None:
    if not any(_has_value(value) for value in values):
        raise ValueError(f"{name} is required")


def _require_exactly_one(name: str, *values: object) -> None:
    count = sum(_has_value(value) for value in values)
    if count != 1:
        raise ValueError(f"exactly one of {name} is required")


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value != ""
    if isinstance(value, Sequence):
        return len(value) > 0
    return True
