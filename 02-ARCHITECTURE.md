# PyKIS - 기술 아키텍처 문서

**버전:** 1.0.0  
**작성일:** 2026-01-14

---

## 1. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      User Application                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     PyKIS Public API                         │
│         ┌─────────────┐         ┌─────────────┐             │
│         │    KIS      │         │  AsyncKIS   │             │
│         │ (Sync API)  │         │ (Async API) │             │
│         └─────────────┘         └─────────────┘             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│    │   Quote    │  │   Order    │  │  Account   │          │
│    │    API     │  │    API     │  │    API     │          │
│    └────────────┘  └────────────┘  └────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │ HTTP Client  │ │    Auth      │ │   WebSocket Client   ││
│  │   (httpx)    │ │   Manager    │ │    (websockets)      ││
│  └──────────────┘ └──────────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    KIS REST / WebSocket API                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 프로젝트 구조

```
pykis/
├── pyproject.toml
├── README.md
│
├── src/
│   └── pykis/
│       ├── __init__.py         # 패키지 진입점
│       ├── client.py           # KIS, AsyncKIS 클라이언트
│       ├── exceptions.py       # 예외 클래스
│       ├── constants.py        # 상수 (URL, TR_ID 등)
│       │
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── token.py        # 토큰 관리
│       │   └── manager.py      # 인증 매니저
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── base.py         # API 베이스
│       │   ├── quote.py        # 시세 API
│       │   ├── order.py        # 주문 API
│       │   └── account.py      # 계좌 API
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py         # 베이스 모델
│       │   ├── ticker.py       # 시세 모델
│       │   ├── orderbook.py    # 호가 모델
│       │   ├── ohlcv.py        # 캔들 모델
│       │   ├── order.py        # 주문 모델
│       │   └── balance.py      # 잔고 모델
│       │
│       ├── websocket/
│       │   ├── __init__.py
│       │   └── client.py       # WebSocket 클라이언트
│       │
│       └── utils/
│           ├── __init__.py
│           └── http.py         # HTTP 유틸리티
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_quote.py
│   ├── test_order.py
│   └── test_account.py
│
└── examples/
    ├── basic_usage.py
    └── async_usage.py
```

---

## 3. 핵심 클래스 설계

### 3.1 메인 클라이언트

```python
# src/pykis/client.py

from typing import List, Optional, Literal

class KIS:
    """동기 방식 KIS 클라이언트 (국내 주식 전용)"""
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        is_paper: bool = False,
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.is_paper = is_paper
        
    # === Market Data ===
    def fetch_ticker(self, symbol: str) -> Ticker:
        """현재가 조회"""
        pass
    
    def fetch_order_book(self, symbol: str) -> OrderBook:
        """호가 조회"""
        pass
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: Optional[int] = None,
    ) -> List[OHLCV]:
        """OHLCV 캔들 조회"""
        pass
    
    # === Trading ===
    def create_limit_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
        price: int,
    ) -> Order:
        """지정가 주문"""
        pass
    
    def create_market_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
    ) -> Order:
        """시장가 주문"""
        pass
    
    def cancel_order(self, order_id: str, symbol: str) -> Order:
        """주문 취소"""
        pass
    
    def fetch_open_orders(self) -> List[Order]:
        """미체결 주문 조회"""
        pass
    
    # === Account ===
    def fetch_balance(self) -> Balance:
        """잔고 조회"""
        pass
```

### 3.2 데이터 모델

```python
# src/pykis/models/ticker.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class Ticker(BaseModel):
    """현재가 정보"""
    
    symbol: str                    # 종목 코드
    name: Optional[str] = None     # 종목명
    
    timestamp: int                 # Unix timestamp (ms)
    datetime: datetime             # 조회 시각
    
    open: float                    # 시가
    high: float                    # 고가
    low: float                     # 저가
    close: float                   # 종가
    last: float                    # 현재가
    
    volume: int                    # 거래량
    change: float                  # 전일대비
    change_percent: float          # 등락률 (%)
    
    info: Optional[Dict[str, Any]] = None  # 원본 응답
```

```python
# src/pykis/models/order.py

from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"

class OrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"

class Order(BaseModel):
    """주문 정보"""
    
    id: str                        # 주문번호
    symbol: str                    # 종목 코드
    side: OrderSide                # buy/sell
    type: OrderType                # limit/market
    status: OrderStatus            # 상태
    
    amount: int                    # 주문 수량
    price: Optional[int] = None    # 주문 가격
    filled: int = 0                # 체결 수량
    remaining: int                 # 미체결 수량
    
    timestamp: int
    datetime: datetime
```

```python
# src/pykis/models/balance.py

from pydantic import BaseModel
from typing import List, Optional

class Position(BaseModel):
    """보유 종목"""
    
    symbol: str                   # 종목코드
    name: str                     # 종목명
    amount: int                   # 보유 수량
    average_price: float          # 평균 매입가
    current_price: float          # 현재가
    unrealized_pnl: float         # 평가손익
    unrealized_pnl_percent: float # 수익률 (%)

class Balance(BaseModel):
    """계좌 잔고"""
    
    total: float                  # 총 평가금액
    free: float                   # 주문가능 금액
    deposit: float                # 예수금
    
    positions: List[Position]     # 보유 종목
    
    total_pnl: float              # 총 평가손익
    total_pnl_percent: float      # 총 수익률
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """특정 종목 보유 정보"""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None
```

