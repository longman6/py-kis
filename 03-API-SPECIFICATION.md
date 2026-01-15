# PyKIS - API 명세서

**버전:** 1.0.0  
**작성일:** 2026-01-14

---

## 1. 심볼 표기

국내 주식은 **6자리 종목코드** 사용:

```python
"005930"  # 삼성전자
"000660"  # SK하이닉스
"035720"  # 카카오
"069500"  # KODEX 200 (ETF)
```

---

## 2. Market Data API

### 2.1 fetch_ticker(symbol)

현재가 조회

```python
def fetch_ticker(self, symbol: str) -> Ticker
```

**Example:**
```python
ticker = kis.fetch_ticker("005930")
print(f"{ticker.name}: {ticker.last:,}원 ({ticker.change_percent:+.2f}%)")
```

**Returns:**
```python
Ticker(
    symbol="005930",
    name="삼성전자",
    timestamp=1705200000000,
    datetime=datetime(2026, 1, 14, 9, 0, 0),
    open=57000,
    high=58000,
    low=56500,
    close=57500,
    last=57500,
    volume=15000000,
    change=500,
    change_percent=0.88,
)
```

---

### 2.2 fetch_order_book(symbol)

호가 조회

```python
def fetch_order_book(self, symbol: str) -> OrderBook
```

**Example:**
```python
ob = kis.fetch_order_book("005930")

print("매도호가:")
for ask in ob.asks[:5]:
    print(f"  {ask.price:,}원 - {ask.amount:,}주")

print("매수호가:")
for bid in ob.bids[:5]:
    print(f"  {bid.price:,}원 - {bid.amount:,}주")
```

**Returns:**
```python
OrderBook(
    symbol="005930",
    timestamp=1705200000000,
    bids=[
        OrderBookLevel(price=57400, amount=50000),
        OrderBookLevel(price=57300, amount=30000),
        ...
    ],
    asks=[
        OrderBookLevel(price=57500, amount=25000),
        OrderBookLevel(price=57600, amount=40000),
        ...
    ],
)
```

---

### 2.3 fetch_ohlcv(symbol, timeframe, limit)

OHLCV (캔들) 조회

```python
def fetch_ohlcv(
    self,
    symbol: str,
    timeframe: str = "1d",
    limit: Optional[int] = None,
) -> List[OHLCV]
```

**Parameters:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| symbol | str | ✓ | 종목 코드 |
| timeframe | str | | "1d" (일봉), "1w" (주봉), "1M" (월봉) |
| limit | int | | 최대 개수 (기본: 100) |

**Example:**
```python
# 최근 30일 일봉
ohlcv = kis.fetch_ohlcv("005930", "1d", limit=30)

for candle in ohlcv[-5:]:
    print(f"{candle.datetime.strftime('%Y-%m-%d')}: "
          f"시{candle.open:,} 고{candle.high:,} 저{candle.low:,} 종{candle.close:,}")
```

**Returns:**
```python
[
    OHLCV(
        timestamp=1705113600000,
        datetime=datetime(2026, 1, 13),
        open=56000,
        high=57500,
        low=55800,
        close=57000,
        volume=12000000,
    ),
    ...
]
```

---

## 3. Trading API

### 3.1 create_limit_order(symbol, side, amount, price)

지정가 주문

```python
def create_limit_order(
    self,
    symbol: str,
    side: Literal["buy", "sell"],
    amount: int,
    price: int,
) -> Order
```

**Example:**
```python
# 삼성전자 10주 지정가 매수
order = kis.create_limit_order("005930", "buy", 10, 57000)
print(f"주문번호: {order.id}")
```

---

### 3.2 create_market_order(symbol, side, amount)

시장가 주문

```python
def create_market_order(
    self,
    symbol: str,
    side: Literal["buy", "sell"],
    amount: int,
) -> Order
```

**Example:**
```python
# 삼성전자 5주 시장가 매도
order = kis.create_market_order("005930", "sell", 5)
```

---

### 3.3 cancel_order(order_id, symbol)

주문 취소

```python
def cancel_order(self, order_id: str, symbol: str) -> Order
```

**Example:**
```python
canceled = kis.cancel_order("0000123456", "005930")
print(f"취소 완료: {canceled.status}")
```

---

### 3.4 fetch_open_orders()

미체결 주문 조회

```python
def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Order]
```

**Example:**
```python
open_orders = kis.fetch_open_orders()

for order in open_orders:
    print(f"[{order.id}] {order.symbol} {order.side.value} "
          f"{order.remaining}/{order.amount}주 @ {order.price:,}원")
```

---

### 3.5 Order 응답 모델

```python
Order(
    id="0000123456",           # 주문번호
    symbol="005930",           # 종목코드
    side=OrderSide.BUY,        # buy/sell
    type=OrderType.LIMIT,      # limit/market
    status=OrderStatus.OPEN,   # open/closed/canceled
    amount=10,                 # 주문 수량
    price=57000,               # 주문 가격
    filled=0,                  # 체결 수량
    remaining=10,              # 미체결 수량
    timestamp=1705200000000,
    datetime=datetime(2026, 1, 14, 9, 0, 0),
)
```

---

## 4. Account API

### 4.1 fetch_balance()

계좌 잔고 조회

```python
def fetch_balance(self) -> Balance
```

**Example:**
```python
balance = kis.fetch_balance()

print(f"총 평가: {balance.total:,.0f}원")
print(f"예수금: {balance.deposit:,.0f}원")
print(f"주문가능: {balance.free:,.0f}원")
print(f"수익률: {balance.total_pnl_percent:+.2f}%")

print("\n보유 종목:")
for pos in balance.positions:
    print(f"  {pos.name}: {pos.amount}주, {pos.unrealized_pnl_percent:+.2f}%")
```

**Returns:**
```python
Balance(
    total=55750000,           # 총 평가금액
    free=50000000,            # 주문가능금액
    deposit=50000000,         # 예수금
    
    positions=[
        Position(
            symbol="005930",
            name="삼성전자",
            amount=100,
            average_price=55000,
            current_price=57500,
            unrealized_pnl=250000,
            unrealized_pnl_percent=4.55,
        ),
    ],
    
    total_pnl=250000,
    total_pnl_percent=0.45,
)
```

---

## 5. WebSocket API (AsyncKIS)

### 5.1 watch_ticker(symbol)

실시간 시세

```python
async def watch_ticker(self, symbol: str) -> AsyncIterator[Ticker]
```

**Example:**
```python
async with AsyncKIS(...) as kis:
    async for ticker in kis.watch_ticker("005930"):
        print(f"{ticker.last:,}원")
```

---

### 5.2 watch_order_book(symbol)

실시간 호가

```python
async def watch_order_book(self, symbol: str) -> AsyncIterator[OrderBook]
```

---

### 5.3 watch_my_trades()

체결 통보

```python
async def watch_my_trades(self) -> AsyncIterator[Trade]
```

---

## 6. 에러 처리

```python
from pykis import (
    KISError,
    AuthenticationError,
    OrderError,
    InsufficientBalanceError,
)

try:
    order = kis.create_limit_order("005930", "buy", 10, 57000)
except InsufficientBalanceError:
    print("잔고 부족")
except OrderError as e:
    print(f"주문 오류: [{e.code}] {e}")
except KISError as e:
    print(f"API 오류: {e}")
```
