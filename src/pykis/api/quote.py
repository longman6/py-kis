"""
PyKIS 시세 API

현재가, 호가, OHLCV 조회 기능을 제공합니다.
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional

from pykis.constants import Endpoint, TrID, MarketCode
from pykis.models import Ticker, OrderBook, OHLCV


class QuoteAPI:
    """
    시세 조회 API
    
    국내 주식(KOSPI/KOSDAQ/ETF)의 시세 정보를 조회합니다.
    """
    
    # API 호출당 최대 반환 개수
    MAX_OHLCV_PER_REQUEST = 100
    
    def __init__(self, http, is_paper: bool = False):
        """
        Args:
            http: HTTPClient 인스턴스
            is_paper: 모의투자 여부 (Rate Limit 결정용)
        """
        self._http = http
        self._is_paper = is_paper
        # Rate Limit: 모의투자 초당 2건, 실전 초당 20건
        self._delay = 0.5 if is_paper else 0.05
    
    def fetch_ticker(self, symbol: str) -> Ticker:
        """
        현재가를 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            Ticker 인스턴스
        """
        data = self._http.get(
            Endpoint.PRICE,
            TrID.PRICE,
            params={
                "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                "FID_INPUT_ISCD": symbol,
            },
        )
        return Ticker.from_kis(data, symbol)
    
    def fetch_order_book(self, symbol: str) -> OrderBook:
        """
        호가를 조회합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            OrderBook 인스턴스 (매수/매도 각 10단계)
        """
        data = self._http.get(
            Endpoint.ORDERBOOK,
            TrID.ORDERBOOK,
            params={
                "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
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
        """
        # timeframe을 KIS API 형식으로 변환
        period_map = {
            "1d": "D",  # 일봉
            "1w": "W",  # 주봉
            "1M": "M",  # 월봉
        }
        
        data = self._http.get(
            Endpoint.DAILY_PRICE,
            TrID.DAILY_PRICE,
            params={
                "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": "",        # 시작일 (빈 문자열 = 최근)
                "FID_INPUT_DATE_2": "",        # 종료일
                "FID_PERIOD_DIV_CODE": period_map.get(timeframe, "D"),
                "FID_ORG_ADJ_PRC": "0",        # 0: 수정주가 반영
            },
        )
        
        # 캔들 데이터 파싱 (API 버전에 따라 output 또는 output2)
        items = data.get("output2") or data.get("output") or []
        
        # items가 dict인 경우 리스트로 변환
        if isinstance(items, dict):
            items = []
        
        ohlcv_list = [OHLCV.from_kis(item) for item in items if item]
        
        # limit 적용
        if limit:
            ohlcv_list = ohlcv_list[:limit]
        
        # 과거 → 최근 순으로 정렬하여 반환
        return list(reversed(ohlcv_list))
    
    def fetch_ohlcv_range(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
        timeframe: str = "1d",
    ) -> List[OHLCV]:
        """
        특정 기간의 OHLCV (캔들) 데이터를 조회합니다.
        
        내부적으로 여러 번 API를 호출하여 전체 기간의 데이터를 수집합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            start_date: 시작일 ("YYYYMMDD" 또는 "YYYY-MM-DD")
            end_date: 종료일 ("YYYYMMDD" 또는 "YYYY-MM-DD", 기본: 오늘)
            timeframe: 기간 구분 ("1d", "1w", "1M")
            
        Returns:
            OHLCV 리스트 (과거 → 최근 순)
            
        Example:
            # 2020년 1월 1일부터 오늘까지
            ohlcv = kis.fetch_ohlcv_range("005930", "20200101")
            
            # 특정 기간
            ohlcv = kis.fetch_ohlcv_range("005930", "2023-01-01", "2023-12-31")
        """
        # 날짜 형식 정규화 (YYYYMMDD)
        start = start_date.replace("-", "")
        end = end_date.replace("-", "") if end_date else datetime.now().strftime("%Y%m%d")
        
        period_map = {"1d": "D", "1w": "W", "1M": "M"}
        period_code = period_map.get(timeframe, "D")
        
        # 결과 저장 (중복 제거용 dict)
        all_data = {}
        
        # API 호출당 약 100개 반환
        # 일봉 기준 약 5개월씩 조회 (100 거래일 ≈ 5개월)
        chunk_days = 150 if timeframe == "1d" else 365  # 일봉은 150일, 주/월봉은 1년
        
        start_dt = datetime.strptime(start, "%Y%m%d")
        end_dt = datetime.strptime(end, "%Y%m%d")
        
        # 구간 생성 (최근 → 과거 순)
        current_end = end_dt
        request_count = 0
        
        while current_end >= start_dt:
            current_start = max(start_dt, current_end - timedelta(days=chunk_days))
            
            # API 호출
            data = self._http.get(
                "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                "FHKST03010100",
                params={
                    "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                    "FID_INPUT_ISCD": symbol,
                    "FID_INPUT_DATE_1": current_start.strftime("%Y%m%d"),
                    "FID_INPUT_DATE_2": current_end.strftime("%Y%m%d"),
                    "FID_PERIOD_DIV_CODE": period_code,
                    "FID_ORG_ADJ_PRC": "0",
                },
            )
            
            items = data.get("output2", [])
            
            for item in items:
                date_str = item.get("stck_bsop_date", "")
                if date_str and date_str >= start and date_str <= end:
                    all_data[date_str] = OHLCV.from_kis(item)
            
            # 다음 구간
            current_end = current_start - timedelta(days=1)
            request_count += 1
            
            # Rate Limit 대기
            if current_end >= start_dt:
                time.sleep(self._delay)
        
        # 날짜순 정렬 (과거 → 최근)
        sorted_data = sorted(all_data.values(), key=lambda x: x.datetime)
        
        return sorted_data
    
    def fetch_minute_ohlcv(
        self,
        symbol: str,
        interval: int = 1,
    ) -> List[OHLCV]:
        """
        당일 분봉 데이터를 조회합니다.
        
        ※ 주의: KIS API 제한으로 당일 데이터만 조회 가능합니다.
        
        Args:
            symbol: 종목 코드 (예: "005930")
            interval: 분 간격 (1, 3, 5, 10, 15, 30, 60)
            
        Returns:
            OHLCV 리스트 (과거 → 최근 순)
            
        Example:
            # 당일 1분봉
            ohlcv = kis.fetch_minute_ohlcv("005930")
            
            # 당일 5분봉
            ohlcv = kis.fetch_minute_ohlcv("005930", interval=5)
        """
        all_data = {}
        
        # 여러 시간대로 나누어 조회 (장 시작~종료, 09:00 ~ 15:30)
        times = ["153000", "140000", "120000", "100000", "093000"]
        
        for start_time in times:
            data = self._http.get(
                "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
                "FHKST03010200",
                params={
                    "FID_ETC_CLS_CODE": "",
                    "FID_COND_MRKT_DIV_CODE": MarketCode.STOCK.value,
                    "FID_INPUT_ISCD": symbol,
                    "FID_INPUT_HOUR_1": start_time,
                    "FID_PW_DATA_INCU_YN": "N",
                },
            )
            
            items = data.get("output2", [])
            
            for item in items:
                date_str = item.get("stck_bsop_date", "")
                time_str = item.get("stck_cntg_hour", "")
                
                if date_str and time_str:
                    key = f"{date_str}_{time_str}"
                    
                    # 분 간격 필터링
                    minute = int(time_str[2:4])
                    if interval > 1 and minute % interval != 0:
                        continue
                    
                    dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                    
                    all_data[key] = OHLCV(
                        datetime=dt,
                        open=float(item.get("stck_oprc", 0)),
                        high=float(item.get("stck_hgpr", 0)),
                        low=float(item.get("stck_lwpr", 0)),
                        close=float(item.get("stck_prpr", 0)),
                        volume=int(item.get("cntg_vol", 0)),
                    )
            
            # Rate Limit 대기
            time.sleep(self._delay)
        
        # 시간순 정렬
        sorted_data = sorted(all_data.values(), key=lambda x: x.datetime)
        
        return sorted_data
