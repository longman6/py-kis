# PyKIS

**한국투자증권 API Python Wrapper (국내 주식 전용)**

CCXT 스타일의 직관적인 인터페이스로 국내 주식을 거래하세요.

## 설치

```bash
pip install pykis
```

## 빠른 시작

```python
from pykis import KIS

kis = KIS(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="12345678-01",
    is_paper=True,  # 모의투자
)

# 현재가 조회
ticker = kis.fetch_ticker("005930")
print(f"삼성전자: {ticker.last:,}원 ({ticker.change_percent:+.2f}%)")

# 호가 조회
orderbook = kis.fetch_order_book("005930")

# 일봉 조회
ohlcv = kis.fetch_ohlcv("005930", "1d", limit=30)

# 지정가 매수
order = kis.create_limit_order("005930", "buy", 10, 50000)

# 시장가 매도
order = kis.create_market_order("005930", "sell", 5)

# 주문 취소
kis.cancel_order(order.id, "005930")

# 잔고 조회
balance = kis.fetch_balance()
for pos in balance.positions:
    print(f"{pos.name}: {pos.amount}주, {pos.unrealized_pnl_percent:+.2f}%")
```

## 기능

| 기능 | 메서드 |
|------|--------|
| 현재가 조회 | `fetch_ticker(symbol)` |
| 호가 조회 | `fetch_order_book(symbol)` |
| OHLCV 조회 | `fetch_ohlcv(symbol, timeframe, limit)` |
| 지정가 주문 | `create_limit_order(symbol, side, amount, price)` |
| 시장가 주문 | `create_market_order(symbol, side, amount)` |
| 주문 취소 | `cancel_order(order_id, symbol)` |
| 미체결 조회 | `fetch_open_orders()` |
| 잔고 조회 | `fetch_balance()` |

## 지원 범위

✅ **포함:**
- 국내 주식 (KOSPI, KOSDAQ)
- 국내 ETF

❌ **제외:**
- 해외 주식
- 채권, 선물, 옵션, ETN, 펀드

## API 키 발급

1. [한국투자증권](https://www.truefriend.com) 로그인
2. 트레이딩 → Open API → KIS Developers
3. API 키 발급

## 에러 처리

```python
from pykis import KISError, OrderError, InsufficientBalanceError

try:
    order = kis.create_limit_order("005930", "buy", 10, 50000)
except InsufficientBalanceError:
    print("잔고 부족")
except OrderError as e:
    print(f"주문 오류: {e}")
```

## 요구사항

- Python 3.9+
- 한국투자증권 계좌
- KIS Developers API 키

## 라이선스

MIT

## 주의사항

⚠️ 이 라이브러리는 투자 조언을 제공하지 않습니다. 자동매매로 인한 손실에 대해 책임지지 않습니다. 반드시 모의투자로 충분한 테스트 후 사용하세요.
