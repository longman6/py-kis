"""
PyKIS 비동기 주문 API

주문 생성, 취소, 조회의 비동기 기능을 제공합니다.
"""

from datetime import datetime
from typing import List, Optional

from pykis.constants import Endpoint, TrID, OrderSide, OrderType, OrderStatus
from pykis.models import Order


class AsyncOrderAPI:
    """
    비동기 주문 관리 API
    
    국내 주식(KOSPI/KOSDAQ/ETF)의 주문을 비동기로 생성/취소/조회합니다.
    """
    
    def __init__(self, http, account_no: str, is_paper: bool):
        """
        Args:
            http: AsyncHTTPClient 인스턴스
            account_no: 계좌번호 (형식: "12345678-01")
            is_paper: 모의투자 여부
        """
        self._http = http
        
        parts = account_no.split("-")
        self._cano = parts[0]
        self._acnt_prdt_cd = parts[1] if len(parts) > 1 else "01"
        
        self._is_paper = is_paper
    
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: int,
        price: Optional[int] = None,
    ) -> Order:
        """
        주문을 비동기로 생성합니다.
        
        Args:
            symbol: 종목 코드
            side: 주문 방향 (buy/sell)
            order_type: 주문 유형 (limit/market)
            amount: 주문 수량
            price: 주문 가격 (지정가 시 필수)
            
        Returns:
            Order 인스턴스
        """
        if side == OrderSide.BUY:
            tr_id = TrID.BUY_PAPER if self._is_paper else TrID.BUY
        else:
            tr_id = TrID.SELL_PAPER if self._is_paper else TrID.SELL
        
        ord_dvsn = "00" if order_type == OrderType.LIMIT else "01"
        
        data = await self._http.post(
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
    
    async def cancel_order(self, order_id: str, symbol: str) -> Order:
        """
        주문을 비동기로 취소합니다.
        
        Args:
            order_id: 주문번호
            symbol: 종목 코드
            
        Returns:
            취소된 Order 인스턴스
        """
        tr_id = TrID.MODIFY_PAPER if self._is_paper else TrID.MODIFY
        
        await self._http.post(
            Endpoint.ORDER_MODIFY,
            tr_id,
            json={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "KRX_FWDG_ORD_ORGNO": "",
                "ORGN_ODNO": order_id,
                "ORD_DVSN": "00",
                "RVSE_CNCL_DVSN_CD": "02",
                "ORD_QTY": "0",
                "ORD_UNPR": "0",
                "QTY_ALL_ORD_YN": "Y",
            },
        )
        
        now = datetime.now()
        
        return Order(
            id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            status=OrderStatus.CANCELED,
            amount=0,
            price=None,
            filled=0,
            remaining=0,
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
        )
    
    async def fetch_open_orders(self) -> List[Order]:
        """
        미체결 주문을 비동기로 조회합니다.
        
        Returns:
            미체결 Order 리스트
        """
        tr_id = TrID.OPEN_ORDERS_PAPER if self._is_paper else TrID.OPEN_ORDERS
        
        data = await self._http.get(
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
        
        orders: List[Order] = []
        for item in data.get("output", []):
            sll_buy_cd = item.get("sll_buy_dvsn_cd", "02")
            side = OrderSide.SELL if sll_buy_cd == "01" else OrderSide.BUY
            
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
