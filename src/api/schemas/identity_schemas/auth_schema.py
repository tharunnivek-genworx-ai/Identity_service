from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class TokenPayload(BaseModel):
    """
    Decoded JWT payload. Validated on every protected request.

    Fields:
        sub  — UUID of the authenticated user (itadminid / mentorid / traineeid).
        role — Role encoded at login; drives all route-level access guards.
        exp  — Expiry unix timestamp (set by PyJWT automatically).
        iat  — Issued-at unix timestamp (set by PyJWT automatically).
               Required for refresh token age checks and audit logging.
        jti  — JWT ID (unique per token). Required to support logout/revocation:
               store jti in a refresh_token_blocklist table and reject reuse.
    """

    sub: UUID
    role: Literal["itadmin", "mentor", "trainee"]
    exp: int
    iat: int
    jti: str  # unique token ID — needed for refresh token revocation on logout


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(Token):
    """
    Returned on successful login.
    refresh_token_expires_in_days matches the design doc (7 days).
    """

    refresh_token: str
    refresh_token_expires_in_days: int = 7


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    """
    The refresh_token must be sent so the server can extract its jti
    and add it to the blocklist, preventing reuse after logout.
    """

    refresh_token: str
