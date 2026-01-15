"""
PyKIS 비동기 메인 클라이언트

KIS API를 비동기로 사용하기 위한 진입점 클래스입니다.
"""

from typing import AsyncIterator, List, Literal, Optional

from pykis.constants import BaseURL, OrderSide, OrderType
from pykis.auth.async_manager import AsyncAuthManager
from pykis.utils.async_http import AsyncHTTPClient
from pykis.api.async_quote import AsyncQuoteAPI
from pykis.api.async_order import AsyncOrderAPI
from pykis.api.async_account import AsyncAccountAPI
from pykis.websocket.client import WebSocketClient
from pykis.models import Ticker, OrderBook, OHLCV, Order, Balance


class AsyncKIS:
    """
    PyKIS 비동기 클라이언트
    
    국내 주식(KOSPI/KOSDAQ/ETF) 거래를 위한 비동기 인터페이스를 제공합니다.
    
    Example:
        ```python
        async with AsyncKIS(
            app_key="YOUR_APP_KEY",
            app_secret="YOUR_APP_SECRET",
            account_no="12345678-01",
            is_paper=True,
        ) as kis:
            # 현재가 조회
            ticker = await kis.fetch_ticker("005930")
            print(f"삼성전자: {ticker.last:,}원")
            
            # 실시간 시세 구독
            async for tick in kis.watch_ticker("005930"):
                print(f"{tick.last:,}원")
        ```
    """
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        is_paper: bool = False,
    ):
        """
        AsyncKIS 클라이언트를 초기화합니다.
        
        Args:
            app_key: KIS Developers API Key
            app_secret: KIS Developers API Secret
            account_no: 계좌번호 (형식: "12345678-01")
            is_paper: 모의투자 여부 (기본: False = 실전투자)
        """
        self.is_paper = is_paper
        self.account_no = account_no
        self.app_key = app_key
        self.app_secret = app_secret
        
        # API 기본 URL 설정
        base_url = BaseURL.PAPER if is_paper else BaseURL.PRODUCTION
        
        # 비동기 인증 및 HTTP 클라이언트 초기화
        self._auth = AsyncAuthManager(app_key, app_secret, base_url)
        self._http = AsyncHTTPClient(base_url, self._auth)
        
        # 비동기 API 모듈 초기화
        self._quote = AsyncQuoteAPI(self._http)
        self._order = AsyncOrderAPI(self._http, account_no, is_paper)
        self._account = AsyncAccountAPI(self._http, account_no, is_paper)
        
        # WebSocket 클라이언트 (지연 초기화)
        self._ws: Optional[WebSocketClient] = None
    
    # =========================================================================
    # Market Data API
    # =========================================================================
    
    async def fetch_ticker(self, symbol: str) -> Ticker:
        """
        현재가를 비동기로 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            Ticker 인스턴스
        """
        return await self._quote.fetch_ticker(symbol)
    
    async def fetch_order_book(self, symbol: str) -> OrderBook:
        """
        호가를 비동기로 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            OrderBook 인스턴스
        """
        return await self._quote.fetch_order_book(symbol)
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: Optional[int] = None,
    ) -> List[OHLCV]:
        """
        OHLCV (캔들) 데이터를 비동기로 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            timeframe: 기간 구분 ("1d", "1w", "1M")
            limit: 최대 개수
            
        Returns:
            OHLCV 리스트
        """
        return await self._quote.fetch_ohlcv(symbol, timeframe, limit)
    
    # =========================================================================
    # Trading API
    # =========================================================================
    
    async def create_limit_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
        price: int,
    ) -> Order:
        """
        지정가 주문을 비동기로 생성합니다.
        
        Args:
            symbol: 종목 코드
            side: 주문 방향 ("buy" 또는 "sell")
            amount: 주문 수량
            price: 주문 가격
            
        Returns:
            Order 인스턴스
        """
        return await self._order.create_order(
            symbol, OrderSide(side), OrderType.LIMIT, amount, price
        )
    
    async def create_market_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
    ) -> Order:
        """
        시장가 주문을 비동기로 생성합니다.
        
        Args:
            symbol: 종목 코드
            side: 주문 방향
            amount: 주문 수량
            
        Returns:
            Order 인스턴스
        """
        return await self._order.create_order(
            symbol, OrderSide(side), OrderType.MARKET, amount
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> Order:
        """
        주문을 비동기로 취소합니다.
        
        Args:
            order_id: 주문번호
            symbol: 종목 코드
            
        Returns:
            취소된 Order 인스턴스
        """
        return await self._order.cancel_order(order_id, symbol)
    
    async def fetch_open_orders(self) -> List[Order]:
        """
        미체결 주문을 비동기로 조회합니다.
        
        Returns:
            미체결 Order 리스트
        """
        return await self._order.fetch_open_orders()
    
    # =========================================================================
    # Account API
    # =========================================================================
    
    async def fetch_balance(self) -> Balance:
        """
        계좌 잔고를 비동기로 조회합니다.
        
        Returns:
            Balance 인스턴스
        """
        return await self._account.fetch_balance()
    
    # =========================================================================
    # WebSocket API (실시간 데이터)
    # =========================================================================
    
    async def _ensure_ws_connected(self) -> WebSocketClient:
        """
        WebSocket 연결을 보장합니다 (지연 초기화).
        """
        if self._ws is None:
            self._ws = WebSocketClient(
                self.app_key,
                self.app_secret,
                self.is_paper,
            )
            await self._ws.connect()
        return self._ws
    
    async def watch_ticker(self, symbol: str) -> AsyncIterator[Ticker]:
        """
        실시간 체결가를 구독합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Yields:
            Ticker 인스턴스 (실시간 업데이트)
            
        Example:
            ```python
            async for ticker in kis.watch_ticker("005930"):
                print(f"{ticker.last:,}원")
                if some_condition:
                    break
            ```
        """
        ws = await self._ensure_ws_connected()
        async for ticker in ws.watch_ticker(symbol):
            yield ticker
    
    async def watch_order_book(self, symbol: str) -> AsyncIterator[OrderBook]:
        """
        실시간 호가를 구독합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Yields:
            OrderBook 인스턴스 (실시간 업데이트)
        """
        ws = await self._ensure_ws_connected()
        async for orderbook in ws.watch_order_book(symbol):
            yield orderbook
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    async def close(self) -> None:
        """
        모든 연결을 종료합니다.
        """
        await self._http.close()
        if self._ws:
            await self._ws.disconnect()
            self._ws = None
    
    async def __aenter__(self) -> "AsyncKIS":
        """Async context manager 진입"""
        return self
    
    async def __aexit__(self, *args) -> None:
        """Async context manager 종료"""
        await self.close()
