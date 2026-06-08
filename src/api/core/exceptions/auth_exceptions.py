# src/api/core/exceptions/identity_exceptions.py
"""
All application-level exceptions for the Identity & Org Service.
Each maps to a specific HTTP status code via FastAPI's exception handler
registration in main.py. Keeping exceptions here (not inside routes or
services) means every layer can raise them without circular imports.
"""

from fastapi import HTTPException, status


# ─────────────────────────────────────────────
# AUTH EXCEPTIONS
# ─────────────────────────────────────────────

class InvalidCredentialsException(HTTPException):
    """Raised when email/password combination does not match any account.
    Deliberately vague — do not reveal whether the email exists."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(HTTPException):
    """Raised when a JWT access or refresh token is missing, expired, or tampered."""
    def __init__(self, detail: str = "Token is invalid or expired."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenRevokedException(HTTPException):
    """Raised when a refresh token's jti appears in the revocation blocklist.
    Covers logout-then-reuse attacks."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsException(HTTPException):
    """Raised when the authenticated user's role is not allowed to access the route."""
    def __init__(self, required_role: str = ""):
        detail = (
            f"Access denied. Required role: {required_role}."
            if required_role
            else "You do not have permission to perform this action."
        )
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class AccountDeactivatedException(HTTPException):
    """Raised when a deactivated (is_active=False) account attempts to log in."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact your IT Admin.",
        )


