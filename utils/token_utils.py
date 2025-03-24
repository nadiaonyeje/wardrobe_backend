from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your_secret_key"  # Make sure to use a strong secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Generate a JWT token for user authentication.

    :param data: Dictionary containing user-related claims (e.g., {"sub": user_email, "user_id": user_id})
    :param expires_delta: Optional expiration time override (default: 30 minutes)
    :return: Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    # Encode the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
