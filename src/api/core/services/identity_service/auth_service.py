# src/api/core/services/auth_service.py
"""Auth service: login (all 3 roles), refresh, and logout.

Flow per design doc Section 3.5.1:
  POST /auth/login   → verify credentials → return access + refresh tokens
  POST /auth/refresh → validate refresh token jti → return new access token
  POST /auth/logout  → blocklist refresh token jti → session is dead

Role detection: ITAdmin is checked first (only one per org), then Mentor,
then Trainee. First email match wins.
"""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.repositories.identity_repository.auth_repository import AuthRepository
from src.api.schemas.identity_schemas.auth_schema import LoginRequest, LoginResponse, RefreshRequest
from src.api.core.exceptions.identity_exceptions.auth_exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    TokenRevokedException,
    AccountDeactivatedException,
)
from src.api.config.dbconfig import settings
from src.api.utils.password import verify_password
from src.api.utils.tokens import create_token, decode_token


class AuthService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, request: LoginRequest) -> LoginResponse:
        """Authenticate any role by email+password and return both tokens."""
        repo = AuthRepository(self.session)

        # Resolve which table this email belongs to
        user = await repo.get_itadmin_by_email(request.email)
        role = "itadmin"

        if user is None:
            user = await repo.get_mentor_by_email(request.email)
            role = "mentor"

        if user is None:
            user = await repo.get_trainee_by_email(request.email)
            role = "trainee"

        # No match across any role table
        if user is None:
            raise InvalidCredentialsException()

        # Account must be active before we check the password
        if not user.isactive:
            raise AccountDeactivatedException()

        # Verify password
        if not verify_password(request.password, user.passwordhash):
            raise InvalidCredentialsException()

        # Resolve the PK field name per role
        user_id_field = {
            "itadmin": "itadminid",
            "mentor": "mentorid",
            "trainee": "traineeid",
        }[role]
        user_id = str(getattr(user, user_id_field))

        # Build tokens
        access_token = create_token(
            data={"sub": user_id, "role": role},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        refresh_token = create_token(
            data={"sub": user_id, "role": role, "token_type": "refresh"},
            expires_delta=timedelta(days=settings.refresh_token_expire_days),
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_minutes=settings.access_token_expire_minutes,
            refresh_token_expires_in_days=settings.refresh_token_expire_days,
        )

    async def refresh(self, request: RefreshRequest) -> dict:
        """Issue a new access token from a valid, non-revoked refresh token."""
        repo = AuthRepository(self.session)

        payload = decode_token(request.refresh_token)

        # Must be a refresh token, not an access token
        if payload.get("token_type") != "refresh":
            raise InvalidTokenException("Not a refresh token.")

        jti = payload.get("jti")
        if not jti:
            raise InvalidTokenException("Token is missing jti claim.")

        # Check revocation blocklist
        if await repo.is_token_revoked(jti):
            raise TokenRevokedException()

        # Issue new access token with same identity claims
        new_access_token = create_token(
            data={"sub": payload["sub"], "role": payload["role"]},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in_minutes": settings.access_token_expire_minutes,
        }

    async def logout(self, request) -> dict:
        """Blocklist the refresh token's jti so it can never be reused."""
        repo = AuthRepository(self.session)

        payload = decode_token(request.refresh_token)
        jti = payload.get("jti")

        if not jti:
            raise InvalidTokenException("Token is missing jti claim.")

        await repo.revoke_token(jti)
        return {"detail": "Successfully logged out."}
