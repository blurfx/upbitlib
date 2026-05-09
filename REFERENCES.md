# upbitlib API Reference

이 문서는 `upbitlib.UpbitClient`로 구현된 업비트 API별 호출 함수, 입력 데이터, 반환값을 정리합니다.

구현 범위:

- Quotation REST 전체
- Quotation WebSocket 전체
- Exchange 자산/주문 REST
- Exchange 내 자산/내 주문 WebSocket

구현 제외:

- Exchange 출금 API
- Exchange 입금 API
- Exchange 서비스 정보 API

## 공통

### 클라이언트 생성

인증이 필요 없는 Quotation API:

```python
from upbitlib import UpbitClient

client = UpbitClient()
```

인증이 필요한 Exchange API:

```python
from upbitlib import UpbitClient

client = UpbitClient.from_env()
```

`.env` 또는 환경변수에는 다음 이름을 사용합니다.

```bash
UPBIT_ACCESS_KEY=...
UPBIT_SECRET_KEY=...
```

### 반환값과 예외

- REST 함수는 업비트 응답 JSON을 그대로 파이썬 `dict` 또는 `list[dict]`로 디코딩해 반환합니다.
- WebSocket 함수는 연결된 `UpbitWebSocketClient`를 반환합니다. `ws.recv_json()`으로 메시지를 받습니다.
- HTTP 오류는 `UpbitAPIError`로 발생하며 `status_code`, `payload` 속성을 가집니다.
- 잘못된 인자 조합은 `ValueError`로 발생합니다.

## Quotation REST API

### 페어 목록 조회

Upbit API: `GET /v1/market/all`

함수:

```python
client.list_trading_pairs(is_details=True)
client.list_markets(is_details=True)  # alias
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `is_details` | `bool \| None` | 선택 | `True`면 시장 경보/이벤트 상세 정보를 포함합니다. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "korean_name": "비트코인",
        "english_name": "Bitcoin",
        "market_warning": "NONE",
        "market_event": {...}
    }
]
```

### 초 캔들 조회

Upbit API: `GET /v1/candles/seconds`

함수:

```python
client.get_candles_seconds("KRW-BTC", to=None, count=1)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str` | 필수 | 페어 코드. 예: `"KRW-BTC"` |
| `to` | `str \| None` | 선택 | 마지막 캔들 시각. 업비트가 지원하는 날짜 문자열을 전달합니다. |
| `count` | `int \| None` | 선택 | 조회 개수. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "candle_date_time_utc": "2026-05-09T15:00:00",
        "candle_date_time_kst": "2026-05-10T00:00:00",
        "opening_price": 100000000.0,
        "high_price": 100100000.0,
        "low_price": 99900000.0,
        "trade_price": 100050000.0,
        "timestamp": 1770000000000,
        "candle_acc_trade_price": 123456789.0,
        "candle_acc_trade_volume": 1.2345
    }
]
```

### 분 캔들 조회

Upbit API: `GET /v1/candles/minutes/{unit}`

함수:

```python
client.get_candles_minutes(1, "KRW-BTC", to=None, count=10)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `unit` | `int` | 필수 | `1`, `3`, `5`, `10`, `15`, `30`, `60`, `240` 중 하나. |
| `market` | `str` | 필수 | 페어 코드. |
| `to` | `str \| None` | 선택 | 마지막 캔들 시각. |
| `count` | `int \| None` | 선택 | 조회 개수. |

응답:

`list[dict]`

초 캔들과 같은 OHLCV 필드를 반환하며 `unit` 필드가 포함될 수 있습니다.

### 일 캔들 조회

Upbit API: `GET /v1/candles/days`

함수:

