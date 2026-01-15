# PyKIS

**한국투자증권 API Python Wrapper (국내 주식 전용)**

CCXT 스타일의 직관적인 인터페이스로 국내 주식을 거래하세요.

## 설치

```bash
pip install git+https://github.com/longman6/py-kis.git
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

# 일봉 조회 (최근 30개)
ohlcv = kis.fetch_ohlcv("005930", "1d", limit=30)

# 기간별 일봉 조회 (2020년 1월 1일부터 오늘까지)
ohlcv = kis.fetch_ohlcv_range("005930", "20200101")

# 당일 분봉 조회
minute_ohlcv = kis.fetch_minute_ohlcv("005930")

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

kis.close()
```

## 기능

### 시세 조회

| 기능 | 메서드 | 설명 |
|------|--------|------|
| 현재가 조회 | `fetch_ticker(symbol)` | 현재가, 등락률, 거래량 등 |
| 호가 조회 | `fetch_order_book(symbol)` | 매수/매도 10단계 호가 |
| OHLCV 조회 | `fetch_ohlcv(symbol, timeframe, limit)` | 최근 일/주/월봉 (최대 100개) |
| 기간별 OHLCV | `fetch_ohlcv_range(symbol, start_date, end_date)` | 특정 기간 일봉 |
| 당일 분봉 | `fetch_minute_ohlcv(symbol, interval)` | 당일 분봉 |
| 과거 분봉 | `fetch_minute_ohlcv_range(symbol, start_date)` | 과거 분봉 (실전투자 전용, 최대 1년) |

### 주문/계좌

| 기능 | 메서드 | 설명 |
|------|--------|------|
| 지정가 주문 | `create_limit_order(symbol, side, amount, price)` | 지정가 매수/매도 |
| 시장가 주문 | `create_market_order(symbol, side, amount)` | 시장가 매수/매도 |
| 주문 취소 | `cancel_order(order_id, symbol)` | 미체결 주문 취소 |
| 미체결 조회 | `fetch_open_orders()` | 미체결 주문 목록 |
| 잔고 조회 | `fetch_balance()` | 예수금, 보유종목, 평가금액 |

## Rate Limit

| 환경 | 제한 | 비고 |
|------|------|------|
| 실전투자 | 초당 20건 | 계좌당 |
| 모의투자 | 초당 2건 | |
| WebSocket | 1세션, 41건 | 실시간 데이터 |

※ `fetch_ohlcv_range`는 내부적으로 여러 번 API를 호출하므로 Rate Limit을 자동으로 고려합니다.

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

## ⚠️ 면책 조항 (Disclaimer)

### AI 생성 코드

이 프로젝트는 **Claude (Anthropic)** 및 **Gemini (Google DeepMind)** AI를 활용하여 생성되었습니다. AI가 생성한 코드이므로 예상치 못한 버그나 오류가 있을 수 있습니다.

### 사용자 책임

- 이 라이브러리를 사용함으로써 발생하는 **모든 결과에 대한 책임은 전적으로 사용자에게 있습니다.**
- **투자 손실**, 시스템 오류, 데이터 손실 등 어떠한 직접적, 간접적 손해에 대해서도 개발자는 책임지지 않습니다.
- 이 라이브러리는 **투자 조언을 제공하지 않습니다.**
- 실제 거래 전에 반드시 **모의투자로 충분한 테스트**를 수행하세요.
- 소스 코드를 검토하고, 본인의 책임 하에 사용하세요.

### 권장 사항

1. 반드시 **모의투자 환경**에서 먼저 테스트하세요
2. 소액으로 시작하여 점진적으로 테스트하세요
