# src/api/data/repositories/identity_repository/mentor_repository.py
"""Repository for mentor CRUD and lifecycle operations.
Flush before commit so the caller can read generated fields (UUID, timestamps)
before the transaction fully closes."""

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.api.data.models.postgres.Identity_models.mentors import Mentor


class MentorRepository:

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, mentor_id: UUID) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.mentor_id == mentor_id).options(selectinload(Mentor.department))
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.email == email).options(selectinload(Mentor.department))
        )
        return result.scalars().first()

    async def get_by_employee_id(self, employee_id: str) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.employee_id == employee_id).options(selectinload(Mentor.department))
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[Mentor], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(Mentor)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Mentor)
            .options(selectinload(Mentor.department))
            .order_by(Mentor.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
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
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor

    async def update(self, mentor: Mentor, updates: dict) -> Mentor:
        for field, value in updates.items():
            setattr(mentor, field, value)
        mentor.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor

    async def deactivate(self, mentor: Mentor) -> Mentor:
        """Soft-delete: set is_active=False and stamp deleted_at."""
        mentor.is_active = False
        mentor.deleted_at = datetime.now(timezone.utc)
        mentor.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor

    async def reactivate(self, mentor: Mentor) -> Mentor:
        """Reverse a soft-delete: set is_active=True and clear deleted_at (EC-29)."""
        mentor.is_active = True
        mentor.deleted_at = None
        mentor.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor