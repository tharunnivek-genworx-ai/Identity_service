# src/api/data/repositories/trainee_repository.py
"""Repository for trainee CRUD and lifecycle operations.
Mirrors mentor_repository structure — same flush-commit-refresh pattern."""

from datetime import UTC, date, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.models.postgres.Identity_models.trainees import Trainee


class TraineeRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, trainee_id: UUID) -> Trainee | None:
        result = await self.db.execute(
            select(Trainee).where(Trainee.trainee_id == trainee_id)
        )
        return cast(Trainee | None, result.scalars().first())

    async def get_by_email(self, email: str) -> Trainee | None:
        result = await self.db.execute(select(Trainee).where(Trainee.email == email))
        return cast(Trainee | None, result.scalars().first())

    async def get_by_employee_id(self, employee_id: str) -> Trainee | None:
        result = await self.db.execute(
            select(Trainee).where(Trainee.employee_id == employee_id)
        )
        return cast(Trainee | None, result.scalars().first())

    async def count_all_and_active(self) -> tuple[int, int]:
        total_result = await self.db.execute(select(func.count()).select_from(Trainee))
        active_result = await self.db.execute(
            select(func.count()).select_from(Trainee).where(Trainee.is_active.is_(True))
        )
        return total_result.scalar_one(), active_result.scalar_one()

    async def get_all(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Trainee], int]:
        count_result = await self.db.execute(select(func.count()).select_from(Trainee))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Trainee)
            .order_by(Trainee.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        department_id: UUID,
        created_by: UUID,
        employee_id: str | None = None,
        dob: date | None = None,
        phone: str | None = None,
        profile_picture_url: str | None = None,
        joining_date: date | None = None,
        is_active: bool = True,
    ) -> Trainee:
        trainee = Trainee(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            department_id=department_id,
            created_by=created_by,
            employee_id=employee_id,
            dob=dob,
            phone=phone,
            profile_picture_url=profile_picture_url,
            joining_date=joining_date,
            is_active=is_active,
        )
        self.db.add(trainee)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def update(self, trainee: Trainee, updates: dict) -> Trainee:
        for field, value in updates.items():
            setattr(trainee, field, value)
        trainee.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def deactivate(self, trainee: Trainee) -> Trainee:
        """Soft-delete: set is_active=False and stamp deleted_at (EC-28)."""
        trainee.is_active = False
        trainee.deleted_at = datetime.now(UTC)
        trainee.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def reactivate(self, trainee: Trainee) -> Trainee:
        """Reverse soft-delete: clear deleted_at, set is_active=True (EC-29)."""
        trainee.is_active = True
        trainee.deleted_at = None
        trainee.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def search_trainees(self, query: str, limit: int = 20) -> list[Trainee]:
        """Search trainees by name, email, or employee ID."""
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Trainee)
            .where(
                (Trainee.full_name.ilike(search_term))
                | (Trainee.email.ilike(search_term))
                | (Trainee.employee_id.ilike(search_term))
            )
            .limit(limit)
        )
        return list(result.scalars().all())
