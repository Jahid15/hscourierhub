from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError
import datetime
from app.config import settings

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=settings.session_expiry_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.app_secret_key, algorithm="HS256")
    return encoded_jwt

async def get_current_user(request: Request):
    """Check API key header OR JWT cookie."""
    # Check API key first
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == settings.external_api_key:
        return {"type": "api_key", "authenticated": True}
        
    if not settings.external_api_key and api_key:
        pass # Handle case where external_api_key is not set

    # Check JWT cookie
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
        if datetime.datetime.utcnow().timestamp() > payload.get("exp", 0):
            raise HTTPException(status_code=401, detail="Session expired")
        return {"type": "session", "authenticated": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid session")

async def get_current_user_optional(request: Request):
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
