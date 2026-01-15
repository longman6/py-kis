"""
PyKIS OHLCV 모델

캔들(일봉/주봉/월봉) 데이터를 표현하는 모델입니다.
"""

from datetime import datetime

from pydantic import BaseModel


class OHLCV(BaseModel):
    """
    OHLCV 캔들 데이터
    
    시가, 고가, 저가, 종가, 거래량 정보를 포함합니다.
    """
    
    timestamp: int        # Unix timestamp (밀리초)
    datetime: datetime    # 날짜/시간
    
    open: float           # 시가
    high: float           # 고가
    low: float            # 저가
    close: float          # 종가
    volume: int           # 거래량

    @classmethod
    def from_kis(cls, item: dict) -> "OHLCV":
        """
        KIS API 응답의 개별 캔들을 OHLCV 모델로 변환합니다.
        
        Args:
            item: KIS API 응답의 개별 캔들 데이터
            
        Returns:
            OHLCV 인스턴스
        """
        # 날짜 파싱 (YYYYMMDD 형식)
        date_str = item.get("stck_bsop_date", "")
        if date_str:
            dt = datetime.strptime(date_str, "%Y%m%d")
        else:
            dt = datetime.now()
        
        return cls(
            timestamp=int(dt.timestamp() * 1000),
            datetime=dt,
            open=float(item.get("stck_oprc", 0)),
            high=float(item.get("stck_hgpr", 0)),
            low=float(item.get("stck_lwpr", 0)),
            close=float(item.get("stck_clpr", 0)),
            volume=int(item.get("acml_vol", 0)),
        )
