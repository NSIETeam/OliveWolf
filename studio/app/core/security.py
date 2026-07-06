from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple API key guard.

    Local development can leave STUDIO_API_KEY empty. Production deployments must set it.
    """
    if not settings.studio_api_key:
        return
    if x_api_key != settings.studio_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
