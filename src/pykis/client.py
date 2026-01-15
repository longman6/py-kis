"""
PyKIS 메인 클라이언트

KIS API를 사용하기 위한 진입점 클래스입니다.
"""

from typing import List, Literal, Optional

from pykis.constants import BaseURL, OrderSide, OrderType
from pykis.auth import AuthManager
from pykis.utils.http import HTTPClient
from pykis.api.quote import QuoteAPI
from pykis.api.order import OrderAPI
from pykis.api.account import AccountAPI
from pykis.models import Ticker, OrderBook, OHLCV, Order, Balance


class KIS:
    """
    PyKIS 동기 클라이언트
    
    국내 주식(KOSPI/KOSDAQ/ETF) 거래를 위한 CCXT 스타일 인터페이스를 제공합니다.
    
    Example:
        ```python
        kis = KIS(
            app_key="YOUR_APP_KEY",
            app_secret="YOUR_APP_SECRET",
            account_no="12345678-01",
            is_paper=True,
        )
        
        # 현재가 조회
        ticker = kis.fetch_ticker("005930")
        print(f"삼성전자: {ticker.last:,}원")
        
        # 지정가 매수
        order = kis.create_limit_order("005930", "buy", 10, 50000)
        
        kis.close()
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
        KIS 클라이언트를 초기화합니다.
        
        Args:
            app_key: KIS Developers API Key
            app_secret: KIS Developers API Secret
            account_no: 계좌번호 (형식: "12345678-01")
            is_paper: 모의투자 여부 (기본: False = 실전투자)
        """
        self.is_paper = is_paper
        self.account_no = account_no
        
        # API 기본 URL 설정
        base_url = BaseURL.PAPER if is_paper else BaseURL.PRODUCTION
        
        # 인증 및 HTTP 클라이언트 초기화
        self._auth = AuthManager(app_key, app_secret, base_url)
        self._http = HTTPClient(base_url, self._auth)
        
        # API 모듈 초기화
        self._quote = QuoteAPI(self._http)
        self._order = OrderAPI(self._http, account_no, is_paper)
        self._account = AccountAPI(self._http, account_no, is_paper)
    
    # =========================================================================
    # Market Data API
    # =========================================================================
    
    def fetch_ticker(self, symbol: str) -> Ticker:
        """
        현재가를 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            Ticker 인스턴스
            
        Example:
            ```python
            ticker = kis.fetch_ticker("005930")
            print(f"{ticker.name}: {ticker.last:,}원 ({ticker.change_percent:+.2f}%)")
            ```
        """
        return self._quote.fetch_ticker(symbol)
    
    def fetch_order_book(self, symbol: str) -> OrderBook:
        """
        호가를 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            OrderBook 인스턴스 (매수/매도 각 10단계)
            
        Example:
            ```python
            ob = kis.fetch_order_book("005930")
            for ask in ob.asks[:3]:
                print(f"매도: {ask.price:,}원 - {ask.amount:,}주")
            ```
        """
        return self._quote.fetch_order_book(symbol)
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: Optional[int] = None,
    ) -> List[OHLCV]:
        """
        OHLCV (캔들) 데이터를 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            timeframe: 기간 구분
                - "1d": 일봉
                - "1w": 주봉
                - "1M": 월봉
            limit: 최대 개수 (기본: 100)
            
        Returns:
            OHLCV 리스트 (과거 → 최근 순)
            
        Example:
            ```python
            ohlcv = kis.fetch_ohlcv("005930", "1d", limit=30)
            for candle in ohlcv[-5:]:
                print(f"{candle.datetime.date()}: {candle.close:,.0f}원")
            ```
        """
        return self._quote.fetch_ohlcv(symbol, timeframe, limit)
    
    # =========================================================================
    # Trading API
    # =========================================================================
    
    def create_limit_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
        price: int,
    ) -> Order:
        """
        지정가 주문을 생성합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            side: 주문 방향 ("buy" 또는 "sell")
            amount: 주문 수량 (주)
            price: 주문 가격 (원)
            
        Returns:
            Order 인스턴스 (주문번호 포함)
            
        Example:
            ```python
            order = kis.create_limit_order("005930", "buy", 10, 50000)
            print(f"주문번호: {order.id}")
            ```
        """
        return self._order.create_order(
            symbol, OrderSide(side), OrderType.LIMIT, amount, price
        )
    
    def create_market_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: int,
    ) -> Order:
        """
        시장가 주문을 생성합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            side: 주문 방향 ("buy" 또는 "sell")
            amount: 주문 수량 (주)
            
        Returns:
            Order 인스턴스 (주문번호 포함)
            
        Example:
            ```python
            order = kis.create_market_order("005930", "sell", 5)
            ```
        """
        return self._order.create_order(
            symbol, OrderSide(side), OrderType.MARKET, amount
        )
    
    def cancel_order(self, order_id: str, symbol: str) -> Order:
        """
        주문을 취소합니다.
        
        Args:
            order_id: 주문번호
            symbol: 종목 코드
            
        Returns:
            취소된 Order 인스턴스
            
        Example:
            ```python
            canceled = kis.cancel_order("0000123456", "005930")
            print(f"취소 완료: {canceled.status}")
            ```
        """
        return self._order.cancel_order(order_id, symbol)
    
    def fetch_open_orders(self) -> List[Order]:
        """
        미체결 주문을 조회합니다.
        
        Returns:
            미체결 Order 리스트
            
        Example:
            ```python
            for order in kis.fetch_open_orders():
                print(f"[{order.id}] {order.symbol} {order.side.value} "
                      f"{order.remaining}주 @ {order.price:,}원")
            ```
        """
        return self._order.fetch_open_orders()
    
    # =========================================================================
    # Account API
    # =========================================================================
    
    def fetch_balance(self) -> Balance:
        """
        계좌 잔고를 조회합니다.
        
        Returns:
            Balance 인스턴스 (예수금, 평가금액, 보유 종목 등)
            
        Example:
            ```python
            balance = kis.fetch_balance()
            print(f"총 평가: {balance.total:,.0f}원")
            print(f"예수금: {balance.deposit:,.0f}원")
            
            for pos in balance.positions:
                print(f"{pos.name}: {pos.amount}주 ({pos.unrealized_pnl_percent:+.2f}%)")
            ```
        """
        return self._account.fetch_balance()
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    def close(self) -> None:
        """
        HTTP 클라이언트를 종료합니다.
        
        리소스 정리를 위해 사용 완료 후 호출해주세요.
        """
        self._http.close()
    
    def __enter__(self) -> "KIS":
        """Context manager 진입"""
        return self
    
    def __exit__(self, *args) -> None:
        """Context manager 종료"""
        self.close()
