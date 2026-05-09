import unittest

from upbitlib import UpbitClient, UpbitCredentials


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


class ClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.http = RecordingHTTP()
        self.client = UpbitClient(
            credentials=UpbitCredentials("access", "secret"),
            http_client=self.http,
        )

    def test_get_candles_minutes_validates_unit(self) -> None:
        with self.assertRaises(ValueError):
            self.client.get_candles_minutes(2, "KRW-BTC")

    def test_get_tickers_joins_markets(self) -> None:
        call = self.client.get_tickers(["KRW-BTC", "KRW-ETH"])

        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["path"], "/v1/ticker")
        self.assertEqual(call["params"], {"markets": "KRW-BTC,KRW-ETH"})
        self.assertFalse(call["auth"])

    def test_create_order_uses_private_json_body(self) -> None:
        call = self.client.create_order(
            "KRW-BTC",
            "bid",
            volume="0.01",
            price="100000000",
            identifier="client-order-1",
        )

        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/v1/orders")
        self.assertTrue(call["auth"])
        self.assertEqual(call["json_body"]["market"], "KRW-BTC")
        self.assertEqual(call["json_body"]["side"], "bid")
        self.assertEqual(call["json_body"]["ord_type"], "limit")
        self.assertEqual(call["json_body"]["volume"], "0.01")
        self.assertEqual(call["json_body"]["price"], "100000000")
        self.assertEqual(call["json_body"]["identifier"], "client-order-1")

    def test_open_orders_uses_states_array_key(self) -> None:
        call = self.client.get_open_orders(market="KRW-BTC", states=["wait", "watch"], limit=10)

        self.assertEqual(
            call["params"],
            {
                "market": "KRW-BTC",
                "state": None,
                "states[]": ["wait", "watch"],
                "page": None,
                "limit": 10,
                "order_by": None,
            },
        )
        self.assertTrue(call["auth"])

    def test_cancel_orders_requires_exactly_one_id_group(self) -> None:
        with self.assertRaises(ValueError):
            self.client.cancel_orders_by_ids()

        with self.assertRaises(ValueError):
            self.client.cancel_orders_by_ids(uuids=[])

        with self.assertRaises(ValueError):
            self.client.cancel_orders_by_ids(uuids=["a"], identifiers=["b"])


if __name__ == "__main__":
    unittest.main()
