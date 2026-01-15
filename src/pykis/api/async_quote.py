"""
PyKIS 비동기 시세 API

현재가, 호가, OHLCV 비동기 조회 기능을 제공합니다.
"""

from typing import List, Optional

from pykis.constants import Endpoint, TrID, MarketCode
from pykis.models import Ticker, OrderBook, OHLCV


class AsyncQuoteAPI:
    """
    비동기 시세 조회 API
    
    국내 주식(KOSPI/KOSDAQ/ETF)의 시세 정보를 비동기로 조회합니다.
    """
    
    def __init__(self, http):
        """
        Args:
            http: AsyncHTTPClient 인스턴스
        """
        self._http = http
    
    async def fetch_ticker(self, symbol: str) -> Ticker:
        """
        현재가를 비동기로 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            Ticker 인스턴스
        """
        data = await self._http.get(
            Endpoint.PRICE,
            TrID.PRICE,
            params={
                "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                "FID_INPUT_ISCD": symbol,
            },
        )
        return Ticker.from_kis(data, symbol)
    
    async def fetch_order_book(self, symbol: str) -> OrderBook:
        """
        호가를 비동기로 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            OrderBook 인스턴스
        """
        data = await self._http.get(
            Endpoint.ORDERBOOK,
            TrID.ORDERBOOK,
            params={
                "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                "FID_INPUT_ISCD": symbol,
            },
        )
        return OrderBook.from_kis(data, symbol)
    
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
            OHLCV 리스트 (과거 → 최근 순)
        """
        period_map = {"1d": "D", "1w": "W", "1M": "M"}
        
        data = await self._http.get(
            Endpoint.DAILY_PRICE,
            TrID.DAILY_PRICE,
            params={
                "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
                "FID_PERIOD_DIV_CODE": period_map.get(timeframe, "D"),
                "FID_ORG_ADJ_PRC": "0",
            },
        )
        # 캔들 데이터 파싱 (API 버전에 따라 output 또는 output2)
        items = data.get("output2") or data.get("output") or []
        
        # items가 dict인 경우 리스트로 변환
        if isinstance(items, dict):
            items = []
        
        ohlcv_list = [OHLCV.from_kis(item) for item in items if item]
        
        if limit:
            ohlcv_list = ohlcv_list[:limit]
        
        return list(reversed(ohlcv_list))
