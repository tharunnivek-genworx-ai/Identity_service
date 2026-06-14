# src/api/data/models/revoked_token.py
"""ORM model for the refresh token revocation blocklist.

Why this exists:
    JWTs are stateless by design — once issued, they are valid until expiry.
    The design doc requires POST /auth/logout to actually invalidate a refresh
    token so it can never be reused (even if it hasn't expired yet).
    The solution is to store the token's unique jti claim here on logout,
    and reject any refresh request whose jti appears in this table.

Table: revokedtokens
    Owned by: Identity & Org Service (add to identity_service/alembic/)
    Migration order: same migration file as itadmins/mentors/trainees —
    this table has no FKs to other services so it can be created first.

Cleanup note:
    This table will grow over time as tokens expire but their jtis remain.
    Add a periodic cleanup job (cron / Celery beat) that deletes rows where
    revokedat < NOW() - INTERVAL '7 days' (the refresh token max lifetime).
    Expired tokens are harmless in the blocklist but waste space long-term.
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class RevokedToken(Base):
    __tablename__ = "revokedtokens"

    # jti is the primary key — it is already globally unique (uuid4 generated
    # at token creation time in auth_service._create_token). Using it as PK
    # makes the existence check a single indexed lookup: SELECT WHERE jti = ?
    jti = Column(
        String(36),  # UUID string: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
        primary_key=True,
        nullable=False,
        index=True,  # explicit index even though PK — makes intent clear
    )

    # revokedat lets the cleanup job find and purge expired entries.
    # It is also useful for audit: "when did this user log out?"
    revoked_at = Column(
        "revokedat",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_now,
    )
