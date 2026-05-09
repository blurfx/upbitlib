# upbitlib

Python client for the Upbit REST and WebSocket APIs.

Implemented scope follows the Upbit API overview:

- Quotation REST: trading pairs, candles, trades, tickers, orderbooks, orderbook instruments
- Quotation WebSocket: `ticker`, `trade`, `orderbook`, `candle.{unit}`
- Exchange REST: accounts and order create/test/cancel/query APIs
- Exchange WebSocket: `myAsset`, `myOrder`
- Not implemented by design: Exchange withdrawal, deposit, and service information APIs

## Setup

```bash
uv sync
```

For private Exchange APIs, set keys in `.env`:

```bash
UPBIT_ACCESS_KEY=...
UPBIT_SECRET_KEY=...
```

## REST Usage

```python
from upbitlib import UpbitClient

client = UpbitClient()

markets = client.list_trading_pairs(is_details=True)
btc_ticker = client.get_tickers(["KRW-BTC"])
minute_candles = client.get_candles_minutes(1, "KRW-BTC", count=10)
orderbook = client.get_orderbooks(["KRW-BTC"], count=15)
```

Private APIs load credentials from `.env`:

```python
from upbitlib import UpbitClient

client = UpbitClient.from_env()

accounts = client.get_accounts()
chance = client.get_order_chance("KRW-BTC")

# 실제 주문 전에는 test_order로 검증하세요.
test = client.test_order(
    "KRW-BTC",
    "bid",
    ord_type="limit",
    volume="0.0001",
    price="100000000",
)
```

## WebSocket Usage

```python
from upbitlib import UpbitClient

client = UpbitClient()

with client.subscribe_ticker(["KRW-BTC"], format="DEFAULT") as ws:
    print(ws.recv_json())
```

Private WebSocket:

```python
from upbitlib import UpbitClient

client = UpbitClient.from_env()

with client.subscribe_my_order(["KRW-BTC"], format="JSON_LIST") as ws:
    for message in ws:
        print(message)
```

## API Reference

See [REFERENCES.md](REFERENCES.md).

## Tests

```bash
uv run python -m unittest discover -s tests
```

Live integration tests are opt-in so the default suite never touches the network:

```bash
UPBIT_RUN_INTEGRATION=1 uv run python -m unittest -v tests.test_integration_upbit
```

The integration suite calls public REST/WebSocket APIs, private read-only Exchange APIs, and private WebSocket authentication. It does not create, cancel, or replace real orders. To test the safe Upbit order-test endpoint explicitly:

```bash
UPBIT_RUN_INTEGRATION=1 UPBIT_RUN_ORDER_TEST=1 uv run python -m unittest -v tests.test_integration_upbit.PrivateUpbitIntegrationTests.test_order_test_api_can_be_enabled_explicitly
```

Existing-order lookup APIs can be tested when you provide a known order id:

```bash
UPBIT_RUN_INTEGRATION=1 UPBIT_TEST_ORDER_UUID=... uv run python -m unittest -v tests.test_integration_upbit.PrivateUpbitIntegrationTests.test_specific_order_lookup_apis_can_be_enabled_with_existing_ids
```
