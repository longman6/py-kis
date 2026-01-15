"""
PyKIS Order 모델

주문 정보를 표현하는 모델입니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from pykis.constants import OrderSide, OrderType, OrderStatus


class Order(BaseModel):
    """
    주문 정보
    
    주문의 상세 내역을 담고 있습니다.
    """
    
    id: str                               # 주문번호
    symbol: str                           # 종목 코드
    
    side: OrderSide                       # 주문 방향 (buy/sell)
    type: OrderType                       # 주문 유형 (limit/market)
    status: OrderStatus                   # 주문 상태 (open/closed/canceled)
    
    amount: int                           # 주문 수량
    price: Optional[int] = None           # 주문 가격 (시장가 시 None)
    filled: int = 0                       # 체결 수량
    remaining: int                        # 미체결 수량
    
    timestamp: int                        # Unix timestamp (밀리초)
    datetime: datetime                    # 주문 시각