```python
client.get_candles_days("KRW-BTC", to=None, count=10, converting_price_unit=None)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str` | 필수 | 페어 코드. |
| `to` | `str \| None` | 선택 | 마지막 캔들 시각. |
| `count` | `int \| None` | 선택 | 조회 개수. |
| `converting_price_unit` | `str \| None` | 선택 | 예: `"KRW"`. 종가 환산 필드를 요청합니다. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "candle_date_time_utc": "...",
        "candle_date_time_kst": "...",
        "opening_price": ...,
        "high_price": ...,
        "low_price": ...,
        "trade_price": ...,
        "prev_closing_price": ...,
        "change_price": ...,
        "change_rate": ...,
        "converted_trade_price": ...
    }
]
```

`converted_trade_price`는 환산 통화를 요청했을 때만 올 수 있습니다.

### 주/월/연 캔들 조회

Upbit API:

- `GET /v1/candles/weeks`
- `GET /v1/candles/months`
- `GET /v1/candles/years`

함수:

```python
client.get_candles_weeks("KRW-BTC", to=None, count=10)
client.get_candles_months("KRW-BTC", to=None, count=10)
client.get_candles_years("KRW-BTC", to=None, count=10)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str` | 필수 | 페어 코드. |
| `to` | `str \| None` | 선택 | 마지막 캔들 시각. |
| `count` | `int \| None` | 선택 | 조회 개수. |

응답:

`list[dict]`

일 캔들과 같은 OHLCV 계열 필드를 반환합니다. 주/월/연 단위에 따라 기준 시각만 달라집니다.

### 페어 체결 이력 조회

Upbit API: `GET /v1/trades/ticks`

함수:

```python
client.get_trades_ticks("KRW-BTC", to=None, count=10, cursor=None, days_ago=None)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str` | 필수 | 페어 코드. |
| `to` | `str \| None` | 선택 | 마지막 체결 시각. |
| `count` | `int \| None` | 선택 | 조회 개수. |
| `cursor` | `str \| None` | 선택 | 페이지 커서. |
| `days_ago` | `int \| None` | 선택 | 며칠 전 체결까지 조회할지 지정. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "trade_date_utc": "2026-05-09",
        "trade_time_utc": "15:00:00",
        "timestamp": 1770000000000,
        "trade_price": 100000000.0,
        "trade_volume": 0.01,
        "prev_closing_price": 99000000.0,
        "change_price": 1000000.0,
        "ask_bid": "BID",
        "sequential_id": 17700000000000000
    }
]
```

### 페어 단위 현재가 조회

Upbit API: `GET /v1/ticker`

함수:

```python
client.get_tickers(["KRW-BTC", "KRW-ETH"])
client.get_tickers("KRW-BTC")
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `markets` | `str \| Sequence[str]` | 필수 | 하나 또는 여러 페어 코드. 리스트는 콤마 문자열로 변환됩니다. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "trade_date": "20260509",
        "trade_time": "150000",
        "trade_price": 100000000.0,
        "prev_closing_price": 99000000.0,
        "change": "RISE",
        "change_price": 1000000.0,
        "change_rate": 0.01010101,
        "signed_change_price": 1000000.0,
        "signed_change_rate": 0.01010101,
        "acc_trade_price": 123456789.0,
        "acc_trade_volume": 12.345,
        "highest_52_week_price": ...,
        "lowest_52_week_price": ...,
        "timestamp": 1770000000000
    }
]
```

### 마켓 단위 현재가 조회

Upbit API: `GET /v1/ticker/all`

함수:

