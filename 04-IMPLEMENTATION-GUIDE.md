# PyKIS - 구현 가이드

**버전:** 1.0.0  
**작성일:** 2026-01-14

---

## 1. 구현 순서

### Phase 1: 핵심 (1주)
1. 예외 클래스 (`exceptions.py`)
2. 상수 정의 (`constants.py`)
3. 인증 시스템 (`auth/`)
4. HTTP 클라이언트 (`utils/http.py`)
5. 시세 조회 (`api/quote.py`)

### Phase 2: 주문/계좌 (1주)
1. 주문 API (`api/order.py`)
2. 계좌 API (`api/account.py`)
3. 메인 클라이언트 (`client.py`)
4. 테스트

### Phase 3: 비동기/WebSocket (선택)
1. AsyncKIS 클라이언트
2. WebSocket 실시간 데이터

---

## 2. 상세 구현

### 2.1 예외 클래스

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

class RateLimitError(APIError):
    """Rate Limit 초과"""
    pass

class OrderError(APIError):
    """주문 오류"""
    pass

class InsufficientBalanceError(OrderError):
    """잔고 부족"""
    pass

# 에러 코드 매핑
ERROR_MAP = {
    "EGW00001": AuthenticationError,
    "EGW00002": TokenExpiredError,
    "OPSP0001": InsufficientBalanceError,
}

def raise_for_code(code: str, message: str):
    exc_class = ERROR_MAP.get(code, APIError)
    raise exc_class(message, code=code)
```

### 2.2 상수 정의

```python
# src/pykis/constants.py

from enum import Enum

class BaseURL:
    PRODUCTION = "https://openapi.koreainvestment.com:9443"
    PAPER = "https://openapivts.koreainvestment.com:29443"
    WS_PRODUCTION = "ws://ops.koreainvestment.com:21000"
    WS_PAPER = "ws://ops.koreainvestment.com:31000"

class Endpoint:
    TOKEN = "/oauth2/tokenP"
    PRICE = "/uapi/domestic-stock/v1/quotations/inquire-price"
    ORDERBOOK = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
    DAILY_PRICE = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    ORDER = "/uapi/domestic-stock/v1/trading/order-cash"
    ORDER_MODIFY = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
    BALANCE = "/uapi/domestic-stock/v1/trading/inquire-balance"
    OPEN_ORDERS = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"

class TrID:
    # 시세
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
    
    # 잔고 (실전/모의)
    BALANCE = "TTTC8434R"
    BALANCE_PAPER = "VTTC8434R"
    OPEN_ORDERS = "TTTC8036R"
    OPEN_ORDERS_PAPER = "VTTC8036R"

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
```

### 2.3 모델 정의

```python
# src/pykis/models/ticker.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class Ticker(BaseModel):
    symbol: str
    name: Optional[str] = None
    timestamp: int
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    last: float
    volume: int
    change: float
    change_percent: float
    info: Optional[Dict[str, Any]] = None

    @classmethod
    def from_kis(cls, data: dict, symbol: str) -> "Ticker":
        """KIS 응답 파싱"""
        output = data.get("output", {})
        
        last = float(output.get("stck_prpr", 0))
        change = float(output.get("prdy_vrss", 0))
        sign = output.get("prdy_vrss_sign", "3")
        
        # 하락이면 음수
        if sign in ("4", "5"):
            change = -abs(change)
        
        change_pct = float(output.get("prdy_ctrt", 0))
        if sign in ("4", "5"):
            change_pct = -abs(change_pct)
        
        now = datetime.now()
        
        return cls(
            symbol=symbol,
            name=output.get("hts_kor_isnm"),
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
            open=float(output.get("stck_oprc", 0)),
            high=float(output.get("stck_hgpr", 0)),
            low=float(output.get("stck_lwpr", 0)),
            close=last,
            last=last,
            volume=int(output.get("acml_vol", 0)),
            change=change,
            change_percent=change_pct,
            info=data,
        )
```

```python
# src/pykis/models/orderbook.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

class OrderBookLevel(BaseModel):
    price: float
    amount: int

