"""
PyKIS WebSocket 클라이언트

실시간 시세 및 체결 통보 기능을 제공합니다.
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator, Callable, Dict, List, Optional, Any

import websockets
from websockets.client import WebSocketClientProtocol

from pykis.constants import BaseURL
from pykis.models import Ticker, OrderBook, OrderBookLevel


class WebSocketClient:
    """
    KIS WebSocket 클라이언트
    
    실시간 시세 데이터를 스트리밍합니다.
    
    Example:
        ```python
        async with WebSocketClient(app_key, app_secret) as ws:
            async for ticker in ws.watch_ticker("005930"):
                print(f"{ticker.last:,}원")
        ```
    """
    
    # WebSocket TR_ID
    TR_ID_TICKER = "H0STCNT0"      # 실시간 체결가
    TR_ID_ORDERBOOK = "H0STASP0"   # 실시간 호가
    TR_ID_EXECUTION = "H0STCNI0"   # 체결 통보 (내 주문)
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        is_paper: bool = False,
    ):
        """
        Args:
            app_key: KIS API App Key
            app_secret: KIS API App Secret
            is_paper: 모의투자 여부
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.is_paper = is_paper
        
        # WebSocket URL 설정
        self.ws_url = BaseURL.WS_PAPER if is_paper else BaseURL.WS_PRODUCTION
        
        self._ws: Optional[WebSocketClientProtocol] = None
        self._approval_key: Optional[str] = None
        self._subscriptions: Dict[str, List[str]] = {}
    
    async def connect(self) -> None:
        """
        WebSocket에 연결합니다.
        """
        # Approval Key 발급 (웹소켓 접속용 일회성 키)
        self._approval_key = await self._get_approval_key()
        
        # WebSocket 연결
        self._ws = await websockets.connect(
            f"{self.ws_url}/tryitout/H0STCNT0",
            ping_interval=30,
            ping_timeout=10,
        )
    
    async def disconnect(self) -> None:
        """
        WebSocket 연결을 종료합니다.
        """
        if self._ws:
            await self._ws.close()
            self._ws = None
    
    async def __aenter__(self) -> "WebSocketClient":
        """Context manager 진입"""
        await self.connect()
        return self
    
    async def __aexit__(self, *args) -> None:
        """Context manager 종료"""
        await self.disconnect()
    
    async def _get_approval_key(self) -> str:
        """
        WebSocket 접속용 Approval Key를 발급받습니다.
        
        Returns:
            Approval Key 문자열
        """
        import httpx
        
        base_url = BaseURL.PAPER if self.is_paper else BaseURL.PRODUCTION
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}/oauth2/Approval",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "secretkey": self.app_secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("approval_key", "")
    
    async def _subscribe(self, tr_id: str, symbol: str) -> None:
        """
        종목을 구독합니다.
        
        Args:
            tr_id: 거래 ID (체결가/호가)
            symbol: 종목 코드
        """
        if not self._ws:
            raise RuntimeError("WebSocket이 연결되지 않았습니다")
        
        message = json.dumps({
            "header": {
                "approval_key": self._approval_key,
                "custtype": "P",
                "tr_type": "1",  # 1: 등록, 2: 해제
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": symbol,
                }
            }
        })
        
        await self._ws.send(message)
    
    async def watch_ticker(self, symbol: str) -> AsyncIterator[Ticker]:
        """
        실시간 체결가를 구독합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Yields:
            Ticker 인스턴스 (실시간 업데이트)
            
        Example:
            ```python
            async for ticker in ws.watch_ticker("005930"):
                print(f"{ticker.last:,}원")
            ```
        """
        if not self._ws:
            raise RuntimeError("WebSocket이 연결되지 않았습니다")
        
        # 구독 요청
        await self._subscribe(self.TR_ID_TICKER, symbol)
        
        # 메시지 수신 및 파싱
        async for message in self._ws:
            try:
                ticker = self._parse_ticker_message(message, symbol)
                if ticker:
                    yield ticker
            except Exception:
                continue
    
    async def watch_order_book(self, symbol: str) -> AsyncIterator[OrderBook]:
        """
        실시간 호가를 구독합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Yields:
            OrderBook 인스턴스 (실시간 업데이트)
        """
        if not self._ws:
            raise RuntimeError("WebSocket이 연결되지 않았습니다")
        
        await self._subscribe(self.TR_ID_ORDERBOOK, symbol)
        
        async for message in self._ws:
            try:
                orderbook = self._parse_orderbook_message(message, symbol)
                if orderbook:
                    yield orderbook
            except Exception:
                continue
    
    def _parse_ticker_message(
        self,
        message: str,
        symbol: str,
    ) -> Optional[Ticker]:
        """
        실시간 체결가 메시지를 Ticker로 파싱합니다.
        
        KIS 실시간 체결가 메시지 형식:
        0: MKSC_SHRN_ISCD (종목코드)
        1: STCK_CNTG_HOUR (체결시간)
        2: STCK_PRPR (현재가)
        ...
        """
        if not message or message.startswith("{"):
            # JSON 응답은 구독 확인 등 제어 메시지
            return None
        
        # 파이프(|)로 구분된 메시지 파싱
        parts = message.split("|")
        if len(parts) < 4:
            return None
        
        # 데이터 부분 (^ 구분)
        data_parts = parts[3].split("^")
        if len(data_parts) < 20:
            return None
        
        now = datetime.now()
        
        try:
            last = float(data_parts[2])
            change = float(data_parts[4])
            change_pct = float(data_parts[5])
            
            # 전일대비부호 (2:상승, 5:하락)
            sign = data_parts[3]
            if sign in ("4", "5"):
                change = -abs(change)
                change_pct = -abs(change_pct)
            
            return Ticker(
                symbol=symbol,
                name=None,
                timestamp=int(now.timestamp() * 1000),
                datetime=now,
                open=float(data_parts[7]),
                high=float(data_parts[8]),
                low=float(data_parts[9]),
                close=last,
                last=last,
                volume=int(data_parts[13]),
                change=change,
                change_percent=change_pct,
            )
        except (ValueError, IndexError):
            return None
    
    def _parse_orderbook_message(
        self,
        message: str,
        symbol: str,
    ) -> Optional[OrderBook]:
        """
        실시간 호가 메시지를 OrderBook으로 파싱합니다.
        """
        if not message or message.startswith("{"):
            return None
        
        parts = message.split("|")
        if len(parts) < 4:
            return None
        
        data_parts = parts[3].split("^")
        if len(data_parts) < 40:
            return None
        
        now = datetime.now()
        
        try:
            bids: List[OrderBookLevel] = []
            asks: List[OrderBookLevel] = []
            
            # 호가 10단계 파싱 (매도 먼저, 매수 나중)
            for i in range(10):
                ask_idx = 3 + i * 2
                bid_idx = 23 + i * 2
                
                ask_price = float(data_parts[ask_idx])
                ask_qty = int(data_parts[ask_idx + 1])
                bid_price = float(data_parts[bid_idx])
                bid_qty = int(data_parts[bid_idx + 1])
                
                if ask_price > 0:
                    asks.append(OrderBookLevel(price=ask_price, amount=ask_qty))
                if bid_price > 0:
                    bids.append(OrderBookLevel(price=bid_price, amount=bid_qty))
            
            return OrderBook(
                symbol=symbol,
                timestamp=int(now.timestamp() * 1000),
                datetime=now,
                bids=bids,
                asks=asks,
            )
        except (ValueError, IndexError):
            return None