```python
client.get_all_tickers(["KRW", "BTC"])
client.get_all_tickers("KRW")
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `quote_currencies` | `str \| Sequence[str]` | 필수 | 호가 통화. 예: `"KRW"`, `["KRW", "BTC"]` |

응답:

`list[dict]`

각 원소는 `get_tickers()`와 같은 현재가 필드들을 포함합니다.

### 호가 정보 조회

Upbit API: `GET /v1/orderbook`

함수:

```python
client.get_orderbooks(["KRW-BTC"], level=None, count=30)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `markets` | `str \| Sequence[str]` | 필수 | 하나 또는 여러 페어 코드. |
| `level` | `str \| int \| None` | 선택 | KRW 마켓 호가 모아보기 단위. 예: `"100000"` |
| `count` | `int \| None` | 선택 | 호가 개수. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "timestamp": 1770000000000,
        "total_ask_size": 1.23,
        "total_bid_size": 2.34,
        "orderbook_units": [
            {
                "ask_price": 100001000.0,
                "bid_price": 100000000.0,
                "ask_size": 0.1,
                "bid_size": 0.2
            }
        ],
        "level": 0
    }
]
```

### 호가 정책 조회

Upbit API: `GET /v1/orderbook/instruments`

함수:

```python
client.get_orderbook_instruments(["KRW-BTC"])
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `markets` | `str \| Sequence[str]` | 필수 | 하나 또는 여러 페어 코드. |

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "market": "KRW-BTC",
        "quote_currency": "KRW",
        "tick_size": "1000",
        "supported_levels": ["0", "10000", "100000"]
    }
]
```

## Exchange REST API

Exchange REST API는 `client = UpbitClient.from_env()`로 생성한 인증 클라이언트가 필요합니다.

### 계정 잔고 조회

Upbit API: `GET /v1/accounts`

함수:

```python
client.get_accounts()
```

입력: 없음

응답:

`list[dict]`

대표 필드:

```python
[
    {
        "currency": "KRW",
        "balance": "1000000.0",
        "locked": "0.0",
        "avg_buy_price": "0",
        "avg_buy_price_modified": True,
        "unit_currency": "KRW"
    }
]
```

### 주문 생성

Upbit API: `POST /v1/orders`

함수:

```python
client.create_order(
    "KRW-BTC",
    "bid",
    ord_type="limit",
    volume="0.0001",
    price="100000000",
    identifier="client-order-1",
    time_in_force=None,
    smp_type=None,
)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str` | 필수 | 페어 코드. |
| `side` | `str` | 필수 | `"bid"` 매수 또는 `"ask"` 매도. |
| `ord_type` | `str` | 필수 | `"limit"`, `"price"`, `"market"`, `"best"`. 기본값 `"limit"`. |
| `volume` | `str \| float \| None` | 주문 유형별 | 주문 수량. 문자열로 전송됩니다. |
| `price` | `str \| float \| None` | 주문 유형별 | 주문 가격 또는 시장가 매수 총액. 문자열로 전송됩니다. |
| `identifier` | `str \| None` | 선택 | 사용자 지정 주문 ID. |
| `time_in_force` | `str \| None` | 선택 | `"ioc"`, `"fok"`, `"post_only"`. |
| `smp_type` | `str \| None` | 선택 | `"cancel_maker"`, `"cancel_taker"`, `"reduce"`. |

주문 유형별 대표 입력:

| 유형 | `side` | `ord_type` | 필요한 값 |
| --- | --- | --- | --- |
| 지정가 매수/매도 | `"bid"` 또는 `"ask"` | `"limit"` | `volume`, `price` |
| 시장가 매수 | `"bid"` | `"price"` | `price` |
| 시장가 매도 | `"ask"` | `"market"` | `volume` |
| 최유리 지정가 매수 | `"bid"` | `"best"` | `price`, `time_in_force` |
| 최유리 지정가 매도 | `"ask"` | `"best"` | `volume`, `time_in_force` |

응답:

`dict`

대표 필드:

```python
{
    "uuid": "...",
    "side": "bid",
    "ord_type": "limit",
    "price": "100000000",
    "state": "wait",
    "market": "KRW-BTC",
    "created_at": "2026-05-10T00:00:00+09:00",
    "volume": "0.0001",
    "remaining_volume": "0.0001",
    "reserved_fee": "...",
    "remaining_fee": "...",
    "paid_fee": "0",
    "locked": "...",
    "executed_volume": "0",
    "trades_count": 0,
    "identifier": "client-order-1",
    "time_in_force": None,
    "smp_type": None
}
```

주의: 실제 주문이 생성됩니다. 주문 가능 여부만 확인하려면 `test_order()`를 사용하세요.

### 주문 생성 테스트

Upbit API: `POST /v1/orders/test`

함수:

```python
client.test_order(
    "KRW-BTC",
    "bid",
    ord_type="limit",
    volume="0.0001",
    price="100000000",
)
```

입력:

`create_order()`와 동일합니다.

응답:

`dict`

주문 생성 응답과 같은 형태의 주문 객체를 반환하지만 실제 주문은 생성되지 않습니다. 반환된 `uuid` 또는 `identifier`는 조회/취소에 사용할 수 없습니다.

### 개별 주문 취소 접수

Upbit API: `DELETE /v1/order`

함수:

```python
client.cancel_order(uuid="...")
client.cancel_order(identifier="client-order-1")
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `uuid` | `str \| None` | 조건부 | 취소할 주문 UUID. |
| `identifier` | `str \| None` | 조건부 | 취소할 사용자 지정 주문 ID. |

`uuid` 또는 `identifier` 중 하나는 반드시 필요합니다. 둘 다 전달하면 업비트는 `uuid` 기준으로 처리합니다.

응답:

`dict`

