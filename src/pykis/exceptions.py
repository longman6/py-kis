"""
PyKIS 예외 클래스 정의

KIS API 사용 시 발생할 수 있는 다양한 오류를 처리하기 위한 예외 계층 구조를 정의합니다.
"""

from typing import Optional


class KISError(Exception):
    """
    PyKIS 기본 예외 클래스
    
    모든 PyKIS 관련 예외의 부모 클래스입니다.
    """
    
    def __init__(self, message: str, code: Optional[str] = None):
        """
        Args:
            message: 오류 메시지
            code: KIS API 오류 코드 (선택)
        """
        super().__init__(message)
        self.code = code


class AuthenticationError(KISError):
    """
    인증 오류
    
    API 키가 유효하지 않거나 인증에 실패한 경우 발생합니다.
    """
    pass


class TokenExpiredError(AuthenticationError):
    """
    토큰 만료 오류
    
    Access Token이 만료된 경우 발생합니다.
    """
    pass


class APIError(KISError):
    """
    API 호출 오류
    
    KIS API 호출 시 오류가 발생한 경우의 기본 예외입니다.
    """
    pass


class RateLimitError(APIError):
    """
    Rate Limit 초과 오류
    
    초당 요청 제한(20건)을 초과한 경우 발생합니다.
    """
    pass


class OrderError(APIError):
    """
    주문 오류
    
    주문 생성, 수정, 취소 시 발생하는 오류입니다.
    """
    pass


class InsufficientBalanceError(OrderError):
    """
    잔고 부족 오류
    
    주문 금액이 보유 잔고보다 큰 경우 발생합니다.
    """
    pass


class MarketClosedError(OrderError):
    """
    장 마감 오류
    
    장 운영 시간이 아닌 경우 발생합니다.
    """
    pass


# KIS API 에러 코드와 예외 클래스 매핑
ERROR_MAP = {
    "EGW00001": AuthenticationError,      # 인증 실패
    "EGW00002": TokenExpiredError,        # 토큰 만료
    "OPSP0001": InsufficientBalanceError, # 잔고 부족
    "OPSP0010": MarketClosedError,        # 장 마감
}


def raise_for_code(code: str, message: str) -> None:
    """
    KIS API 오류 코드에 해당하는 예외를 발생시킵니다.
    
    Args:
        code: KIS API 오류 코드
        message: 오류 메시지
        
    Raises:
        해당 코드에 매핑된 예외 또는 APIError
    """
    exc_class = ERROR_MAP.get(code, APIError)
    raise exc_class(message, code=code)
