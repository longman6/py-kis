"""
주문 API 테스트
"""

import pytest
from pykis import OrderSide, OrderType, OrderStatus
from conftest import SAMPLE_ORDER_RESPONSE


class TestCreateOrder:
    """주문 생성 테스트"""
    
    def test_create_limit_order_buy(self, mock_kis):
        """지정가 매수 주문"""
        kis, mock_http = mock_kis
        mock_http.post.return_value = SAMPLE_ORDER_RESPONSE
        
        order = kis.create_limit_order("005930", "buy", 10, 57000)
        
        assert order.id == "0000123456"
        assert order.symbol == "005930"
        assert order.side == OrderSide.BUY
        assert order.type == OrderType.LIMIT
        assert order.status == OrderStatus.OPEN
        assert order.amount == 10
        assert order.price == 57000
        assert order.remaining == 10
    
    def test_create_limit_order_sell(self, mock_kis):
        """지정가 매도 주문"""
        kis, mock_http = mock_kis
        mock_http.post.return_value = SAMPLE_ORDER_RESPONSE
        
        order = kis.create_limit_order("005930", "sell", 5, 58000)
        
        assert order.side == OrderSide.SELL
        assert order.amount == 5
        assert order.price == 58000
    
    def test_create_market_order(self, mock_kis):
        """시장가 주문"""
        kis, mock_http = mock_kis
        mock_http.post.return_value = SAMPLE_ORDER_RESPONSE
        
        order = kis.create_market_order("005930", "buy", 10)
        
        assert order.type == OrderType.MARKET
        assert order.price is None


class TestCancelOrder:
    """주문 취소 테스트"""
    
    def test_cancel_order_success(self, mock_kis):
        """주문 취소 성공"""
        kis, mock_http = mock_kis
        mock_http.post.return_value = {"rt_cd": "0", "output": {}}
        
        result = kis.cancel_order("0000123456", "005930")
        
        assert result.id == "0000123456"
        assert result.status == OrderStatus.CANCELED


class TestFetchOpenOrders:
    """미체결 조회 테스트"""
    
    def test_fetch_open_orders_empty(self, mock_kis):
        """미체결 없음"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = {"rt_cd": "0", "output": []}
        
        orders = kis.fetch_open_orders()
        
        assert orders == []
    
    def test_fetch_open_orders_with_items(self, mock_kis):
        """미체결 있음"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = {
            "rt_cd": "0",
            "output": [
                {
                    "odno": "0000123456",
                    "pdno": "005930",
                    "sll_buy_dvsn_cd": "02",  # 매수
                    "ord_qty": "10",
                    "ord_unpr": "57000",
                    "tot_ccld_qty": "0",
                    "psbl_qty": "10",
                }
            ]
        }
        
        orders = kis.fetch_open_orders()
        
        assert len(orders) == 1
        assert orders[0].id == "0000123456"
        assert orders[0].side == OrderSide.BUY
        assert orders[0].remaining == 10