취소된 주문 객체를 반환합니다. 필드는 주문 생성 응답과 유사하며 `state`가 `"cancel"`로 바뀔 수 있습니다.

### 지정 주문 목록 취소 접수

Upbit API: `DELETE /v1/orders/uuids`

함수:

```python
client.cancel_orders_by_ids(uuids=["uuid-1", "uuid-2"])
client.cancel_orders_by_ids(identifiers=["client-order-1", "client-order-2"])
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `uuids` | `Sequence[str] \| None` | 조건부 | 취소할 주문 UUID 목록. |
| `identifiers` | `Sequence[str] \| None` | 조건부 | 취소할 사용자 지정 주문 ID 목록. |

두 인자는 동시에 사용할 수 없습니다. 하나만 전달해야 합니다.

응답:

`list[dict]`

각 원소는 취소된 주문 객체입니다.

### 주문 일괄 취소 접수

Upbit API: `DELETE /v1/orders/open`

함수:

```python
client.batch_cancel_orders(
    quote_currencies=["KRW"],
    cancel_side="bid",
    count=20,
    order_by="desc",
    pairs=None,
    exclude_pairs=None,
)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `quote_currencies` | `str \| Sequence[str] \| None` | 선택 | 취소 대상 호가 통화. |
| `cancel_side` | `str \| None` | 선택 | `"bid"`, `"ask"`, `"all"`. |
| `count` | `int \| None` | 선택 | 취소 대상 주문 수. |
| `order_by` | `str \| None` | 선택 | `"asc"` 또는 `"desc"`. |
| `pairs` | `str \| Sequence[str] \| None` | 선택 | 취소 대상 페어. |
| `exclude_pairs` | `str \| Sequence[str] \| None` | 선택 | 제외할 페어. |

`quote_currencies`와 `pairs`는 동시에 사용할 수 없습니다.

응답:

`dict`

일괄 취소 결과 객체입니다. 업비트 응답에는 취소 성공/실패 결과와 대상 주문 정보가 포함될 수 있습니다.

주의: 실제 체결 대기 주문을 취소합니다.

### 취소 후 재주문

Upbit API: `POST /v1/orders/cancel_and_new`

함수:

```python
client.cancel_and_new_order(
    prev_order_uuid="...",
    new_ord_type="limit",
    new_volume="remain_only",
    new_price="100000000",
    new_identifier="client-order-2",
    new_time_in_force=None,
    new_smp_type=None,
)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `prev_order_uuid` | `str \| None` | 조건부 | 취소할 기존 주문 UUID. |
| `prev_order_identifier` | `str \| None` | 조건부 | 취소할 기존 사용자 지정 주문 ID. |
| `new_ord_type` | `str` | 필수 | 신규 주문 유형. |
| `new_volume` | `str \| float \| None` | 주문 유형별 | 신규 주문 수량. `"remain_only"` 사용 가능. |
| `new_price` | `str \| float \| None` | 주문 유형별 | 신규 주문 가격 또는 총액. |
| `new_identifier` | `str \| None` | 선택 | 신규 사용자 지정 주문 ID. |
| `new_time_in_force` | `str \| None` | 선택 | `"ioc"`, `"fok"`, `"post_only"`. |
| `new_smp_type` | `str \| None` | 선택 | `"reduce"`, `"cancel_maker"`, `"cancel_taker"`. |

`prev_order_uuid` 또는 `prev_order_identifier` 중 하나는 반드시 필요합니다.

응답:

`dict`

취소 후 재주문 결과 객체입니다. 기존 주문 취소 결과와 신규 주문 생성 결과가 포함됩니다.

주의: 실제 주문 취소와 신규 주문 생성이 발생합니다.

### 주문 가능정보 조회

Upbit API: `GET /v1/orders/chance`

함수:

```python
client.get_order_chance("KRW-BTC")
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str` | 필수 | 페어 코드. |

응답:

`dict`

대표 필드:

```python
{
    "bid_fee": "0.0005",
    "ask_fee": "0.0005",
    "maker_bid_fee": "0.0005",
    "maker_ask_fee": "0.0005",
    "market": {
        "id": "KRW-BTC",
        "name": "BTC/KRW",
        "order_sides": ["ask", "bid"],
        "bid_types": ["limit", "price", "best"],
        "ask_types": ["limit", "market", "best"],
        "bid": {...},
        "ask": {...},
        "max_total": "..."
    },
    "bid_account": {...},
    "ask_account": {...}
}
```

### 개별 주문 조회

Upbit API: `GET /v1/order`

함수:

```python
client.get_order(uuid="...")
client.get_order(identifier="client-order-1")
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `uuid` | `str \| None` | 조건부 | 주문 UUID. |
| `identifier` | `str \| None` | 조건부 | 사용자 지정 주문 ID. |

