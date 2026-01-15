# PyKIS - 한국투자증권 API Python Wrapper

## Product Requirements Document (PRD)

**버전:** 1.0.0  
**작성일:** 2026-01-14

---

## 1. 개요

### 1.1 제품 비전
PyKIS는 한국투자증권(KIS) Open API를 CCXT 스타일로 래핑한 Python 라이브러리입니다. **국내 주식(KOSPI/KOSDAQ)** 거래에 집중합니다.

### 1.2 목표
- **CCXT 스타일 API**: 직관적이고 일관된 인터페이스
- **국내 주식 전문**: KOSPI, KOSDAQ, ETF 완벽 지원
- **타입 안전성**: 완벽한 Type Hints와 Pydantic 모델
- **비동기 지원**: async/await 기반의 비동기 API

### 1.3 범위 (Scope)

**포함:**
- ✅ 국내 주식 (KOSPI, KOSDAQ)
- ✅ 국내 ETF
- ✅ 실시간 시세 (WebSocket)

**제외:**
- ❌ 해외 주식 (미국, 중국, 일본 등)
- ❌ 채권
- ❌ 선물/옵션
- ❌ ETN
- ❌ 펀드

---

## 2. 핵심 기능 요구사항

### 2.1 인증

| ID | 기능 | 우선순위 | 설명 |
|----|------|----------|------|
| AUTH-01 | API 키 인증 | P0 | AppKey, AppSecret 기반 인증 |
| AUTH-02 | 토큰 자동 관리 | P0 | Access Token 자동 발급/갱신/저장 |
| AUTH-03 | 실전/모의투자 전환 | P0 | 환경 간 쉬운 전환 |

### 2.2 시장 데이터

| ID | 기능 | 우선순위 | 설명 |
|----|------|----------|------|
| MKT-01 | 현재가 조회 | P0 | fetch_ticker() |
| MKT-02 | 호가 조회 | P0 | fetch_order_book() |
| MKT-03 | OHLCV 조회 | P0 | fetch_ohlcv() - 일봉/주봉/월봉 |
| MKT-04 | 체결 내역 | P1 | fetch_trades() |

### 2.3 주문 관리

| ID | 기능 | 우선순위 | 설명 |
|----|------|----------|------|
| ORD-01 | 지정가 주문 | P0 | create_limit_order() |
| ORD-02 | 시장가 주문 | P0 | create_market_order() |
| ORD-03 | 주문 취소 | P0 | cancel_order() |
| ORD-04 | 주문 정정 | P1 | edit_order() |
| ORD-05 | 미체결 조회 | P0 | fetch_open_orders() |

### 2.4 계좌 관리

| ID | 기능 | 우선순위 | 설명 |
|----|------|----------|------|
| ACC-01 | 잔고 조회 | P0 | fetch_balance() |
| ACC-02 | 보유 종목 | P0 | balance.positions |

### 2.5 실시간 데이터 (WebSocket)

| ID | 기능 | 우선순위 | 설명 |
|----|------|----------|------|
| WS-01 | 실시간 시세 | P1 | watch_ticker() |
| WS-02 | 실시간 호가 | P1 | watch_order_book() |
| WS-03 | 체결 통보 | P1 | watch_my_trades() |

---

## 3. 사용 예시

```python
from pykis import KIS

kis = KIS(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="12345678-01",
    is_paper=True  # 모의투자
)

# 시세 조회
ticker = kis.fetch_ticker("005930")
print(f"삼성전자: {ticker.last:,}원")

# 지정가 매수
order = kis.create_limit_order("005930", "buy", 10, 50000)

# 잔고 조회
balance = kis.fetch_balance()
for pos in balance.positions:
    print(f"{pos.name}: {pos.amount}주")
```

---

## 4. 로드맵

### Phase 1 (MVP) - 2주
- [ ] 프로젝트 구조 설정
- [ ] 인증 시스템 (토큰 발급/저장/갱신)
- [ ] 시세 조회 (현재가, 호가, OHLCV)
- [ ] 주문 (지정가, 시장가, 취소)
- [ ] 잔고 조회

### Phase 2 - 2주
- [ ] 비동기 API (AsyncKIS)
- [ ] WebSocket 실시간 데이터
- [ ] 테스트 및 문서화

---

## 5. 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.9+ |
| HTTP | httpx |
| WebSocket | websockets |
| 검증 | Pydantic v2 |
| 테스트 | pytest |
| 패키징 | Poetry |
