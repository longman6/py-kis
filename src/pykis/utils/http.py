"""
PyKIS HTTP 클라이언트

KIS API와의 HTTP 통신을 담당합니다.
"""

from typing import Any, Dict, Optional

import httpx

from pykis.exceptions import APIError, RateLimitError, raise_for_code


class HTTPClient:
    """
    KIS API HTTP 클라이언트
    
    인증 헤더를 포함한 HTTP 요청을 수행하고,
    응답의 성공/실패를 처리합니다.
    """
    
    def __init__(self, base_url: str, auth: Any):
        """
        Args:
            base_url: API 기본 URL
            auth: AuthManager 인스턴스
        """
        self.base_url = base_url
        self.auth = auth
        self._client = httpx.Client(base_url=base_url, timeout=30.0)
    
    def get(
        self,
        endpoint: str,
        tr_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        GET 요청을 수행합니다.
        
        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID (tr_id 헤더)
            params: 쿼리 파라미터
            
        Returns:
            API 응답 데이터
            
        Raises:
            APIError: API 오류 발생 시
            RateLimitError: Rate Limit 초과 시
        """
        headers = self.auth.get_headers()
        headers["tr_id"] = tr_id
        
        resp = self._client.get(endpoint, params=params, headers=headers)
        return self._handle_response(resp)
    
    def post(
        self,
        endpoint: str,
        tr_id: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        POST 요청을 수행합니다.
        
        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID (tr_id 헤더)
            json: 요청 본문 (JSON)
            
        Returns:
            API 응답 데이터
            
        Raises:
            APIError: API 오류 발생 시
            RateLimitError: Rate Limit 초과 시
        """
        headers = self.auth.get_headers()
        headers["tr_id"] = tr_id
        
        resp = self._client.post(endpoint, json=json, headers=headers)
        return self._handle_response(resp)
    
    def _handle_response(self, resp: httpx.Response) -> Dict[str, Any]:
        """
        HTTP 응답을 처리합니다.
        
        Args:
            resp: HTTP 응답 객체
            
        Returns:
            API 응답 데이터
            
        Raises:
            APIError: API 오류 발생 시
            RateLimitError: Rate Limit 초과 시
        """
        # Rate Limit 초과 (HTTP 429)
        if resp.status_code == 429:
            raise RateLimitError("Rate limit exceeded (초당 20건 초과)")
        
        try:
            data = resp.json()
        except Exception as e:
            raise APIError(f"응답 파싱 오류: {e}")
        
        # KIS API 결과 코드 확인 (rt_cd: "0" = 성공)
        if data.get("rt_cd") != "0":
            msg_cd = data.get("msg_cd", "")
            msg1 = data.get("msg1", "Unknown error")
            raise_for_code(msg_cd, msg1)
        
        return data
    
    def close(self) -> None:
        """
        HTTP 클라이언트를 종료합니다.
        """
        self._client.close()