class OrderBook(BaseModel):
    symbol: str
    timestamp: int
    datetime: datetime
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    info: Optional[Dict[str, Any]] = None

    @classmethod
    def from_kis(cls, data: dict, symbol: str) -> "OrderBook":
        output = data.get("output1", {})
        now = datetime.now()
        
        bids = []
        asks = []
        
        for i in range(1, 11):
            # 매수호가
            bid_price = float(output.get(f"bidp{i}", 0))
            bid_qty = int(output.get(f"bidp_rsqn{i}", 0))
            if bid_price > 0:
                bids.append(OrderBookLevel(price=bid_price, amount=bid_qty))
            
            # 매도호가
            ask_price = float(output.get(f"askp{i}", 0))
            ask_qty = int(output.get(f"askp_rsqn{i}", 0))
            if ask_price > 0:
                asks.append(OrderBookLevel(price=ask_price, amount=ask_qty))
        
        return cls(
            symbol=symbol,
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
            bids=bids,
            asks=asks,
            info=data,
        )
```

```python
# src/pykis/models/ohlcv.py

from pydantic import BaseModel
from datetime import datetime

class OHLCV(BaseModel):
    timestamp: int
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    @classmethod
    def from_kis(cls, item: dict) -> "OHLCV":
        date_str = item.get("stck_bsop_date", "")
        dt = datetime.strptime(date_str, "%Y%m%d") if date_str else datetime.now()
        
        return cls(
            timestamp=int(dt.timestamp() * 1000),
            datetime=dt,
            open=float(item.get("stck_oprc", 0)),
            high=float(item.get("stck_hgpr", 0)),
            low=float(item.get("stck_lwpr", 0)),
            close=float(item.get("stck_clpr", 0)),
            volume=int(item.get("acml_vol", 0)),
        )
```

```python
# src/pykis/models/order.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pykis.constants import OrderSide, OrderType, OrderStatus