응답:

`dict`

주문 객체를 반환합니다. 대표 필드는 `uuid`, `side`, `ord_type`, `price`, `state`, `market`, `created_at`, `volume`, `remaining_volume`, `executed_volume`, `trades_count`, `trades` 등입니다.

### 주문 목록 조회

Upbit API: `GET /v1/orders/uuids`

함수:

```python
client.get_orders_by_ids(uuids=["uuid-1", "uuid-2"], market="KRW-BTC", order_by="desc")
client.get_orders_by_ids(identifiers=["client-order-1"], market=None)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str \| None` | 선택 | 필터링할 페어 코드. |
| `uuids` | `Sequence[str] \| None` | 조건부 | 주문 UUID 목록. |
| `identifiers` | `Sequence[str] \| None` | 조건부 | 사용자 지정 주문 ID 목록. |
| `order_by` | `str \| None` | 선택 | `"asc"` 또는 `"desc"`. |

`uuids`와 `identifiers` 중 하나만 전달해야 합니다.

응답:

`list[dict]`

각 원소는 주문 객체입니다.

### 체결 대기 주문 조회

Upbit API: `GET /v1/orders/open`

함수:

```python
client.get_open_orders(
    market="KRW-BTC",
    state="wait",
    states=None,
    page=1,
    limit=100,
    order_by="desc",
)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str \| None` | 선택 | 페어 코드. |
| `state` | `str \| None` | 선택 | `"wait"` 또는 `"watch"`. |
| `states` | `Sequence[str] \| None` | 선택 | 여러 상태. 예: `["wait", "watch"]` |
| `page` | `int \| None` | 선택 | 페이지. |
| `limit` | `int \| None` | 선택 | 페이지 크기. |
| `order_by` | `str \| None` | 선택 | `"asc"` 또는 `"desc"`. |

`state`와 `states`는 동시에 사용할 수 없습니다.

응답:

`list[dict]`

각 원소는 체결 대기 또는 예약 주문 객체입니다.

### 종료 주문 조회

Upbit API: `GET /v1/orders/closed`

함수:

```python
client.get_closed_orders(
    market="KRW-BTC",
    state=None,
    states=["done", "cancel"],
    start_time=None,
    end_time=None,
    limit=100,
    order_by="desc",
)
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `market` | `str \| None` | 선택 | 페어 코드. |
| `state` | `str \| None` | 선택 | `"done"`, `"cancel"`, `"done,cancel"`. |
| `states` | `Sequence[str] \| None` | 선택 | 여러 상태. 예: `["done", "cancel"]` |
| `start_time` | `str \| None` | 선택 | 조회 시작 시각. |
| `end_time` | `str \| None` | 선택 | 조회 종료 시각. |
| `limit` | `int \| None` | 선택 | 조회 개수. |
| `order_by` | `str \| None` | 선택 | `"asc"` 또는 `"desc"`. |

`state`와 `states`는 동시에 사용할 수 없습니다.

응답:

`list[dict]`

각 원소는 체결 완료 또는 취소된 주문 객체입니다.

## WebSocket API

WebSocket 함수는 연결 직후 구독 요청을 보내고 `UpbitWebSocketClient`를 반환합니다.

사용 패턴:

```python
with client.subscribe_ticker(["KRW-BTC"], is_only_snapshot=True) as ws:
    message = ws.recv_json()