---

## 4. 인증 시스템

```python
# src/pykis/auth/manager.py

import httpx
from datetime import datetime, timedelta
from pathlib import Path
import json

class AuthManager:
    """인증 관리자"""
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        is_paper: bool = False,
        token_path: Optional[str] = None,
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self.is_paper = is_paper
        self._token_path = Path(token_path or "~/.pykis/token.json").expanduser()
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
        self._load_cached_token()
    
    def get_token(self) -> str:
        """유효한 토큰 반환"""
        if self._is_token_expired():
            self._refresh_token()
        return self._token
    
    def get_headers(self) -> dict:
        """API 요청용 헤더"""
        return {
            "authorization": f"Bearer {self.get_token()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _is_token_expired(self) -> bool:
        if not self._token or not self._token_expires:
            return True
        return datetime.now() >= self._token_expires - timedelta(minutes=5)
    
    def _refresh_token(self):
        """토큰 발급"""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            self._token = data["access_token"]
            self._token_expires = datetime.now() + timedelta(seconds=data["expires_in"])
            self._save_token()
    
    def _load_cached_token(self):
        """캐시된 토큰 로드"""
        if not self._token_path.exists():
            return
        try:
            data = json.loads(self._token_path.read_text())
            expires = datetime.fromisoformat(data["expires_at"])
            if expires > datetime.now():
                self._token = data["token"]
                self._token_expires = expires
        except Exception:
            pass
    
    def _save_token(self):
        """토큰 저장"""
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        self._token_path.write_text(json.dumps({
            "token": self._token,
            "expires_at": self._token_expires.isoformat(),
        }))
```

---

## 5. 예외 클래스

```python
# src/pykis/exceptions.py

class KISError(Exception):
    """기본 예외"""
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code

class AuthenticationError(KISError):
    """인증 오류"""
    pass

class TokenExpiredError(AuthenticationError):
    """토큰 만료"""
    pass

class APIError(KISError):
    """API 오류"""
    pass

class OrderError(APIError):
    """주문 오류"""
    pass

class InsufficientBalanceError(OrderError):
    """잔고 부족"""
    pass
```

---

## 6. 상수 정의

```python
# src/pykis/constants.py

class BaseURL:
    PRODUCTION = "https://openapi.koreainvestment.com:9443"
    PAPER = "https://openapivts.koreainvestment.com:29443"
    
    WS_PRODUCTION = "ws://ops.koreainvestment.com:21000"
    WS_PAPER = "ws://ops.koreainvestment.com:31000"

class Endpoint:
    # 인증
    TOKEN = "/oauth2/tokenP"
    
    # 시세
    PRICE = "/uapi/domestic-stock/v1/quotations/inquire-price"
    ORDERBOOK = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
    DAILY_PRICE = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    
    # 주문
    ORDER = "/uapi/domestic-stock/v1/trading/order-cash"
    ORDER_MODIFY = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
    
    # 잔고
    BALANCE = "/uapi/domestic-stock/v1/trading/inquire-balance"
    OPEN_ORDERS = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"

class TrID:
    # 시세 (실전/모의 동일)
    PRICE = "FHKST01010100"
    ORDERBOOK = "FHKST01010200"
    DAILY_PRICE = "FHKST01010400"
    
    # 주문 (실전)
    BUY = "TTTC0802U"
    SELL = "TTTC0801U"
    MODIFY = "TTTC0803U"
    
    # 주문 (모의)
    BUY_PAPER = "VTTC0802U"
    SELL_PAPER = "VTTC0801U"
    MODIFY_PAPER = "VTTC0803U"
    
    # 잔고
    BALANCE = "TTTC8434R"
    BALANCE_PAPER = "VTTC8434R"
    OPEN_ORDERS = "TTTC8036R"
    OPEN_ORDERS_PAPER = "VTTC8036R"
```

---

## 7. HTTP 유틸리티

```python
# src/pykis/utils/http.py

import httpx
from typing import Dict, Any, Optional
from pykis.exceptions import APIError, RateLimitError

class HTTPClient:
    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url
        self.auth_manager = auth_manager
        self._client = httpx.Client(base_url=base_url, timeout=30.0)
    
    def get(self, endpoint: str, tr_id: str, params: Dict = None) -> Dict[str, Any]:
        headers = self.auth_manager.get_headers()
        headers["tr_id"] = tr_id
        
        response = self._client.get(endpoint, params=params, headers=headers)
        return self._handle_response(response)
    
    def post(self, endpoint: str, tr_id: str, json: Dict = None) -> Dict[str, Any]:
        headers = self.auth_manager.get_headers()
        headers["tr_id"] = tr_id
        
        response = self._client.post(endpoint, json=json, headers=headers)
        return self._handle_response(response)
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            raise APIError(
                data.get("msg1", "Unknown error"),
                code=data.get("msg_cd"),
            )
        
        return data
    
    def close(self):
        self._client.close()
```