class Order(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    status: OrderStatus
    amount: int
    price: Optional[int] = None
    filled: int = 0
    remaining: int
    timestamp: int
    datetime: datetime
```

```python
# src/pykis/models/balance.py

from pydantic import BaseModel
from typing import List, Optional

class Position(BaseModel):
    symbol: str
    name: str
    amount: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

class Balance(BaseModel):
    total: float
    free: float
    deposit: float
    positions: List[Position]
    total_pnl: float
    total_pnl_percent: float

    def get_position(self, symbol: str) -> Optional[Position]:
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    @classmethod
    def from_kis(cls, data: dict) -> "Balance":
        output1 = data.get("output1", [])
        output2 = data.get("output2", [{}])[0]
        
        positions = []
        for item in output1:
            qty = int(item.get("hldg_qty", 0))
            if qty > 0:
                positions.append(Position(
                    symbol=item.get("pdno", ""),
                    name=item.get("prdt_name", ""),
                    amount=qty,
                    average_price=float(item.get("pchs_avg_pric", 0)),
                    current_price=float(item.get("prpr", 0)),
                    unrealized_pnl=float(item.get("evlu_pfls_amt", 0)),
                    unrealized_pnl_percent=float(item.get("evlu_pfls_rt", 0)),
                ))
        
        return cls(
            total=float(output2.get("tot_evlu_amt", 0)),
            free=float(output2.get("prvs_rcdl_excc_amt", 0)),
            deposit=float(output2.get("dnca_tot_amt", 0)),
            positions=positions,
            total_pnl=float(output2.get("evlu_pfls_smtl_amt", 0)),
            total_pnl_percent=float(output2.get("asst_icdc_erng_rt", 0)),
        )
```

### 2.4 인증 매니저

```python
# src/pykis/auth/manager.py

import httpx
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

class AuthManager:
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        token_path: Optional[str] = None,
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self._path = Path(token_path or "~/.pykis/token.json").expanduser()
        self._token: Optional[str] = None
        self._expires: Optional[datetime] = None
        self._load_token()
    
    def get_headers(self) -> dict:
        if self._is_expired():
            self._refresh()
        return {
            "authorization": f"Bearer {self._token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _is_expired(self) -> bool:
        if not self._token or not self._expires:
            return True
        return datetime.now() >= self._expires - timedelta(minutes=5)
    
    def _refresh(self):
        with httpx.Client() as client:
            resp = client.post(
                f"{self.base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            
            self._token = data["access_token"]
            self._expires = datetime.now() + timedelta(seconds=data["expires_in"])
            self._save_token()
    
    def _load_token(self):
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text())
            exp = datetime.fromisoformat(data["expires_at"])
            if exp > datetime.now():
                self._token = data["token"]
                self._expires = exp
        except:
            pass
    
    def _save_token(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({
            "token": self._token,
            "expires_at": self._expires.isoformat(),
        }))
```

### 2.5 HTTP 클라이언트

```python
# src/pykis/utils/http.py

import httpx
from typing import Dict, Any
from pykis.exceptions import APIError, RateLimitError, raise_for_code

class HTTPClient:
    def __init__(self, base_url: str, auth):
        self.base_url = base_url
        self.auth = auth
        self._client = httpx.Client(base_url=base_url, timeout=30.0)
    
    def get(self, endpoint: str, tr_id: str, params: Dict = None) -> Dict[str, Any]:
        headers = self.auth.get_headers()
        headers["tr_id"] = tr_id
        resp = self._client.get(endpoint, params=params, headers=headers)
        return self._handle(resp)
    
    def post(self, endpoint: str, tr_id: str, json: Dict = None) -> Dict[str, Any]:
        headers = self.auth.get_headers()
        headers["tr_id"] = tr_id
        resp = self._client.post(endpoint, json=json, headers=headers)
        return self._handle(resp)
    
    def _handle(self, resp: httpx.Response) -> Dict[str, Any]:
        if resp.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        
        data = resp.json()
        if data.get("rt_cd") != "0":
            raise_for_code(data.get("msg_cd", ""), data.get("msg1", "Unknown"))
        
        return data
    
    def close(self):
        self._client.close()
```

### 2.6 시세 API

```python
# src/pykis/api/quote.py

from typing import List, Optional
from pykis.constants import Endpoint, TrID
from pykis.models import Ticker, OrderBook, OHLCV

class QuoteAPI:
    def __init__(self, http):
        self._http = http
    
    def fetch_ticker(self, symbol: str) -> Ticker:
        data = self._http.get(
            Endpoint.PRICE,
            TrID.PRICE,
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
            },
        )
        return Ticker.from_kis(data, symbol)
    
    def fetch_order_book(self, symbol: str) -> OrderBook:
        data = self._http.get(
            Endpoint.ORDERBOOK,
            TrID.ORDERBOOK,
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
            },
        )
        return OrderBook.from_kis(data, symbol)
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: Optional[int] = None,
    ) -> List[OHLCV]:
        period_map = {"1d": "D", "1w": "W", "1M": "M"}
        
        data = self._http.get(
            Endpoint.DAILY_PRICE,
            TrID.DAILY_PRICE,
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
                "FID_PERIOD_DIV_CODE": period_map.get(timeframe, "D"),
                "FID_ORG_ADJ_PRC": "0",
            },
        )
        
        items = data.get("output2", [])
        ohlcv_list = [OHLCV.from_kis(item) for item in items]
        
        if limit:
            ohlcv_list = ohlcv_list[:limit]
        
        return list(reversed(ohlcv_list))
```

### 2.7 주문 API

```python
# src/pykis/api/order.py

from typing import List, Optional
from datetime import datetime
from pykis.constants import Endpoint, TrID, OrderSide, OrderType, OrderStatus
from pykis.models import Order

