"""
비동기 API 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from conftest import (
    SAMPLE_PRICE_RESPONSE,
    SAMPLE_ORDERBOOK_RESPONSE,
    SAMPLE_ORDER_RESPONSE,
    SAMPLE_BALANCE_RESPONSE,
)


@pytest.fixture
def mock_async_kis():
    """모의 AsyncKIS 클라이언트"""
    with patch("pykis.async_client.AsyncAuthManager") as mock_auth_class:
        with patch("pykis.async_client.AsyncHTTPClient") as mock_http_class:
            # AsyncAuthManager 모킹
            mock_auth = MagicMock()
            mock_auth.get_headers = AsyncMock(return_value={
                "authorization": "Bearer mock_token",
                "appkey": "mock_app_key",
                "appsecret": "mock_app_secret",
            })
            mock_auth_class.return_value = mock_auth
            
            # AsyncHTTPClient 모킹
            mock_http = MagicMock()
            mock_http.get = AsyncMock()
            mock_http.post = AsyncMock()
            mock_http.close = AsyncMock()
            mock_http_class.return_value = mock_http
            
            from pykis import AsyncKIS
            kis = AsyncKIS(
                app_key="test_key",
                app_secret="test_secret",
                account_no="12345678-01",
                is_paper=True,
            )
            
            yield kis, mock_http


class TestAsyncFetchTicker:
    """비동기 fetch_ticker 테스트"""
    
    @pytest.mark.asyncio
    async def test_fetch_ticker_success(self, mock_async_kis):
        """비동기 현재가 조회 성공"""
        kis, mock_http = mock_async_kis
        mock_http.get.return_value = SAMPLE_PRICE_RESPONSE
        
        ticker = await kis.fetch_ticker("005930")
        
        assert ticker.symbol == "005930"
        assert ticker.name == "삼성전자"
        assert ticker.last == 57500


class TestAsyncFetchOrderBook:
    """비동기 fetch_order_book 테스트"""
    
    @pytest.mark.asyncio
    async def test_fetch_order_book_success(self, mock_async_kis):
        """비동기 호가 조회 성공"""
        kis, mock_http = mock_async_kis
        mock_http.get.return_value = SAMPLE_ORDERBOOK_RESPONSE
        
        ob = await kis.fetch_order_book("005930")
        
        assert ob.symbol == "005930"
        assert len(ob.asks) == 3
        assert len(ob.bids) == 3


class TestAsyncCreateOrder:
    """비동기 주문 생성 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_limit_order(self, mock_async_kis):
        """비동기 지정가 매수 주문"""
        kis, mock_http = mock_async_kis
        mock_http.post.return_value = SAMPLE_ORDER_RESPONSE
        
        order = await kis.create_limit_order("005930", "buy", 10, 57000)
        
        assert order.id == "0000123456"
        assert order.symbol == "005930"
        assert order.amount == 10


class TestAsyncFetchBalance:
    """비동기 fetch_balance 테스트"""
    
    @pytest.mark.asyncio
    async def test_fetch_balance_success(self, mock_async_kis):
        """비동기 잔고 조회 성공"""
        kis, mock_http = mock_async_kis
        mock_http.get.return_value = SAMPLE_BALANCE_RESPONSE
        
        balance = await kis.fetch_balance()
        
        assert balance.total == 55750000
        assert len(balance.positions) == 1
        assert balance.positions[0].symbol == "005930"


class TestAsyncContextManager:
    """비동기 컨텍스트 매니저 테스트"""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_async_kis):
        """async with 문 사용"""
        kis, mock_http = mock_async_kis
        mock_http.get.return_value = SAMPLE_PRICE_RESPONSE
        
        # 정상적으로 컨텍스트 종료되는지 확인
        async with kis:
            ticker = await kis.fetch_ticker("005930")
            assert ticker.symbol == "005930"
        
        # close가 호출되었는지 확인
        mock_http.close.assert_called_once()
