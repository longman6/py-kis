"""
PyKIS 비동기 계좌 API

잔고 조회의 비동기 기능을 제공합니다.
"""

from pykis.constants import Endpoint, TrID
from pykis.models import Balance


class AsyncAccountAPI:
    """
    비동기 계좌 관리 API
    
    계좌 잔고 및 보유 종목을 비동기로 조회합니다.
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
    
    async def fetch_balance(self) -> Balance:
        """
        계좌 잔고를 비동기로 조회합니다.
        
        Returns:
            Balance 인스턴스
        """
        tr_id = TrID.BALANCE_PAPER if self._is_paper else TrID.BALANCE
        
        data = await self._http.get(
            Endpoint.BALANCE,
            tr_id,
            params={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )
        
        return Balance.from_kis(data)
