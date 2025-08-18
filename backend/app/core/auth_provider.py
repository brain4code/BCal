from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import JWTError, jwt
from ..core.config import settings
from ..models.user import User
from ..core.database import get_db
from sqlalchemy.orm import Session
import httpx
import logging

logger = logging.getLogger(__name__)


class AuthProvider(ABC):
    """Abstract base class for authentication providers"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate user and return User object"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token and return payload"""
        pass
    
    @abstractmethod
    def create_token(self, user: User) -> str:
        """Create authentication token for user"""
        pass


class LocalAuthProvider(AuthProvider):
    """Local JWT-based authentication provider"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate using local database"""
        from ..core.security import verify_password
        
        email = credentials.get("username")
        password = credentials.get("password")
        
        if not email or not password:
            return None
        
        db = next(get_db())
        user = db.query(User).filter(User.email == email).first()
        
        if user and verify_password(password, user.hashed_password):
            return user
        
        return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def create_token(self, user: User) -> str:
        """Create JWT token"""
        from ..core.security import create_access_token
        return create_access_token(data={"sub": user.email})


class Auth0Provider(AuthProvider):
    """Auth0 authentication provider"""
    
    def __init__(self):
        self.domain = settings.auth0_domain
        self.client_id = settings.auth0_client_id
        self.client_secret = settings.auth0_client_secret
        self.audience = settings.auth0_audience
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate using Auth0"""
        # Auth0 authentication is typically handled via OAuth flow
        # This method would handle the OAuth callback
        code = credentials.get("code")
        if not code:
            return None
        
        # Exchange code for token
        token_data = await self._exchange_code_for_token(code)
        if not token_data:
            return None
        
        # Get user info from Auth0
        user_info = await self._get_user_info(token_data["access_token"])
        if not user_info:
            return None
        
        # Find or create user in local database
        return await self._get_or_create_user(user_info)
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Auth0 token"""
        try:
            # Verify token with Auth0
            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            async with httpx.AsyncClient() as client:
                jwks_response = await client.get(jwks_url)
                jwks = jwks_response.json()
            
            # Verify token using Auth0's public key
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )
            return payload
        except Exception as e:
            logger.error(f"Auth0 token verification failed: {e}")
            return None
    
    def create_token(self, user: User) -> str:
        """Create local JWT token for Auth0 users"""
        from ..core.security import create_access_token
        return create_access_token(data={"sub": user.email, "auth0_user_id": user.auth0_user_id})
    
    async def _exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        try:
            token_url = f"https://{self.domain}/oauth/token"
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": settings.auth0_redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
        
        return None
    
    async def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Auth0"""
        try:
            userinfo_url = f"https://{self.domain}/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
        
        return None
    
    async def _get_or_create_user(self, user_info: Dict[str, Any]) -> Optional[User]:
        """Get or create user in local database"""
        db = next(get_db())
        
        # Check if user exists
        user = db.query(User).filter(User.auth0_user_id == user_info["sub"]).first()
        
        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                username=user_info.get("nickname", user_info["email"].split("@")[0]),
                full_name=user_info.get("name", ""),
                auth0_user_id=user_info["sub"],
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user


class GenericSSOProvider(AuthProvider):
    """Generic SSO authentication provider"""
    
    def __init__(self):
        self.issuer_url = settings.sso_issuer_url
        self.client_id = settings.sso_client_id
        self.client_secret = settings.sso_client_secret
        self.redirect_uri = settings.sso_redirect_uri
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate using generic SSO"""
        # Similar to Auth0 but for generic SSO providers
        code = credentials.get("code")
        if not code:
            return None
        
        # Exchange code for token
        token_data = await self._exchange_code_for_token(code)
        if not token_data:
            return None
        
        # Get user info from SSO provider
        user_info = await self._get_user_info(token_data["access_token"])
        if not user_info:
            return None
        
        # Find or create user in local database
        return await self._get_or_create_user(user_info)
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify SSO token"""
        try:
            # Verify token with SSO provider
            jwks_url = f"{self.issuer_url}/.well-known/jwks.json"
            async with httpx.AsyncClient() as client:
                jwks_response = await client.get(jwks_url)
                jwks = jwks_response.json()
            
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer_url
            )
            return payload
        except Exception as e:
            logger.error(f"SSO token verification failed: {e}")
            return None
    
    def create_token(self, user: User) -> str:
        """Create local JWT token for SSO users"""
        from ..core.security import create_access_token
        return create_access_token(data={"sub": user.email, "sso_user_id": user.sso_user_id})
    
    async def _exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        try:
            token_url = f"{self.issuer_url}/oauth/token"
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
        
        return None
    
    async def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from SSO provider"""
        try:
            userinfo_url = f"{self.issuer_url}/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
        
        return None
    
    async def _get_or_create_user(self, user_info: Dict[str, Any]) -> Optional[User]:
        """Get or create user in local database"""
        db = next(get_db())
        
        # Check if user exists
        user = db.query(User).filter(User.sso_user_id == user_info["sub"]).first()
        
        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                username=user_info.get("preferred_username", user_info["email"].split("@")[0]),
                full_name=user_info.get("name", ""),
                sso_user_id=user_info["sub"],
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user


def get_auth_provider() -> AuthProvider:
    """Get the configured authentication provider"""
    if settings.auth_provider == "auth0":
        return Auth0Provider()
    elif settings.auth_provider == "generic_sso":
        return GenericSSOProvider()
    else:
        return LocalAuthProvider()