class OrderAPI:
    def __init__(self, http, account_no: str, is_paper: bool):
        self._http = http
        self._cano = account_no.split("-")[0]
        self._acnt_prdt_cd = account_no.split("-")[1]
        self._is_paper = is_paper
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: int,
        price: Optional[int] = None,
    ) -> Order:
        # TR_ID 선택
        if side == OrderSide.BUY:
            tr_id = TrID.BUY_PAPER if self._is_paper else TrID.BUY
        else:
            tr_id = TrID.SELL_PAPER if self._is_paper else TrID.SELL
        
        # 주문구분 (00:지정가, 01:시장가)
        ord_dvsn = "00" if order_type == OrderType.LIMIT else "01"
        
        data = self._http.post(
            Endpoint.ORDER,
            tr_id,
            json={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "PDNO": symbol,
                "ORD_DVSN": ord_dvsn,
                "ORD_QTY": str(amount),
                "ORD_UNPR": str(price or 0),
            },
        )
        
        output = data.get("output", {})
        now = datetime.now()
        
        return Order(
            id=output.get("ODNO", ""),
            symbol=symbol,
            side=side,
            type=order_type,
            status=OrderStatus.OPEN,
            amount=amount,
            price=price,
            filled=0,
            remaining=amount,
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
        )
    
    def cancel_order(self, order_id: str, symbol: str) -> Order:
        tr_id = TrID.MODIFY_PAPER if self._is_paper else TrID.MODIFY
        
        data = self._http.post(
            Endpoint.ORDER_MODIFY,
            tr_id,
            json={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "KRX_FWDG_ORD_ORGNO": "",
                "ORGN_ODNO": order_id,
                "ORD_DVSN": "00",
                "RVSE_CNCL_DVSN_CD": "02",  # 취소
                "ORD_QTY": "0",
                "ORD_UNPR": "0",
                "QTY_ALL_ORD_YN": "Y",
            },
        )
        
        now = datetime.now()
        return Order(
            id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,  # 원본 정보 필요
            type=OrderType.LIMIT,
            status=OrderStatus.CANCELED,
            amount=0,
            price=None,
            filled=0,
            remaining=0,
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
        )
    
    def fetch_open_orders(self) -> List[Order]:
        tr_id = TrID.OPEN_ORDERS_PAPER if self._is_paper else TrID.OPEN_ORDERS
        
        data = self._http.get(
            Endpoint.OPEN_ORDERS,
            tr_id,
            params={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
                "INQR_DVSN_1": "0",
                "INQR_DVSN_2": "0",
            },
        )
        
        orders = []
        for item in data.get("output", []):
            side = OrderSide.SELL if item.get("sll_buy_dvsn_cd") == "01" else OrderSide.BUY
            
            orders.append(Order(
                id=item.get("odno", ""),
                symbol=item.get("pdno", ""),
                side=side,
                type=OrderType.LIMIT,
                status=OrderStatus.OPEN,
                amount=int(item.get("ord_qty", 0)),
                price=int(float(item.get("ord_unpr", 0))),
                filled=int(item.get("tot_ccld_qty", 0)),
                remaining=int(item.get("psbl_qty", 0)),
                timestamp=int(datetime.now().timestamp() * 1000),
                datetime=datetime.now(),
            ))
        
        return orders
```

### 2.8 계좌 API

```python
# src/pykis/api/account.py

from pykis.constants import Endpoint, TrID
from pykis.models import Balance

class AccountAPI:
    def __init__(self, http, account_no: str, is_paper: bool):
        self._http = http
        self._cano = account_no.split("-")[0]
        self._acnt_prdt_cd = account_no.split("-")[1]
        self._is_paper = is_paper
    
    def fetch_balance(self) -> Balance:
        tr_id = TrID.BALANCE_PAPER if self._is_paper else TrID.BALANCE
        
        data = self._http.get(
            Endpoint.BALANCE,
            tr_id,
            params={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )
        
        return Balance.from_kis(data)
```

### 2.9 메인 클라이언트

```python
# src/pykis/client.py

from typing import List, Optional, Literal
from pykis.constants import BaseURL, OrderSide, OrderType
from pykis.auth import AuthManager
from pykis.utils.http import HTTPClient
from pykis.api.quote import QuoteAPI
from pykis.api.order import OrderAPI
from pykis.api.account import AccountAPI
from pykis.models import Ticker, OrderBook, OHLCV, Order, Balance

class KIS:
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        is_paper: bool = False,
    ):
        self.is_paper = is_paper
        base_url = BaseURL.PAPER if is_paper else BaseURL.PRODUCTION
        
        self._auth = AuthManager(app_key, app_secret, base_url)
        self._http = HTTPClient(base_url, self._auth)
        
        self._quote = QuoteAPI(self._http)
        self._order = OrderAPI(self._http, account_no, is_paper)
        self._account = AccountAPI(self._http, account_no, is_paper)
    
    # === Market Data ===
    def fetch_ticker(self, symbol: str) -> Ticker:
        return self._quote.fetch_ticker(symbol)
    
    def fetch_order_book(self, symbol: str) -> OrderBook:
        return self._quote.fetch_order_book(symbol)
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: Optional[int] = None,
    ) -> List[OHLCV]:
        return self._quote.fetch_ohlcv(symbol, timeframe, limit)
    
    # === Trading ===
    def create_limit_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
        price: int,
    ) -> Order:
        return self._order.create_order(
            symbol, OrderSide(side), OrderType.LIMIT, amount, price
        )
    
    def create_market_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
    ) -> Order:
        return self._order.create_order(
            symbol, OrderSide(side), OrderType.MARKET, amount
        )
    
    def cancel_order(self, order_id: str, symbol: str) -> Order:
        return self._order.cancel_order(order_id, symbol)
    
    def fetch_open_orders(self) -> List[Order]:
        return self._order.fetch_open_orders()
    
    # === Account ===
    def fetch_balance(self) -> Balance:
        return self._account.fetch_balance()
    
    # === Context Manager ===
    def close(self):
        self._http.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
