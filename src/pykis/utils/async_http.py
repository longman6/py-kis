"""
PyKIS 비동기 HTTP 클라이언트

KIS API와의 비동기 HTTP 통신을 담당합니다.
"""

from typing import Any, Dict, Optional

import httpx

from pykis.exceptions import APIError, RateLimitError, raise_for_code


class AsyncHTTPClient:
    """
    KIS API 비동기 HTTP 클라이언트
    
    인증 헤더를 포함한 비동기 HTTP 요청을 수행합니다.
    """
    
    def __init__(self, base_url: str, auth: Any):
        """
        Args:
            base_url: API 기본 URL
            auth: AsyncAuthManager 인스턴스
        """
        self.base_url = base_url
        self.auth = auth
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        AsyncClient 인스턴스를 반환합니다 (지연 초기화).
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._client
    
    async def get(
        self,
        endpoint: str,
        tr_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        비동기 GET 요청을 수행합니다.
        
        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID (tr_id 헤더)
            params: 쿼리 파라미터
            
        Returns:
            API 응답 데이터
        """
        headers = await self.auth.get_headers()
        headers["tr_id"] = tr_id
        
        client = await self._get_client()
        resp = await client.get(endpoint, params=params, headers=headers)
        return self._handle_response(resp)
    
    async def post(
        self,
        endpoint: str,
        tr_id: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        비동기 POST 요청을 수행합니다.
        
        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID (tr_id 헤더)
            json: 요청 본문 (JSON)
            
        Returns:
            API 응답 데이터
        """
        headers = await self.auth.get_headers()
        headers["tr_id"] = tr_id
        
        client = await self._get_client()
        resp = await client.post(endpoint, json=json, headers=headers)
        return self._handle_response(resp)
    
    def _handle_response(self, resp: httpx.Response) -> Dict[str, Any]:
        """
        HTTP 응답을 처리합니다.
        """
        if resp.status_code == 429:
            raise RateLimitError("Rate limit exceeded (초당 20건 초과)")
        
        try:
            data = resp.json()
        except Exception as e:
            raise APIError(f"응답 파싱 오류: {e}")
        
        if data.get("rt_cd") != "0":
            msg_cd = data.get("msg_cd", "")
            msg1 = data.get("msg1", "Unknown error")
            raise_for_code(msg_cd, msg1)
        
        return data
    
    async def close(self) -> None:
        """
        HTTP 클라이언트를 종료합니다.
        """
        if self._client:
            await self._client.aclose()
            self._client = None
