import reflex as rx
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import jwt
from datetime import datetime, timedelta, timezone
import os
import logging
from app.utils import supabase_client

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
SECRET_KEY = os.getenv("ENCRYPTION_SECRET", "default-secret-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_org_from_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API Key"
        )
    try:
        org_id = await supabase_client.get_org_id_from_api_key(api_key)
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
            )
        return org_id
    except Exception as e:
        logging.exception(f"API Key validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )