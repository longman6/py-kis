"""
PyKIS - 한국투자증권 API Python Wrapper

CCXT 스타일의 직관적인 인터페이스로 국내 주식(KOSPI/KOSDAQ/ETF)을 거래하세요.

Example:
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
    print(f"삼성전자: {ticker.last:,}원")
    
    kis.close()
    ```
"""

# 버전 정보
__version__ = "0.1.0"

# 메인 클라이언트
from pykis.client import KIS
from pykis.async_client import AsyncKIS

# WebSocket 클라이언트
from pykis.websocket import WebSocketClient

# 데이터 모델
from pykis.models import (
    Ticker,
    OrderBook,
    OrderBookLevel,
    OHLCV,
    Order,
    Balance,
    Position,
)

# 상수 (Enum)
from pykis.constants import (
    OrderSide,
    OrderType,
    OrderStatus,
)

# 예외 클래스
from pykis.exceptions import (
    KISError,
    AuthenticationError,
    TokenExpiredError,
    APIError,
    RateLimitError,
    OrderError,
    InsufficientBalanceError,
    MarketClosedError,
)

# 공개 API 목록
__all__ = [
    # 버전
    "__version__",
    
    # 클라이언트
    "KIS",
    "AsyncKIS",
    "WebSocketClient",
    
    # 데이터 모델
    "Ticker",
    "OrderBook",
    "OrderBookLevel",
    "OHLCV",
    "Order",
    "Balance",
    "Position",
    
    # 상수
    "OrderSide",
    "OrderType",
    "OrderStatus",
    
    # 예외
    "KISError",
    "AuthenticationError",
    "TokenExpiredError",
    "APIError",
    "RateLimitError",
    "OrderError",
    "InsufficientBalanceError",
    "MarketClosedError",
]
