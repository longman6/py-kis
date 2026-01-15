"""
PyKIS OrderBook 모델

호가 조회 결과를 표현하는 모델입니다.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OrderBookLevel(BaseModel):
    """
    호가 단위
    
    개별 호가 가격과 잔량을 표현합니다.
    """
    price: float    # 호가
    amount: int     # 잔량


class OrderBook(BaseModel):
    """
    호가 정보
    
    매수/매도 호가 10단계를 포함합니다.
    """
    
    symbol: str                              # 종목 코드
    timestamp: int                           # Unix timestamp (밀리초)
    datetime: datetime                       # 조회 시각
    
    bids: List[OrderBookLevel]               # 매수호가 (높은 가격순)
    asks: List[OrderBookLevel]               # 매도호가 (낮은 가격순)
    
    info: Optional[Dict[str, Any]] = None    # 원본 응답 데이터

    @classmethod
    def from_kis(cls, data: dict, symbol: str) -> "OrderBook":
        """
        KIS API 응답을 OrderBook 모델로 변환합니다.
        
        Args:
            data: KIS API 응답 데이터
            symbol: 종목 코드
            
        Returns:
            OrderBook 인스턴스
        """
        output = data.get("output1", {})
        now = datetime.now()
        
        bids: List[OrderBookLevel] = []
        asks: List[OrderBookLevel] = []
        
        # 호가 10단계 파싱
        for i in range(1, 11):
            # 매수호가 (bidp1 ~ bidp10)
            bid_price = float(output.get(f"bidp{i}", 0))
            bid_qty = int(output.get(f"bidp_rsqn{i}", 0))
            if bid_price > 0:
                bids.append(OrderBookLevel(price=bid_price, amount=bid_qty))
            
            # 매도호가 (askp1 ~ askp10)
            ask_price = float(output.get(f"askp{i}", 0))
            ask_qty = int(output.get(f"askp_rsqn{i}", 0))
            if ask_price > 0:
                asks.append(OrderBookLevel(price=ask_price, amount=ask_qty))
        
        return cls(
            symbol=symbol,
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
            bids=bids,
            asks=asks,
            info=data,
        )
