"""
PyKIS Ticker 모델

현재가 조회 결과를 표현하는 모델입니다.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class Ticker(BaseModel):
    """
    현재가 정보
    
    종목의 현재 시세 정보를 담고 있습니다.
    """
    
    symbol: str                              # 종목 코드 (예: "005930")
    name: Optional[str] = None               # 종목명 (예: "삼성전자")
    
    timestamp: int                           # Unix timestamp (밀리초)
    datetime: datetime                       # 조회 시각
    
    open: float                              # 시가
    high: float                              # 고가
    low: float                               # 저가
    close: float                             # 종가 (= 현재가)
    last: float                              # 현재가
    
    volume: int                              # 누적 거래량
    change: float                            # 전일대비 변동 (원)
    change_percent: float                    # 등락률 (%)
    
    info: Optional[Dict[str, Any]] = None    # 원본 응답 데이터

    @classmethod
    def from_kis(cls, data: dict, symbol: str) -> "Ticker":
        """
        KIS API 응답을 Ticker 모델로 변환합니다.
        
        Args:
            data: KIS API 응답 데이터
            symbol: 종목 코드
            
        Returns:
            Ticker 인스턴스
        """
        output = data.get("output", {})
        
        # 현재가
        last = float(output.get("stck_prpr", 0))
        
        # 전일대비 및 부호
        change = float(output.get("prdy_vrss", 0))
        sign = output.get("prdy_vrss_sign", "3")
        
        # 하락(4, 5)이면 음수로 변환
        if sign in ("4", "5"):
            change = -abs(change)
        
        # 등락률
        change_pct = float(output.get("prdy_ctrt", 0))
        if sign in ("4", "5"):
            change_pct = -abs(change_pct)
        
        now = datetime.now()
        
        return cls(
            symbol=symbol,
            # 종목명: 여러 필드명 시도 (API에 따라 다름)
            name=output.get("hts_kor_isnm") or output.get("prdt_name") or output.get("stck_shrn_iscd"),
            timestamp=int(now.timestamp() * 1000),
            datetime=now,
            open=float(output.get("stck_oprc", 0)),
            high=float(output.get("stck_hgpr", 0)),
            low=float(output.get("stck_lwpr", 0)),
            close=last,
            last=last,
            volume=int(output.get("acml_vol", 0)),
            change=change,
            change_percent=change_pct,
            info=data,
        )
