"""Repository for auth operations: multi-role lookup by email across
itadmins, mentors, and trainees. Each role lives in its own table —
there is no shared User table in StudyGuru."""

from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.models.postgres.Identity_models.it_admin import ITAdmin
from src.api.data.models.postgres.Identity_models.mentors import Mentor
from src.api.data.models.postgres.Identity_models.revoked_token import RevokedToken
from src.api.data.models.postgres.Identity_models.trainees import Trainee


class AuthRepository:
    """Handles all DB reads/writes needed by the auth flow.

    Role resolution strategy:
        Login attempts check all three role tables in order:
        ITAdmin → Mentor → Trainee. The first match wins.
        This avoids a shared users table while keeping auth in one repo.
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    # ── Lookup helpers ──────────────────────────────────────────────

    async def get_itadmin_by_email(self, email: str) -> ITAdmin | None:
        result = await self.db.execute(select(ITAdmin).where(ITAdmin.email == email))
        return cast(ITAdmin | None, result.scalars().first())

    async def get_mentor_by_email(self, email: str) -> Mentor | None:
        result = await self.db.execute(select(Mentor).where(Mentor.email == email))
        return cast(Mentor | None, result.scalars().first())

    async def get_trainee_by_email(self, email: str) -> Trainee | None:
        result = await self.db.execute(select(Trainee).where(Trainee.email == email))
        return cast(Trainee | None, result.scalars().first())

    # ── Refresh token blocklist (for logout / revocation) ───────────
    # Store revoked JTIs in a simple table: revokedtokens(jti, revoked_at)
    # Create this table in your Alembic migration for the identity service.

    async def revoke_token(self, jti: str) -> None:
        """Insert a JTI into the revocation blocklist."""
        revoked = RevokedToken(jti=jti)
        self.db.add(revoked)
        await self.db.commit()

    async def is_token_revoked(self, jti: str) -> bool:
        """Return True if the given JTI has been revoked (logout was called)."""
        result = await self.db.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        return result.scalars().first() is not None
