# src/api/rest/routes/dependencies.py
"""Shared FastAPI dependencies for the Identity & Org Service.

get_db         → yields an async DB session (already written in database.py)
get_current_user → decodes the Bearer JWT and returns the token payload
require_role   → factory that returns a dependency enforcing a specific role
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.schemas.auth_schema import TokenPayload
from src.api.core.exceptions.auth_exceptions import (
    InsufficientPermissionsException,
)
from src.api.utils.tokens import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> TokenPayload:
    """Decode and validate the Bearer JWT on every protected request.
    Returns the typed TokenPayload so routes can read sub, role, jti."""
    payload = decode_token(
        credentials.credentials,
        expired_message="Access token has expired.",
        invalid_message="Access token is invalid.",
    )

    return TokenPayload(**payload)


def require_role(*roles: str):
    """Dependency factory. Usage:
        Depends(require_role("itadmin"))
        Depends(require_role("mentor", "itadmin"))
    """
    async def _guard(
        current_user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        if current_user.role not in roles:
            raise InsufficientPermissionsException(required_role=", ".join(roles))
        return current_user
    return _guard
