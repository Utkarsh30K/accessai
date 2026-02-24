from datetime import datetime, timedelta
from jose import JWTError, jwt
from ..config import settings


def create_access_token(user_id: str, email: str) -> str:
    """
    Create a JWT access token for the user.
    
    Args:
        user_id: The user's UUID
        email: The user's email address
    
    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token string
    
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
