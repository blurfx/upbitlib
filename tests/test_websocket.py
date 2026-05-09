import unittest

from upbitlib import build_subscription, make_channel
from upbitlib.websocket import normalize_candle_unit


class WebSocketTests(unittest.TestCase):
    def test_build_subscription_adds_ticket_channels_and_format(self) -> None:
        request = build_subscription(
            make_channel("trade", codes=["KRW-BTC"]),
            make_channel("orderbook", codes=["KRW-ETH.5"], level=10000),
            ticket="ticket-1",
            format="SIMPLE_LIST",
        )

        self.assertEqual(
            request,
            [
                {"ticket": "ticket-1"},
                {"type": "trade", "codes": ["KRW-BTC"]},
                {"type": "orderbook", "codes": ["KRW-ETH.5"], "level": 10000},
                {"format": "SIMPLE_LIST"},
            ],
        )

    def test_make_channel_keeps_false_snapshot_flag(self) -> None:
        channel = make_channel("ticker", codes=["KRW-BTC"], is_only_snapshot=False)

        self.assertEqual(channel["is_only_snapshot"], False)

    def test_normalize_candle_unit(self) -> None:
        self.assertEqual(normalize_candle_unit("candle.1s"), "1s")
        self.assertEqual(normalize_candle_unit(3), "3m")
        with self.assertRaises(ValueError):
            normalize_candle_unit("2m")


if __name__ == "__main__":
    unittest.main()
