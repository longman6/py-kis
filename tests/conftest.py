"""
PyKIS 테스트 설정

pytest 픽스처 및 공통 설정을 정의합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def mock_auth():
    """모의 AuthManager"""
    auth = Mock()
    auth.get_headers.return_value = {
        "authorization": "Bearer mock_token",
        "appkey": "mock_app_key",
        "appsecret": "mock_app_secret",
        "Content-Type": "application/json; charset=utf-8",
    }
    return auth


@pytest.fixture
def mock_http_client():
    """모의 HTTPClient"""
    return Mock()


@pytest.fixture
def mock_kis():
    """모의 KIS 클라이언트"""
    with patch("pykis.client.AuthManager") as mock_auth_class:
        with patch("pykis.client.HTTPClient") as mock_http_class:
            # AuthManager 모킹
            mock_auth = Mock()
            mock_auth.get_headers.return_value = {
                "authorization": "Bearer mock_token",
                "appkey": "mock_app_key",
                "appsecret": "mock_app_secret",
            }
            mock_auth_class.return_value = mock_auth
            
            # HTTPClient 모킹
            mock_http = Mock()
            mock_http_class.return_value = mock_http
            
            from pykis import KIS
            kis = KIS(
                app_key="test_key",
                app_secret="test_secret",
                account_no="12345678-01",
                is_paper=True,
            )
            
            yield kis, mock_http


# 테스트용 샘플 응답 데이터
SAMPLE_PRICE_RESPONSE = {
    "rt_cd": "0",
    "msg_cd": "0000",
    "msg1": "정상처리",
    "output": {
        "stck_prpr": "57500",
        "stck_oprc": "57000",
        "stck_hgpr": "58000",
        "stck_lwpr": "56500",
        "acml_vol": "15000000",
        "prdy_vrss": "500",
        "prdy_vrss_sign": "2",
        "prdy_ctrt": "0.88",
        "hts_kor_isnm": "삼성전자",
    }
}

SAMPLE_ORDERBOOK_RESPONSE = {
    "rt_cd": "0",
    "msg_cd": "0000",
    "msg1": "정상처리",
    "output1": {
        "askp1": "57500",
        "askp2": "57600",
        "askp3": "57700",
        "bidp1": "57400",
        "bidp2": "57300",
        "bidp3": "57200",
        "askp_rsqn1": "25000",
        "askp_rsqn2": "30000",
        "askp_rsqn3": "20000",
        "bidp_rsqn1": "50000",
        "bidp_rsqn2": "40000",
        "bidp_rsqn3": "35000",
    }
}

SAMPLE_DAILY_PRICE_RESPONSE = {
    "rt_cd": "0",
    "msg_cd": "0000",
    "msg1": "정상처리",
    "output2": [
        {
            "stck_bsop_date": "20260114",
            "stck_oprc": "57000",
            "stck_hgpr": "58000",
            "stck_lwpr": "56500",
            "stck_clpr": "57500",
            "acml_vol": "15000000",
        },
        {
            "stck_bsop_date": "20260113",
            "stck_oprc": "56000",
            "stck_hgpr": "57500",
            "stck_lwpr": "55800",
            "stck_clpr": "57000",
            "acml_vol": "12000000",
        },
    ]
}

SAMPLE_ORDER_RESPONSE = {
    "rt_cd": "0",
    "msg_cd": "0000",
    "msg1": "정상처리",
    "output": {
        "ODNO": "0000123456",
        "ORD_TMD": "090000",
    }
}

SAMPLE_BALANCE_RESPONSE = {
    "rt_cd": "0",
    "msg_cd": "0000",
    "msg1": "정상처리",
    "output1": [
        {
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "hldg_qty": "100",
            "pchs_avg_pric": "55000.0000",
            "prpr": "57500",
            "evlu_amt": "5750000",
            "evlu_pfls_amt": "250000",
            "evlu_pfls_rt": "4.55",
        }
    ],
    "output2": [
        {
            "dnca_tot_amt": "50000000",
            "prvs_rcdl_excc_amt": "50000000",
            "tot_evlu_amt": "55750000",
            "evlu_pfls_smtl_amt": "250000",
            "asst_icdc_erng_rt": "0.45",
        }
    ]
}
