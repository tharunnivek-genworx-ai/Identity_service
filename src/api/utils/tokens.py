import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt

from src.api.config.dbconfig import settings
from src.api.core.exceptions.identity_exceptions.auth_exceptions import (
    InvalidTokenException,
)


def create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    now = datetime.now(UTC)
    payload.update(
        {
            "iat": now,
            "exp": now + expires_delta,
            "jti": str(uuid.uuid4()),
        }
    )
    return cast(
        str, jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    )


def decode_token(
    token: str,
    *,
    expired_message: str = "Token has expired.",
    invalid_message: str = "Token is invalid.",
) -> dict[str, Any]:
    try:
        return cast(
            dict[str, Any],
            jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]),
        )
    except jwt.ExpiredSignatureError:
        raise InvalidTokenException(expired_message) from None
    except jwt.InvalidTokenError:
        raise InvalidTokenException(invalid_message) from None
