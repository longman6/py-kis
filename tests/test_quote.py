"""
시세 API 테스트
"""

import pytest
from conftest import (
    SAMPLE_PRICE_RESPONSE,
    SAMPLE_ORDERBOOK_RESPONSE,
    SAMPLE_DAILY_PRICE_RESPONSE,
)


class TestFetchTicker:
    """fetch_ticker 테스트"""
    
    def test_fetch_ticker_success(self, mock_kis):
        """현재가 조회 성공"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_PRICE_RESPONSE
        
        ticker = kis.fetch_ticker("005930")
        
        assert ticker.symbol == "005930"
        assert ticker.name == "삼성전자"
        assert ticker.last == 57500
        assert ticker.open == 57000
        assert ticker.high == 58000
        assert ticker.low == 56500
        assert ticker.volume == 15000000
        assert ticker.change == 500
        assert ticker.change_percent == 0.88
    
    def test_fetch_ticker_falling(self, mock_kis):
        """하락 종목 조회"""
        kis, mock_http = mock_kis
        
        # 하락 응답 (prdy_vrss_sign: "5")
        response = {**SAMPLE_PRICE_RESPONSE}
        response["output"] = {
            **SAMPLE_PRICE_RESPONSE["output"],
            "prdy_vrss": "500",
            "prdy_vrss_sign": "5",
            "prdy_ctrt": "0.88",
        }
        mock_http.get.return_value = response
        
        ticker = kis.fetch_ticker("005930")
        
        # 하락이면 음수
        assert ticker.change == -500
        assert ticker.change_percent == -0.88


class TestFetchOrderBook:
    """fetch_order_book 테스트"""
    
    def test_fetch_order_book_success(self, mock_kis):
        """호가 조회 성공"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_ORDERBOOK_RESPONSE
        
        ob = kis.fetch_order_book("005930")
        
        assert ob.symbol == "005930"
        assert len(ob.asks) == 3
        assert len(ob.bids) == 3
        
        # 매도호가 확인
        assert ob.asks[0].price == 57500
        assert ob.asks[0].amount == 25000
        
        # 매수호가 확인
        assert ob.bids[0].price == 57400
        assert ob.bids[0].amount == 50000


class TestFetchOHLCV:
    """fetch_ohlcv 테스트"""
    
    def test_fetch_ohlcv_success(self, mock_kis):
        """OHLCV 조회 성공"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_DAILY_PRICE_RESPONSE
        
        ohlcv = kis.fetch_ohlcv("005930", "1d")
        
        # 과거 → 최근 순으로 정렬되어야 함
        assert len(ohlcv) == 2
        assert ohlcv[0].datetime.day == 13  # 더 과거
        assert ohlcv[1].datetime.day == 14  # 더 최근
        
        # 첫 번째 캔들 (더 과거)
        assert ohlcv[0].open == 56000
        assert ohlcv[0].close == 57000
    
    def test_fetch_ohlcv_with_limit(self, mock_kis):
        """OHLCV 조회 (limit 적용)"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_DAILY_PRICE_RESPONSE
        
        ohlcv = kis.fetch_ohlcv("005930", "1d", limit=1)
        
        assert len(ohlcv) == 1
