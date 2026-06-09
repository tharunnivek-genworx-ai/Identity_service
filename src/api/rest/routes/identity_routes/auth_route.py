# src/api/rest/routes/auth_route.py
"""Auth routes: login, refresh, logout.
No role guard needed — these are public endpoints (except logout
which just needs a valid refresh token in the body)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.clients.postgres.database import get_db
from src.api.core.services.identity_service.auth_service import AuthService
from src.api.schemas.identity_schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    LogoutRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate any role (itadmin / mentor / trainee) by email + password.
    Returns both an access token (60 min) and a refresh token (7 days)."""
    service = AuthService(db)
    return await service.login(payload)


@router.post("/refresh", response_model=dict)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token.
    The refresh token's jti must not appear in the revocation blocklist."""
    service = AuthService(db)
    return await service.refresh(payload)


@router.post("/logout", status_code=200)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the refresh token by adding its jti to the blocklist.
    After this, the refresh token can never be used again."""
    service = AuthService(db)
    return await service.logout(payload)