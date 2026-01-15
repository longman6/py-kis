"""
PyKIS Balance 모델

계좌 잔고 및 보유 종목 정보를 표현하는 모델입니다.
"""

from typing import List, Optional

from pydantic import BaseModel


class Position(BaseModel):
    """
    보유 종목 정보
    
    개별 보유 종목의 상세 내역입니다.
    """
    
    symbol: str                  # 종목 코드
    name: str                    # 종목명
    amount: int                  # 보유 수량
    average_price: float         # 평균 매입가
    current_price: float         # 현재가
    unrealized_pnl: float        # 평가손익 (원)
    unrealized_pnl_percent: float  # 수익률 (%)


class Balance(BaseModel):
    """
    계좌 잔고 정보
    
    계좌의 자산 현황과 보유 종목 리스트를 포함합니다.
    """
    
    total: float                 # 총 평가금액
    free: float                  # 주문 가능 금액
    deposit: float               # 예수금
    
    positions: List[Position]    # 보유 종목 리스트
    
    total_pnl: float             # 총 평가손익
    total_pnl_percent: float     # 총 수익률 (%)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        특정 종목의 보유 정보를 조회합니다.
        
        Args:
            symbol: 종목 코드
            
        Returns:
            Position 인스턴스 또는 None (미보유 시)
        """
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    @classmethod
    def from_kis(cls, data: dict) -> "Balance":
        """
        KIS API 응답을 Balance 모델로 변환합니다.
        
        Args:
            data: KIS API 응답 데이터
            
        Returns:
            Balance 인스턴스
        """
        output1 = data.get("output1", [])  # 보유 종목 리스트
        output2_list = data.get("output2", [])
        output2 = output2_list[0] if output2_list else {}  # 계좌 요약
        
        # 보유 종목 파싱
        positions: List[Position] = []
        for item in output1:
            # 보유 수량이 0보다 큰 종목만 추가
            qty = int(item.get("hldg_qty", 0))
            if qty > 0:
                positions.append(Position(
                    symbol=item.get("pdno", ""),
                    name=item.get("prdt_name", ""),
                    amount=qty,
                    average_price=float(item.get("pchs_avg_pric", 0)),
                    current_price=float(item.get("prpr", 0)),
                    unrealized_pnl=float(item.get("evlu_pfls_amt", 0)),
                    unrealized_pnl_percent=float(item.get("evlu_pfls_rt", 0)),
                ))
        
        return cls(
            total=float(output2.get("tot_evlu_amt", 0)),
            free=float(output2.get("prvs_rcdl_excc_amt", 0)),
            deposit=float(output2.get("dnca_tot_amt", 0)),
            positions=positions,
            total_pnl=float(output2.get("evlu_pfls_smtl_amt", 0)),
            total_pnl_percent=float(output2.get("asst_icdc_erng_rt", 0)),
        )