```

`format` 값:

| 값 | 설명 |
| --- | --- |
| `None` 또는 `"DEFAULT"` | 기본 필드명 객체를 메시지마다 반환. |
| `"SIMPLE"` | 축약 필드명 객체를 메시지마다 반환. |
| `"JSON_LIST"` | 기본 필드명 객체를 리스트로 반환. |
| `"SIMPLE_LIST"` | 축약 필드명 객체를 리스트로 반환. |

### 현재가 구독

Upbit WebSocket type: `ticker`

함수:

```python
ws = client.subscribe_ticker(
    ["KRW-BTC", "KRW-ETH"],
    is_only_snapshot=None,
    is_only_realtime=None,
    format="DEFAULT",
    ticket=None,
)
message = ws.recv_json()
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `codes` | `Sequence[str]` | 필수 | 페어 코드 목록. |
| `is_only_snapshot` | `bool \| None` | 선택 | 스냅샷만 수신. |
| `is_only_realtime` | `bool \| None` | 선택 | 실시간만 수신. |
| `format` | `str \| None` | 선택 | `"DEFAULT"`, `"SIMPLE"`, `"JSON_LIST"`, `"SIMPLE_LIST"`. |
| `ticket` | `str \| None` | 선택 | 구독 티켓. 없으면 UUID 생성. |

응답:

`dict` 또는 `list[dict]`

대표 필드:

```python
{
    "type": "ticker",
    "code": "KRW-BTC",
    "opening_price": ...,
    "high_price": ...,
    "low_price": ...,
    "trade_price": ...,
    "prev_closing_price": ...,
    "change": "RISE",
    "change_price": ...,
    "signed_change_price": ...,
    "change_rate": ...,
    "signed_change_rate": ...,
    "trade_volume": ...,
    "acc_trade_volume": ...,
    "acc_trade_price": ...,
    "timestamp": ...,
    "stream_type": "SNAPSHOT"
}
```

### 체결 구독

Upbit WebSocket type: `trade`

함수:

```python
ws = client.subscribe_trade(["KRW-BTC"], is_only_realtime=True)
message = ws.recv_json()
```

입력:

`subscribe_ticker()`와 동일합니다.

응답:

`dict` 또는 `list[dict]`

대표 필드:

```python
{
    "type": "trade",
    "code": "KRW-BTC",
    "trade_price": ...,
    "trade_volume": ...,
    "ask_bid": "BID",
    "prev_closing_price": ...,
    "change": "RISE",
    "change_price": ...,
    "trade_date": "2026-05-09",
    "trade_time": "15:00:00",
    "trade_timestamp": ...,
    "timestamp": ...,
    "sequential_id": ...,
    "best_ask_price": ...,
    "best_ask_size": ...,
    "best_bid_price": ...,
    "best_bid_size": ...,
    "stream_type": "REALTIME"
}
```

### 호가 구독

Upbit WebSocket type: `orderbook`

함수:

```python
ws = client.subscribe_orderbook(
    ["KRW-BTC.5"],
    level=10000,
    is_only_snapshot=True,
)
message = ws.recv_json()
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `codes` | `Sequence[str]` | 필수 | 페어 코드 목록. 호가 개수 지정은 `"KRW-BTC.5"`처럼 코드 뒤에 붙입니다. |
| `level` | `str \| int \| float \| None` | 선택 | KRW 마켓 호가 모아보기 단위. |
| `is_only_snapshot` | `bool \| None` | 선택 | 스냅샷만 수신. |
| `is_only_realtime` | `bool \| None` | 선택 | 실시간만 수신. |
| `format` | `str \| None` | 선택 | 응답 포맷. |
| `ticket` | `str \| None` | 선택 | 구독 티켓. |

응답:

`dict` 또는 `list[dict]`

대표 필드:

```python
{
    "type": "orderbook",
    "code": "KRW-BTC",
    "timestamp": ...,
    "total_ask_size": ...,
    "total_bid_size": ...,
    "orderbook_units": [
        {
            "ask_price": ...,
            "bid_price": ...,
            "ask_size": ...,
            "bid_size": ...
        }
    ],
    "level": 0,
    "stream_type": "SNAPSHOT"
}
```

### 캔들 구독

Upbit WebSocket type: `candle.{unit}`

함수:

```python
ws = client.subscribe_candle("1s", ["KRW-BTC"], is_only_snapshot=True)
ws = client.subscribe_candle(1, ["KRW-BTC"])  # 1m
message = ws.recv_json()
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `unit` | `str \| int` | 필수 | `"1s"`, `"1m"`, `"3m"`, `"5m"`, `"10m"`, `"15m"`, `"30m"`, `"60m"`, `"240m"`. 정수는 분 단위로 해석됩니다. |
| `codes` | `Sequence[str]` | 필수 | 페어 코드 목록. |
| `is_only_snapshot` | `bool \| None` | 선택 | 스냅샷만 수신. |
| `is_only_realtime` | `bool \| None` | 선택 | 실시간만 수신. |
| `format` | `str \| None` | 선택 | 응답 포맷. |
| `ticket` | `str \| None` | 선택 | 구독 티켓. |

