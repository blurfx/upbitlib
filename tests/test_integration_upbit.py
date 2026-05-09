import os
import unittest

from upbitlib import UpbitAPIError, UpbitClient, UpbitCredentials, load_dotenv


RUN_INTEGRATION = os.getenv("UPBIT_RUN_INTEGRATION") == "1"
RUN_ORDER_TEST = os.getenv("UPBIT_RUN_ORDER_TEST") == "1"
TEST_MARKET = os.getenv("UPBIT_TEST_MARKET", "KRW-BTC")
TEST_QUOTE = os.getenv("UPBIT_TEST_QUOTE", "KRW")


@unittest.skipUnless(RUN_INTEGRATION, "set UPBIT_RUN_INTEGRATION=1 to run live Upbit integration tests")
class PublicUpbitIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = UpbitClient(timeout=10)

    def test_all_public_rest_apis_return_expected_shapes(self) -> None:
        checks = [
            ("list_trading_pairs", lambda: self.client.list_trading_pairs(is_details=True), list),
            ("get_candles_seconds", lambda: self.client.get_candles_seconds(TEST_MARKET, count=1), list),
            ("get_candles_minutes", lambda: self.client.get_candles_minutes(1, TEST_MARKET, count=1), list),
            ("get_candles_days", lambda: self.client.get_candles_days(TEST_MARKET, count=1), list),
            ("get_candles_weeks", lambda: self.client.get_candles_weeks(TEST_MARKET, count=1), list),
            ("get_candles_months", lambda: self.client.get_candles_months(TEST_MARKET, count=1), list),
            ("get_candles_years", lambda: self.client.get_candles_years(TEST_MARKET, count=1), list),
            ("get_trades_ticks", lambda: self.client.get_trades_ticks(TEST_MARKET, count=1), list),
            ("get_tickers", lambda: self.client.get_tickers([TEST_MARKET]), list),
            ("get_all_tickers", lambda: self.client.get_all_tickers([TEST_QUOTE]), list),
            ("get_orderbooks", lambda: self.client.get_orderbooks([TEST_MARKET], count=5), list),
            ("get_orderbook_instruments", lambda: self.client.get_orderbook_instruments([TEST_MARKET]), list),
        ]

        for name, invoke, expected_type in checks:
            with self.subTest(name=name):
                result = invoke()
                self.assertIsInstance(result, expected_type)

    def test_public_websocket_snapshot_apis_receive_messages(self) -> None:
        checks = [
            ("ticker", lambda: self.client.subscribe_ticker([TEST_MARKET], is_only_snapshot=True, ticket="it-ticker")),
            ("trade", lambda: self.client.subscribe_trade([TEST_MARKET], is_only_snapshot=True, ticket="it-trade")),
            (
                "orderbook",
                lambda: self.client.subscribe_orderbook([TEST_MARKET], is_only_snapshot=True, ticket="it-orderbook"),
            ),
            (
                "candle",
                lambda: self.client.subscribe_candle("1s", [TEST_MARKET], is_only_snapshot=True, ticket="it-candle"),
            ),
        ]

        for expected_type, connect in checks:
            with self.subTest(type=expected_type):
                ws = connect()
                try:
                    message = ws.recv_json()
                finally:
                    ws.close()

                if isinstance(message, list):
                    self.assertGreater(len(message), 0)
                    message = message[0]
                self.assertEqual(message["type"], expected_type if expected_type != "candle" else "candle.1s")


@unittest.skipUnless(RUN_INTEGRATION, "set UPBIT_RUN_INTEGRATION=1 to run live Upbit integration tests")
class PrivateUpbitIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv(".env")
        try:
            credentials = UpbitCredentials.from_env(env_path=None)
        except Exception as exc:
            raise unittest.SkipTest(f"missing Upbit credentials: {exc}") from exc
        cls.client = UpbitClient(credentials=credentials, timeout=10)

    def test_private_read_only_exchange_apis_return_expected_shapes(self) -> None:
        checks = [
            ("get_accounts", lambda: self.client.get_accounts(), list),
            ("get_order_chance", lambda: self.client.get_order_chance(TEST_MARKET), dict),
            ("get_open_orders", lambda: self.client.get_open_orders(market=TEST_MARKET, limit=1), list),
            ("get_closed_orders", lambda: self.client.get_closed_orders(market=TEST_MARKET, limit=1), list),
        ]

        for name, invoke, expected_type in checks:
            with self.subTest(name=name):
                result = invoke()
                self.assertIsInstance(result, expected_type)

    def test_order_test_api_can_be_enabled_explicitly(self) -> None:
        if not RUN_ORDER_TEST:
            self.skipTest("set UPBIT_RUN_ORDER_TEST=1 to validate the order test endpoint")

        result = self.client.test_order(
            TEST_MARKET,
            "bid",
            ord_type="limit",
            volume=os.getenv("UPBIT_TEST_ORDER_VOLUME", "0.0001"),
            price=os.getenv("UPBIT_TEST_ORDER_PRICE", "100000000"),
            identifier=os.getenv("UPBIT_TEST_ORDER_IDENTIFIER"),
        )
        self.assertIsInstance(result, dict)

    def test_specific_order_lookup_apis_can_be_enabled_with_existing_ids(self) -> None:
        uuid = os.getenv("UPBIT_TEST_ORDER_UUID")
        identifier = os.getenv("UPBIT_TEST_ORDER_IDENTIFIER")
        if not uuid and not identifier:
            self.skipTest("set UPBIT_TEST_ORDER_UUID or UPBIT_TEST_ORDER_IDENTIFIER for live order lookup tests")

        if uuid:
            self.assertIsInstance(self.client.get_order(uuid=uuid), dict)
            self.assertIsInstance(self.client.get_orders_by_ids(uuids=[uuid]), list)
        if identifier:
            self.assertIsInstance(self.client.get_order(identifier=identifier), dict)
            self.assertIsInstance(self.client.get_orders_by_ids(identifiers=[identifier]), list)

    def test_private_websocket_authenticates_and_subscribes(self) -> None:
        # myAsset/myOrder only emit data when account assets or orders change. This test
        # proves authentication and subscription by accepting a short idle timeout.
        for name, connect in [
            ("myAsset", lambda: self.client.subscribe_my_asset(ticket="it-my-asset")),
            ("myOrder", lambda: self.client.subscribe_my_order(ticket="it-my-order")),
        ]:
            with self.subTest(name=name):
                ws = connect()
                try:
                    ws.ping()
                except (TimeoutError, UpbitAPIError):
                    raise
                finally:
                    ws.close()


if __name__ == "__main__":
    unittest.main()
