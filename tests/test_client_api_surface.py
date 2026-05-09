import unittest
from unittest.mock import patch

from upbitlib import UpbitClient, UpbitCredentials
from upbitlib import client as client_module


class RecordingHTTP:
    def __init__(self) -> None:
        self.calls = []

    def request(self, method, path, *, params=None, json_body=None, auth=False):
        call = {
            "method": method,
            "path": path,
            "params": params,
            "json_body": json_body,
            "auth": auth,
        }
        self.calls.append(call)
        return call


class FakeWebSocketClient:
    instances = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.connected = False
        self.sent_json = []
        FakeWebSocketClient.instances.append(self)

    def connect(self) -> None:
        self.connected = True

    def send_json(self, value) -> None:
        self.sent_json.append(value)


class ClientAPISurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.http = RecordingHTTP()
        self.credentials = UpbitCredentials("access", "secret")
        self.client = UpbitClient(credentials=self.credentials, http_client=self.http)

    def test_all_public_rest_methods_build_expected_requests(self) -> None:
        cases = [
            (
                "list_trading_pairs",
                lambda: self.client.list_trading_pairs(is_details=True),
                "GET",
                "/v1/market/all",
                {"is_details": True},
            ),
            (
                "list_markets",
                lambda: self.client.list_markets(is_details=False),
                "GET",
                "/v1/market/all",
                {"is_details": False},
            ),
            (
                "get_candles_seconds",
                lambda: self.client.get_candles_seconds("KRW-BTC", to="2026-05-10T00:00:00", count=2),
                "GET",
                "/v1/candles/seconds",
                {"market": "KRW-BTC", "to": "2026-05-10T00:00:00", "count": 2},
            ),
            (
                "get_candles_minutes",
                lambda: self.client.get_candles_minutes(1, "KRW-BTC", to="2026-05-10T00:00:00", count=2),
                "GET",
                "/v1/candles/minutes/1",
                {"market": "KRW-BTC", "to": "2026-05-10T00:00:00", "count": 2},
            ),
            (
                "get_candles_days",
                lambda: self.client.get_candles_days(
                    "BTC-ETH",
                    to="2026-05-10T00:00:00",
                    count=2,
                    converting_price_unit="KRW",
                ),
                "GET",
                "/v1/candles/days",
                {
                    "market": "BTC-ETH",
                    "to": "2026-05-10T00:00:00",
                    "count": 2,
                    "converting_price_unit": "KRW",
                },
            ),
            (
                "get_candles_weeks",
                lambda: self.client.get_candles_weeks("KRW-BTC", count=2),
                "GET",
                "/v1/candles/weeks",
                {"market": "KRW-BTC", "to": None, "count": 2},
            ),
            (
                "get_candles_months",
                lambda: self.client.get_candles_months("KRW-BTC", count=2),
                "GET",
                "/v1/candles/months",
                {"market": "KRW-BTC", "to": None, "count": 2},
            ),
            (
                "get_candles_years",
                lambda: self.client.get_candles_years("KRW-BTC", count=2),
                "GET",
                "/v1/candles/years",
                {"market": "KRW-BTC", "to": None, "count": 2},
            ),
            (
                "get_trades_ticks",
                lambda: self.client.get_trades_ticks("KRW-BTC", count=2, cursor="cursor", days_ago=1),
                "GET",
                "/v1/trades/ticks",
                {"market": "KRW-BTC", "to": None, "count": 2, "cursor": "cursor", "days_ago": 1},
            ),
            (
                "get_tickers",
                lambda: self.client.get_tickers(["KRW-BTC", "KRW-ETH"]),
                "GET",
                "/v1/ticker",
                {"markets": "KRW-BTC,KRW-ETH"},
            ),
            (
                "get_all_tickers",
                lambda: self.client.get_all_tickers(["KRW", "BTC"]),
                "GET",
                "/v1/ticker/all",
                {"quote_currencies": "KRW,BTC"},
            ),
            (
                "get_orderbooks",
                lambda: self.client.get_orderbooks(["KRW-BTC"], level="0", count=15),
                "GET",
                "/v1/orderbook",
                {"markets": "KRW-BTC", "level": "0", "count": 15},
            ),
            (
                "get_orderbook_instruments",
                lambda: self.client.get_orderbook_instruments(["KRW-BTC", "KRW-ETH"]),
                "GET",
                "/v1/orderbook/instruments",
                {"markets": "KRW-BTC,KRW-ETH"},
            ),
        ]

        for name, invoke, method, path, params in cases:
            with self.subTest(name=name):
                call = invoke()
                self.assertEqual(call["method"], method)
                self.assertEqual(call["path"], path)
                self.assertEqual(call["params"], params)
                self.assertIsNone(call["json_body"])
                self.assertFalse(call["auth"])

    def test_all_private_rest_methods_build_expected_requests(self) -> None:
        cases = [
            (
                "get_accounts",
                lambda: self.client.get_accounts(),
                "GET",
                "/v1/accounts",
                None,
                None,
            ),
            (
                "cancel_order",
                lambda: self.client.cancel_order(uuid="order-uuid"),
                "DELETE",
                "/v1/order",
                {"uuid": "order-uuid", "identifier": None},
                None,
            ),
            (
                "cancel_orders_by_ids",
                lambda: self.client.cancel_orders_by_ids(uuids=["order-1", "order-2"]),
                "DELETE",
                "/v1/orders/uuids",
                {"uuids[]": ["order-1", "order-2"], "identifiers[]": None},
                None,
            ),
            (
                "batch_cancel_orders",
                lambda: self.client.batch_cancel_orders(
                    quote_currencies=["KRW"],
                    cancel_side="bid",
                    count=3,
                    order_by="asc",
                    exclude_pairs=["KRW-ETH"],
                ),
                "DELETE",
                "/v1/orders/open",
                {
                    "quote_currencies": "KRW",
                    "cancel_side": "bid",
                    "count": 3,
                    "order_by": "asc",
                    "pairs": None,
                    "exclude_pairs": "KRW-ETH",
                },
                None,
            ),
            (
                "get_order",
                lambda: self.client.get_order(identifier="client-order-1"),
                "GET",
                "/v1/order",
                {"uuid": None, "identifier": "client-order-1"},
                None,
            ),
            (
                "get_orders_by_ids",
                lambda: self.client.get_orders_by_ids(
                    market="KRW-BTC",
                    identifiers=["client-order-1"],
                    order_by="desc",
                ),
                "GET",
                "/v1/orders/uuids",
                {
                    "market": "KRW-BTC",
                    "uuids[]": None,
                    "identifiers[]": ["client-order-1"],
                    "order_by": "desc",
                },
                None,
            ),
            (
                "get_order_chance",
                lambda: self.client.get_order_chance("KRW-BTC"),
                "GET",
                "/v1/orders/chance",
                {"market": "KRW-BTC"},
                None,
            ),
            (
                "get_open_orders",
                lambda: self.client.get_open_orders(market="KRW-BTC", state="wait", page=1, limit=10),
                "GET",
                "/v1/orders/open",
                {
                    "market": "KRW-BTC",
                    "state": "wait",
                    "states[]": None,
                    "page": 1,
                    "limit": 10,
                    "order_by": None,
                },
                None,
            ),
            (
                "get_closed_orders",
                lambda: self.client.get_closed_orders(
                    market="KRW-BTC",
                    states=["done", "cancel"],
                    start_time="2026-05-09T00:00:00+09:00",
                    end_time="2026-05-10T00:00:00+09:00",
                    limit=10,
                    order_by="desc",
                ),
                "GET",
                "/v1/orders/closed",
                {
                    "market": "KRW-BTC",
                    "state": None,
                    "states[]": ["done", "cancel"],
                    "start_time": "2026-05-09T00:00:00+09:00",
                    "end_time": "2026-05-10T00:00:00+09:00",
                    "limit": 10,
                    "order_by": "desc",
                },
                None,
            ),
        ]

        for name, invoke, method, path, params, json_body in cases:
            with self.subTest(name=name):
                call = invoke()
                self.assertEqual(call["method"], method)
                self.assertEqual(call["path"], path)
                self.assertEqual(call["params"], params)
                self.assertEqual(call["json_body"], json_body)
                self.assertTrue(call["auth"])

    def test_order_creation_methods_build_json_bodies(self) -> None:
        create_call = self.client.create_order(
            "KRW-BTC",
            "bid",
            ord_type="limit",
            volume=0.0001,
            price=100000000,
            identifier="client-order-1",
            time_in_force="post_only",
        )
        test_call = self.client.test_order(
            "KRW-BTC",
            "ask",
            ord_type="market",
            volume="0.0001",
            smp_type="cancel_taker",
        )

        self.assertEqual(create_call["path"], "/v1/orders")
        self.assertEqual(create_call["method"], "POST")
        self.assertTrue(create_call["auth"])
        self.assertEqual(
            create_call["json_body"],
            {
                "market": "KRW-BTC",
                "side": "bid",
                "volume": "0.0001",
                "price": "100000000",
                "ord_type": "limit",
                "identifier": "client-order-1",
                "time_in_force": "post_only",
                "smp_type": None,
            },
        )

        self.assertEqual(test_call["path"], "/v1/orders/test")
        self.assertEqual(test_call["method"], "POST")
        self.assertTrue(test_call["auth"])
        self.assertEqual(
            test_call["json_body"],
            {
                "market": "KRW-BTC",
                "side": "ask",
                "volume": "0.0001",
                "price": None,
                "ord_type": "market",
                "identifier": None,
                "time_in_force": None,
                "smp_type": "cancel_taker",
            },
        )

    def test_cancel_and_new_order_builds_json_body(self) -> None:
        call = self.client.cancel_and_new_order(
            prev_order_identifier="client-order-1",
            new_ord_type="limit",
            new_volume="remain_only",
            new_price="100000000",
            new_identifier="client-order-2",
            new_time_in_force="ioc",
            new_smp_type="reduce",
        )

        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/v1/orders/cancel_and_new")
        self.assertTrue(call["auth"])
        self.assertEqual(
            call["json_body"],
            {
                "prev_order_uuid": None,
                "prev_order_identifier": "client-order-1",
                "new_ord_type": "limit",
                "new_volume": "remain_only",
                "new_price": "100000000",
                "new_identifier": "client-order-2",
                "new_time_in_force": "ioc",
                "new_smp_type": "reduce",
            },
        )

    def test_invalid_private_rest_argument_combinations_raise(self) -> None:
        with self.assertRaises(ValueError):
            self.client.cancel_order()
        with self.assertRaises(ValueError):
            self.client.cancel_orders_by_ids()
        with self.assertRaises(ValueError):
            self.client.cancel_orders_by_ids(uuids=["a"], identifiers=["b"])
        with self.assertRaises(ValueError):
            self.client.batch_cancel_orders(quote_currencies=["KRW"], pairs=["KRW-BTC"])
        with self.assertRaises(ValueError):
            self.client.cancel_and_new_order(new_ord_type="limit")
        with self.assertRaises(ValueError):
            self.client.get_order()
        with self.assertRaises(ValueError):
            self.client.get_orders_by_ids()
        with self.assertRaises(ValueError):
            self.client.get_open_orders(state="wait", states=["watch"])
        with self.assertRaises(ValueError):
            self.client.get_closed_orders(state="done", states=["cancel"])

    def test_all_websocket_helpers_build_expected_subscriptions(self) -> None:
        FakeWebSocketClient.instances = []
        credentials = self.credentials
        with patch.object(client_module, "UpbitWebSocketClient", FakeWebSocketClient):
            self.client.subscribe_ticker(["KRW-BTC"], is_only_snapshot=True, ticket="ticker-ticket")
            self.client.subscribe_trade(["KRW-BTC"], is_only_realtime=True, ticket="trade-ticket")
            self.client.subscribe_orderbook(["KRW-BTC.5"], level=10000, ticket="orderbook-ticket")
            self.client.subscribe_candle("1s", ["KRW-BTC"], ticket="candle-ticket")
            self.client.subscribe_my_asset(ticket="asset-ticket")
            self.client.subscribe_my_order(["KRW-BTC"], ticket="order-ticket", format="JSON_LIST")

        expected = [
            (
                {"private": False, "credentials": None, "timeout": 10.0},
                [{"ticket": "ticker-ticket"}, {"type": "ticker", "codes": ["KRW-BTC"], "is_only_snapshot": True}],
            ),
            (
                {"private": False, "credentials": None, "timeout": 10.0},
                [{"ticket": "trade-ticket"}, {"type": "trade", "codes": ["KRW-BTC"], "is_only_realtime": True}],
            ),
            (
                {"private": False, "credentials": None, "timeout": 10.0},
                [{"ticket": "orderbook-ticket"}, {"type": "orderbook", "codes": ["KRW-BTC.5"], "level": 10000}],
            ),
            (
                {"private": False, "credentials": None, "timeout": 10.0},
                [{"ticket": "candle-ticket"}, {"type": "candle.1s", "codes": ["KRW-BTC"]}],
            ),
            (
                {"private": True, "credentials": credentials, "timeout": 10.0},
                [{"ticket": "asset-ticket"}, {"type": "myAsset"}],
            ),
            (
                {"private": True, "credentials": credentials, "timeout": 10.0},
                [{"ticket": "order-ticket"}, {"type": "myOrder", "codes": ["KRW-BTC"]}, {"format": "JSON_LIST"}],
            ),
        ]

        self.assertEqual(len(FakeWebSocketClient.instances), len(expected))
        for instance, (kwargs, sent_json) in zip(FakeWebSocketClient.instances, expected):
            self.assertEqual(instance.kwargs, kwargs)
            self.assertTrue(instance.connected)
            self.assertEqual(instance.sent_json, [sent_json])

    def test_connect_websocket_passes_custom_timeout(self) -> None:
        FakeWebSocketClient.instances = []
        with patch.object(client_module, "UpbitWebSocketClient", FakeWebSocketClient):
            self.client.connect_websocket(
                {"type": "ticker", "codes": ["KRW-BTC"]},
                ticket="custom-ticket",
                format="DEFAULT",
                timeout=3.5,
            )

        instance = FakeWebSocketClient.instances[0]
        self.assertEqual(instance.kwargs, {"private": False, "credentials": None, "timeout": 3.5})
        self.assertEqual(
            instance.sent_json,
            [[{"ticket": "custom-ticket"}, {"type": "ticker", "codes": ["KRW-BTC"]}, {"format": "DEFAULT"}]],
        )


if __name__ == "__main__":
    unittest.main()