응답:

`dict` 또는 `list[dict]`

대표 필드:

```python
{
    "type": "candle.1s",
    "code": "KRW-BTC",
    "candle_date_time_utc": "...",
    "candle_date_time_kst": "...",
    "opening_price": ...,
    "high_price": ...,
    "low_price": ...,
    "trade_price": ...,
    "candle_acc_trade_volume": ...,
    "candle_acc_trade_price": ...,
    "timestamp": ...,
    "stream_type": "REALTIME"
}
```

### 내 자산 구독

Upbit WebSocket type: `myAsset`

함수:

```python
client = UpbitClient.from_env()
ws = client.subscribe_my_asset(format="JSON_LIST")
message = ws.recv_json()
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `format` | `str \| None` | 선택 | 응답 포맷. |
| `ticket` | `str \| None` | 선택 | 구독 티켓. |

응답:

`dict` 또는 `list[dict]`

자산 변동이 있을 때만 메시지가 옵니다.

대표 필드:

```python
{
    "type": "myAsset",
    "asset_uuid": "...",
    "assets": [
        {
            "currency": "KRW",
            "balance": 1000000.0,
            "locked": 0.0
        }
    ],
    "asset_timestamp": ...,
    "timestamp": ...,
    "stream_type": "REALTIME"
}
```

### 내 주문 및 체결 구독

Upbit WebSocket type: `myOrder`

함수:

```python
client = UpbitClient.from_env()
ws = client.subscribe_my_order(["KRW-BTC"], format="JSON_LIST")
message = ws.recv_json()
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `codes` | `Sequence[str] \| None` | 선택 | 페어 코드 목록. 생략하면 모든 마켓. |
| `format` | `str \| None` | 선택 | 응답 포맷. |
| `ticket` | `str \| None` | 선택 | 구독 티켓. |

응답:

`dict` 또는 `list[dict]`

주문 생성, 체결, 취소 등 내 주문 이벤트가 있을 때만 메시지가 옵니다.

대표 필드:

```python
{
    "type": "myOrder",
    "code": "KRW-BTC",
    "uuid": "...",
    "ask_bid": "BID",
    "order_type": "limit",
    "state": "trade",
    "trade_uuid": "...",
    "price": ...,
    "avg_price": ...,
    "volume": ...,
    "remaining_volume": ...,
    "executed_volume": ...,
    "trades_count": 1,
    "reserved_fee": ...,
    "remaining_fee": ...,
    "paid_fee": ...,
    "locked": ...,
    "executed_funds": ...,
    "time_in_force": None,
    "trade_fee": ...,
    "is_maker": True,
    "identifier": "client-order-1",
    "smp_type": "cancel_maker",
    "prevented_volume": ...,
    "prevented_locked": ...,
    "trade_timestamp": ...,
    "order_timestamp": ...,
    "timestamp": ...,
    "stream_type": "REALTIME"
}
```

### 직접 WebSocket 구독

위 편의 함수로 표현하기 어려운 조합은 `connect_websocket()`에 채널 객체를 직접 넘깁니다.

```python
from upbitlib import make_channel

ws = client.connect_websocket(
    make_channel("trade", codes=["KRW-BTC"]),
    make_channel("orderbook", codes=["KRW-ETH.5"], level=10000),
    ticket="custom-ticket",
    format="SIMPLE_LIST",
)
message = ws.recv_json()
```

입력:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `*channels` | `Mapping[str, Any]` | 필수 | WebSocket Data Type Object 목록. |
| `private` | `bool` | 선택 | 사설 WebSocket 여부. |
| `ticket` | `str \| None` | 선택 | 구독 티켓. |
| `format` | `str \| None` | 선택 | 응답 포맷. |
| `timeout` | `float` | 선택 | 연결 타임아웃 초. |

응답:

연결과 구독 요청이 완료된 `UpbitWebSocketClient`.

## 테스트 명령

기본 테스트:

```bash
/Users/xo/.local/bin/uv run python -m unittest discover -s tests
```

실제 Upbit 통합 테스트:

```bash
UPBIT_RUN_INTEGRATION=1 /Users/xo/.local/bin/uv run python -m unittest -v tests.test_integration_upbit
```
