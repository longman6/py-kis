"""
PyKIS 비동기 인증 매니저

KIS API Access Token의 비동기 발급, 저장, 갱신을 관리합니다.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from pykis.exceptions import AuthenticationError


class AsyncAuthManager:
    """
    KIS API 비동기 인증 매니저
    
    Access Token을 비동기로 관리하며, 다음 기능을 제공합니다:
    - 토큰 자동 발급 (비동기)
    - 토큰 캐싱 (파일 저장)
    - 토큰 만료 시 자동 갱신
    """
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        token_path: Optional[str] = None,
    ):
        """
        Args:
            app_key: KIS API App Key
            app_secret: KIS API App Secret
            base_url: API 기본 URL (실전/모의투자)
            token_path: 토큰 저장 경로 (기본: ~/.pykis/token_{hash}.json)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        
        # 토큰 저장 경로 (app_key 해시로 구분)
        if token_path:
            self._path = Path(token_path).expanduser()
        else:
            key_hash = hashlib.md5(app_key.encode()).hexdigest()[:8]
            self._path = Path(f"~/.pykis/token_{key_hash}.json").expanduser()
        
        self._token: Optional[str] = None
        self._expires: Optional[datetime] = None
        
        # 캐시된 토큰 로드 시도
        self._load_token()
    
    async def get_headers(self) -> dict:
        """
        API 요청에 필요한 헤더를 반환합니다.
        
        토큰이 만료되었거나 없는 경우 자동으로 갱신합니다.
        
        Returns:
            API 요청 헤더 딕셔너리
        """
        if self._is_expired():
            await self._refresh()
        
        return {
            "authorization": f"Bearer {self._token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _is_expired(self) -> bool:
        """
        토큰 만료 여부를 확인합니다.
        """
        if not self._token or not self._expires:
            return True
        return datetime.now() >= self._expires - timedelta(minutes=5)
    
    async def _refresh(self) -> None:
        """
        새로운 Access Token을 비동기로 발급받습니다.
        
        Raises:
            AuthenticationError: 토큰 발급 실패 시
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/oauth2/tokenP",
                    json={
                        "grant_type": "client_credentials",
                        "appkey": self.app_key,
                        "appsecret": self.app_secret,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                
                if "access_token" not in data:
                    raise AuthenticationError(
                        data.get("msg1", "토큰 발급 실패"),
                        code=data.get("msg_cd"),
                    )
                
                self._token = data["access_token"]
                self._expires = datetime.now() + timedelta(
                    seconds=data.get("expires_in", 86400)
                )
                self._save_token()
                
        except httpx.HTTPError as e:
            raise AuthenticationError(f"토큰 발급 HTTP 오류: {e}") from e
    
    def _load_token(self) -> None:
        """
        파일에 저장된 토큰을 로드합니다.
        """
        if not self._path.exists():
            return
        
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            exp = datetime.fromisoformat(data["expires_at"])
            
            if exp > datetime.now():
                self._token = data["token"]
                self._expires = exp
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
    
    def _save_token(self) -> None:
        """
        현재 토큰을 파일에 저장합니다.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({
                "token": self._token,
                "expires_at": self._expires.isoformat() if self._expires else None,
            }, ensure_ascii=False),
            encoding="utf-8",
        )
