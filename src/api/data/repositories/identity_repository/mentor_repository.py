"""Repository for mentor CRUD and lifecycle operations.
Flush before commit so the caller can read generated fields (UUID, timestamps)
before the transaction fully closes."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.data.models.postgres.Identity_models.mentors import Mentor


class MentorRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, mentor_id: UUID) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor)
            .where(Mentor.mentor_id == mentor_id)
            .options(selectinload(Mentor.department))
        )
        return cast(Mentor | None, result.scalars().first())

    async def get_by_email(self, email: str) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor)
            .where(Mentor.email == email)
            .options(selectinload(Mentor.department))
        )
        return cast(Mentor | None, result.scalars().first())

    async def get_by_employee_id(self, employee_id: str) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor)
            .where(Mentor.employee_id == employee_id)
            .options(selectinload(Mentor.department))
        )
        return cast(Mentor | None, result.scalars().first())

    async def count_all_and_active(self) -> tuple[int, int]:
        total_result = await self.db.execute(select(func.count()).select_from(Mentor))
        active_result = await self.db.execute(
            select(func.count()).select_from(Mentor).where(Mentor.is_active.is_(True))
        )
        return total_result.scalar_one(), active_result.scalar_one()

    async def get_all(
        self, skip: int = 0, limit: int = 20, *, is_active: bool | None = None
    ) -> tuple[list[Mentor], int]:
        filters = []
        if is_active is not None:
            filters.append(Mentor.is_active.is_(is_active))

        count_stmt = select(func.count()).select_from(Mentor)
        list_stmt = (
            select(Mentor)
            .options(selectinload(Mentor.department))
            .order_by(Mentor.created_at.desc())
        )
        if filters:
            count_stmt = count_stmt.where(*filters)
            list_stmt = list_stmt.where(*filters)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        result = await self.db.execute(list_stmt.offset(skip).limit(limit))
        return result.scalars().all(), total

    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        designation: str,
        department_id: UUID,
        created_by: UUID,
        employee_id: str | None = None,
        phone: str | None = None,
        profile_picture_url: str | None = None,
        is_active: bool = True,
    ) -> Mentor:
        mentor = Mentor(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            designation=designation,
            department_id=department_id,
            created_by=created_by,
            employee_id=employee_id,
            phone=phone,
            profile_picture_url=profile_picture_url,
            is_active=is_active,
        )
        self.db.add(mentor)
        await self.db.flush()
        mentor_id = mentor.mentor_id
        await self.db.commit()
        reloaded = await self.get_by_id(mentor_id)
        assert reloaded is not None
        return reloaded

    async def update(self, mentor: Mentor, updates: dict) -> Mentor:
        mentor_id = mentor.mentor_id
        for field, value in updates.items():
            setattr(mentor, field, value)
        mentor.updated_at = datetime.now(UTC)
        await self.db.commit()
        reloaded = await self.get_by_id(mentor_id)
        assert reloaded is not None
        return reloaded

    async def deactivate(self, mentor: Mentor) -> Mentor:
        """Soft-delete: set is_active=False and stamp deleted_at."""
        mentor_id = mentor.mentor_id
        mentor.is_active = False
        mentor.deleted_at = datetime.now(UTC)
        mentor.updated_at = datetime.now(UTC)
        await self.db.commit()
        reloaded = await self.get_by_id(mentor_id)
        assert reloaded is not None
        return reloaded

    async def reactivate(self, mentor: Mentor) -> Mentor:
        """Reverse a soft-delete: set is_active=True and clear deleted_at (EC-29)."""
        mentor_id = mentor.mentor_id
        mentor.is_active = True
        mentor.deleted_at = None
        mentor.updated_at = datetime.now(UTC)
        await self.db.commit()
        reloaded = await self.get_by_id(mentor_id)
        assert reloaded is not None
        return reloaded
