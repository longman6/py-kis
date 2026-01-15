"""
계좌 API 테스트
"""

import pytest
from conftest import SAMPLE_BALANCE_RESPONSE


class TestFetchBalance:
    """fetch_balance 테스트"""
    
    def test_fetch_balance_success(self, mock_kis):
        """잔고 조회 성공"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_BALANCE_RESPONSE
        
        balance = kis.fetch_balance()
        
        # 계좌 요약
        assert balance.total == 55750000
        assert balance.free == 50000000
        assert balance.deposit == 50000000
        assert balance.total_pnl == 250000
        assert balance.total_pnl_percent == 0.45
    
    def test_fetch_balance_with_positions(self, mock_kis):
        """보유 종목 포함 잔고 조회"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_BALANCE_RESPONSE
        
        balance = kis.fetch_balance()
        
        assert len(balance.positions) == 1
        
        pos = balance.positions[0]
        assert pos.symbol == "005930"
        assert pos.name == "삼성전자"
        assert pos.amount == 100
        assert pos.average_price == 55000
        assert pos.current_price == 57500
        assert pos.unrealized_pnl == 250000
        assert pos.unrealized_pnl_percent == 4.55
    
    def test_fetch_balance_get_position(self, mock_kis):
        """특정 종목 보유 정보 조회"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = SAMPLE_BALANCE_RESPONSE
        
        balance = kis.fetch_balance()
        
        # 보유 종목 조회
        pos = balance.get_position("005930")
        assert pos is not None
        assert pos.symbol == "005930"
        
        # 미보유 종목 조회
        pos = balance.get_position("000660")
        assert pos is None
    
    def test_fetch_balance_empty(self, mock_kis):
        """보유 종목 없음"""
        kis, mock_http = mock_kis
        mock_http.get.return_value = {
            "rt_cd": "0",
            "output1": [],
            "output2": [
                {
                    "dnca_tot_amt": "50000000",
                    "prvs_rcdl_excc_amt": "50000000",
                    "tot_evlu_amt": "50000000",
                    "evlu_pfls_smtl_amt": "0",
                    "asst_icdc_erng_rt": "0",
                }
            ]
        }
        
        balance = kis.fetch_balance()
        
        assert len(balance.positions) == 0
        assert balance.total == 50000000