```

### 2.10 패키지 진입점

```python
# src/pykis/__init__.py

from pykis.client import KIS
from pykis.models import Ticker, OrderBook, OHLCV, Order, Balance, Position
from pykis.constants import OrderSide, OrderType, OrderStatus
from pykis.exceptions import (
    KISError,
    AuthenticationError,
    TokenExpiredError,
    APIError,
    RateLimitError,
    OrderError,
    InsufficientBalanceError,
)

__version__ = "0.1.0"
__all__ = [
    "KIS",
    "Ticker", "OrderBook", "OHLCV", "Order", "Balance", "Position",
    "OrderSide", "OrderType", "OrderStatus",
    "KISError", "AuthenticationError", "TokenExpiredError",
    "APIError", "RateLimitError", "OrderError", "InsufficientBalanceError",
]
```

---

## 3. pyproject.toml

```toml
[tool.poetry]
name = "pykis"
version = "0.1.0"
description = "CCXT-style Python wrapper for KIS API (국내 주식)"
authors = ["Your Name <you@example.com>"]
license = "MIT"
readme = "README.md"
packages = [{ include = "pykis", from = "src" }]

[tool.poetry.dependencies]
python = "^3.9"
httpx = "^0.27.0"
pydantic = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
ruff = "^0.1.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "UP", "B"]

[tool.mypy]
python_version = "3.9"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=pykis"
```

---

## 4. 테스트 예시

```python
# tests/test_quote.py

import pytest
from unittest.mock import Mock, patch
from pykis import KIS

@pytest.fixture
def mock_kis():
    with patch("pykis.client.AuthManager"):
        with patch("pykis.client.HTTPClient") as mock_http:
            kis = KIS("key", "secret", "12345678-01", is_paper=True)
            yield kis, mock_http

def test_fetch_ticker(mock_kis):
    kis, mock_http = mock_kis
    
    # Mock 응답 설정
    mock_http.return_value.get.return_value = {
        "rt_cd": "0",
        "output": {
            "stck_prpr": "57500",
            "stck_oprc": "57000",
            "stck_hgpr": "58000",
            "stck_lwpr": "56500",
            "acml_vol": "15000000",
            "prdy_vrss": "500",
            "prdy_vrss_sign": "2",
            "prdy_ctrt": "0.88",
            "hts_kor_isnm": "삼성전자",
        }
    }
    
    ticker = kis.fetch_ticker("005930")
    
    assert ticker.symbol == "005930"
    assert ticker.last == 57500
    assert ticker.change == 500
    assert ticker.change_percent == 0.88
```

---

## 5. 체크리스트

### Phase 1 완료 조건
- [ ] `poetry install` 성공
- [ ] `pytest` 통과
- [ ] 토큰 발급/저장 동작
- [ ] `fetch_ticker()` 동작
- [ ] `fetch_order_book()` 동작
- [ ] `fetch_ohlcv()` 동작

### Phase 2 완료 조건
- [ ] `create_limit_order()` 동작
- [ ] `create_market_order()` 동작
- [ ] `cancel_order()` 동작
- [ ] `fetch_open_orders()` 동작
- [ ] `fetch_balance()` 동작
- [ ] 테스트 커버리지 70%+
