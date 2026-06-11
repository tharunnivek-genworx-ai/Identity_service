# src/api/data/repositories/department_repository.py
"""Repository for department CRUD operations.
All queries are async. No business logic lives here — only DB access."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.models.postgres.Identity_models.departments import Department
from src.api.data.models.postgres.Identity_models.mentors import Mentor
from src.api.data.models.postgres.Identity_models.trainees import Trainee


class DepartmentRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, department_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.department_id == department_id)
        )
        return cast(Department | None, result.scalars().first())

    async def get_by_code(self, code: str) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.department_code == code)
        )
        return cast(Department | None, result.scalars().first())

    async def get_by_name(self, name: str) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.department_name == name)
        )
        return cast(Department | None, result.scalars().first())

    async def get_all(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Department], int]:
        """Return (page of departments, total count) for paginated listing."""
        count_result = await self.db.execute(
            select(func.count()).select_from(Department)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Department)
            .order_by(Department.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def create(
        self,
        department_name: str,
        department_code: str,
        description: str | None,
        is_active: bool,
        created_by: UUID,
    ) -> Department:
        dept = Department(
            department_name=department_name,
            department_code=department_code,
            description=description,
            is_active=is_active,
            created_by=created_by,
        )
        self.db.add(dept)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def update(self, department: Department, updates: dict) -> Department:
        """Apply a dict of field→value updates to the department and commit."""
        for field, value in updates.items():
            setattr(department, field, value)
        department.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def has_active_members(self, department_id: UUID) -> bool:
        """Return True if any active mentor or trainee belongs to this department.
        Used to block deactivation when members still exist (FK RESTRICT guard)."""
        mentor_result = await self.db.execute(
            select(func.count())
            .select_from(Mentor)
            .where(
                Mentor.department_id == department_id,
                Mentor.is_active,
            )
        )
        mentor_count = mentor_result.scalar_one()

        trainee_result = await self.db.execute(
            select(func.count())
            .select_from(Trainee)
            .where(
                Trainee.department_id == department_id,
                Trainee.is_active,
            )
        )
        trainee_count = trainee_result.scalar_one()

        return bool((mentor_count + trainee_count) > 0)
