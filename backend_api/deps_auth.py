from fastapi import Header, HTTPException

from backend_api import settings


def require_device_ingest_token(x_device_token: str | None = Header(None, alias="X-Device-Token")) -> None:
    expected = settings.DEVICE_INGEST_SECRET
    if not expected:
        return
    if not x_device_token or x_device_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Device-Token")


def require_admin_secret(x_admin_token: str | None = Header(None, alias="X-Admin-Token")) -> None:
    expected = settings.ADMIN_API_SECRET
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin routes disabled. Set ADMIN_API_SECRET in the environment.",
        )
    if not x_admin_token or x_admin_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token")
