"""
Authentication and authorization for the Video Shooting Assistant API.

Provides JWT-based authentication and rate limiting middleware.

Requirements covered:
- 10.4: Implement rate limiting (100 req/min/user)
- 10.5: Implement JWT-based authentication
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from configs.settings import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.security.secret_key
ALGORITHM = settings.security.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.access_token_expire_minutes

# Rate limiting settings
RATE_LIMIT_PER_MINUTE = settings.security.rate_limit_per_minute

# Security scheme
security = HTTPBearer(auto_error=False)


# =========================================================================
# Models
# =========================================================================

class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model."""
    user_id: str
    username: str
    email: Optional[str] = None
    is_active: bool = True


# =========================================================================
# JWT Token Functions
# =========================================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData with decoded payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        exp: datetime = datetime.fromtimestamp(payload.get("exp", 0))
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(user_id=user_id, username=username, exp=exp)
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# =========================================================================
# Rate Limiting
# =========================================================================

class RateLimiter:
    """
    In-memory rate limiter.
    
    Implements a sliding window rate limiting algorithm.
    For production, consider using Redis-based rate limiting.
    
    Requirement 10.4: Rate limiting of 100 requests per minute per user.
    """
    
    def __init__(self, requests_per_minute: int = RATE_LIMIT_PER_MINUTE):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
    
    def _clean_old_requests(self, key: str, current_time: float) -> None:
        """Remove requests outside the current window."""
        cutoff = current_time - self.window_size
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]
    
    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Identifier for rate limiting (e.g., user_id or IP)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()
        self._clean_old_requests(key, current_time)
        
        request_count = len(self._requests[key])
        remaining = max(0, self.requests_per_minute - request_count)
        
        if request_count >= self.requests_per_minute:
            return False, 0
        
        self._requests[key].append(current_time)
        return True, remaining - 1
    
    def get_retry_after(self, key: str) -> int:
        """
        Get seconds until rate limit resets.
        
        Args:
            key: Identifier for rate limiting
            
        Returns:
            Seconds until oldest request expires
        """
        if not self._requests[key]:
            return 0
        
        oldest_request = min(self._requests[key])
        retry_after = int(oldest_request + self.window_size - time.time())
        return max(0, retry_after)


# Global rate limiter instance
rate_limiter = RateLimiter()


# =========================================================================
# Dependencies
# =========================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token.
    
    This dependency is optional - returns None if no token provided.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    token_data = verify_token(credentials.credentials)
    
    return User(
        user_id=token_data.user_id,
        username=token_data.username or "unknown",
    )


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> User:
    """
    Require authentication - raises 401 if not authenticated.
    
    Requirement 10.5: JWT-based authentication for all API endpoints.
    
    Args:
        credentials: HTTP Bearer credentials (required)
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If not authenticated
    """
    token_data = verify_token(credentials.credentials)
    
    return User(
        user_id=token_data.user_id,
        username=token_data.username or "unknown",
    )


async def rate_limit_check(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
) -> None:
    """
    Check rate limit for the current request.
    
    Requirement 10.4: Rate limiting of 100 requests per minute per user.
    
    Uses user_id if authenticated, otherwise uses client IP.
    
    Args:
        request: FastAPI request object
        user: Optional authenticated user
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Use user_id if authenticated, otherwise use IP
    if user:
        key = f"user:{user.user_id}"
    else:
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            key = f"ip:{forwarded.split(',')[0].strip()}"
        else:
            key = f"ip:{request.client.host if request.client else 'unknown'}"
    
    is_allowed, remaining = rate_limiter.is_allowed(key)
    
    if not is_allowed:
        retry_after = rate_limiter.get_retry_after(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


# =========================================================================
# Utility Functions
# =========================================================================

def generate_token_for_user(user_id: str, username: str) -> Token:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: User identifier
        username: Username
        
    Returns:
        Token object with access token
    """
    access_token = create_access_token(
        data={"sub": user_id, "username": username}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
