"""
PyKIS 계좌 API

잔고 조회 기능을 제공합니다.
"""

from pykis.constants import Endpoint, TrID
from pykis.models import Balance


class AccountAPI:
    """
    계좌 관리 API
    
    계좌 잔고 및 보유 종목을 조회합니다.
    """
    
    def __init__(self, http, account_no: str, is_paper: bool):
        """
        Args:
            http: HTTPClient 인스턴스
            account_no: 계좌번호 (형식: "12345678-01")
            is_paper: 모의투자 여부
        """
        self._http = http
        
        # 계좌번호 분리
        parts = account_no.split("-")
        self._cano = parts[0]
        self._acnt_prdt_cd = parts[1] if len(parts) > 1 else "01"
        
        self._is_paper = is_paper
    
    def fetch_balance(self) -> Balance:
        """
        계좌 잔고를 조회합니다.
        
        Returns:
            Balance 인스턴스 (예수금, 평가금액, 보유 종목 등 포함)
        """
        tr_id = TrID.BALANCE_PAPER if self._is_paper else TrID.BALANCE
        
        data = self._http.get(
            Endpoint.BALANCE,
            tr_id,
            params={
                "CANO": self._cano,
                "ACNT_PRDT_CD": self._acnt_prdt_cd,
                "AFHR_FLPR_YN": "N",           # 시간외단일가 반영 여부
                "OFL_YN": "",                  # 오프라인 여부
                "INQR_DVSN": "02",             # 조회구분 (01: 대출, 02: 일반)
                "UNPR_DVSN": "01",             # 단가구분 (01: 기본)
                "FUND_STTL_ICLD_YN": "N",      # 펀드결제분 포함 여부
                "FNCG_AMT_AUTO_RDPT_YN": "N",  # 융자금 자동상환 여부
                "PRCS_DVSN": "00",             # 처리구분 (00: 전일)
                "CTX_AREA_FK100": "",          # 연속조회 키
                "CTX_AREA_NK100": "",          # 연속조회 키
            },
        )
        
        return Balance.from_kis(data)
