"""
인증 시스템 테스트
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestAuthManager:
    """AuthManager 테스트"""
    
    def test_token_expired_when_no_token(self):
        """토큰이 없으면 만료 상태"""
        with patch("pykis.auth.manager.httpx.Client"):
            from pykis.auth.manager import AuthManager
            
            auth = AuthManager(
                app_key="test_key",
                app_secret="test_secret",
                base_url="https://test.com",
                token_path="/tmp/test_token.json",
            )
            
            # 토큰이 없으면 만료 상태
            assert auth._is_expired() is True
    
    def test_token_refresh(self):
        """토큰 갱신"""
        with patch("pykis.auth.manager.httpx.Client") as mock_client:
            # HTTP 응답 모킹
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "new_token",
                "expires_in": 86400,
            }
            mock_response.raise_for_status = Mock()
            
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.post.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            from pykis.auth.manager import AuthManager
            
            auth = AuthManager(
                app_key="test_key",
                app_secret="test_secret",
                base_url="https://test.com",
                token_path="/tmp/test_token_refresh.json",
            )
            
            # 토큰 갱신
            auth._refresh()
            
            assert auth._token == "new_token"
            assert auth._expires is not None
    
    def test_get_headers(self):
        """헤더 생성"""
        with patch("pykis.auth.manager.httpx.Client") as mock_client:
            # HTTP 응답 모킹
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test_token",
                "expires_in": 86400,
            }
            mock_response.raise_for_status = Mock()
            
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.post.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            from pykis.auth.manager import AuthManager
            
            auth = AuthManager(
                app_key="test_key",
                app_secret="test_secret",
                base_url="https://test.com",
                token_path="/tmp/test_token_headers.json",
            )
            
            headers = auth.get_headers()
            
            assert "authorization" in headers
            assert headers["authorization"] == "Bearer test_token"
            assert headers["appkey"] == "test_key"
            assert headers["appsecret"] == "test_secret"


class TestExceptions:
    """예외 클래스 테스트"""
    
    def test_kis_error(self):
        """KISError 생성"""
        from pykis.exceptions import KISError
        
        error = KISError("테스트 오류", code="TEST001")
        
        assert str(error) == "테스트 오류"
        assert error.code == "TEST001"
    
    def test_raise_for_code(self):
        """에러 코드에 따른 예외 발생"""
        from pykis.exceptions import (
            raise_for_code,
            AuthenticationError,
            InsufficientBalanceError,
            APIError,
        )
        
        # 인증 오류
        with pytest.raises(AuthenticationError):
            raise_for_code("EGW00001", "인증 실패")
        
        # 잔고 부족
        with pytest.raises(InsufficientBalanceError):
            raise_for_code("OPSP0001", "잔고 부족")
        
        # 알 수 없는 코드는 APIError
        with pytest.raises(APIError):
            raise_for_code("UNKNOWN", "알 수 없는 오류")
