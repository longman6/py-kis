"""
PyKIS 상수 정의

KIS API 사용에 필요한 URL, 엔드포인트, TR_ID 및 Enum 상수를 정의합니다.
"""

from enum import Enum


class BaseURL:
    """
    KIS API 기본 URL
    
    실전투자와 모의투자 환경에 따른 URL을 정의합니다.
    """
    
    # REST API URL
    PRODUCTION = "https://openapi.koreainvestment.com:9443"
    PAPER = "https://openapivts.koreainvestment.com:29443"
    
    # WebSocket URL
    WS_PRODUCTION = "ws://ops.koreainvestment.com:21000"
    WS_PAPER = "ws://ops.koreainvestment.com:31000"


class Endpoint:
    """
    KIS API 엔드포인트
    
    각 API 기능별 경로를 정의합니다.
    """
    
    # 인증
    TOKEN = "/oauth2/tokenP"
    
    # 시세 (국내 주식)
    PRICE = "/uapi/domestic-stock/v1/quotations/inquire-price"
    ORDERBOOK = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
    DAILY_PRICE = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    
    # 주문 (국내 주식)
    ORDER = "/uapi/domestic-stock/v1/trading/order-cash"
    ORDER_MODIFY = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
    
    # 잔고
    BALANCE = "/uapi/domestic-stock/v1/trading/inquire-balance"
    OPEN_ORDERS = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"


class TrID:
    """
    KIS API 거래 ID (tr_id)
    
    API 요청 시 헤더에 포함할 거래 ID를 정의합니다.
    실전/모의투자에 따라 다른 ID를 사용합니다.
    """
    
    # 시세 조회 (실전/모의 동일)
    PRICE = "FHKST01010100"           # 현재가 조회
    ORDERBOOK = "FHKST01010200"       # 호가 조회
    DAILY_PRICE = "FHKST01010400"     # 일별 시세(OHLCV)
    
    # 주문 (실전)
    BUY = "TTTC0802U"                 # 매수
    SELL = "TTTC0801U"                # 매도
    MODIFY = "TTTC0803U"              # 정정/취소
    
    # 주문 (모의)
    BUY_PAPER = "VTTC0802U"           # 매수 (모의)
    SELL_PAPER = "VTTC0801U"          # 매도 (모의)
    MODIFY_PAPER = "VTTC0803U"        # 정정/취소 (모의)
    
    # 잔고 조회 (실전)
    BALANCE = "TTTC8434R"             # 잔고 조회
    OPEN_ORDERS = "TTTC8036R"         # 미체결 조회
    
    # 잔고 조회 (모의)
    BALANCE_PAPER = "VTTC8434R"       # 잔고 조회 (모의)
    OPEN_ORDERS_PAPER = "VTTC8036R"   # 미체결 조회 (모의)


class OrderSide(str, Enum):
    """
    주문 방향
    
    매수(buy) 또는 매도(sell)를 나타냅니다.
    """
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """
    주문 유형
    
    지정가(limit) 또는 시장가(market)를 나타냅니다.
    """
    LIMIT = "limit"
    MARKET = "market"


class OrderStatus(str, Enum):
    """
    주문 상태
    
    주문의 현재 상태를 나타냅니다.
    """
    OPEN = "open"           # 미체결 (접수/일부체결)
    CLOSED = "closed"       # 체결 완료
    CANCELED = "canceled"   # 취소됨


class MarketCode(str, Enum):
    """
    시장 구분 코드
    
    KIS API의 FID_COND_MRKT_DIV_CODE 값을 정의합니다.
    """
    STOCK = "J"   # 주식/ETF/ETN
