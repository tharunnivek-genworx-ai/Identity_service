# src/api/data/repositories/department_repository.py
"""Repository for department CRUD operations.
All queries are async. No business logic lives here — only DB access."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from src.api.data.models.postgres.departments import Department
from src.api.data.models.postgres.mentors import Mentor
from src.api.data.models.postgres.trainees import Trainee


class DepartmentRepository:

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, department_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.departmentid == department_id)
        )
        return result.scalars().first()

    async def get_by_code(self, code: str) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.departmentcode == code)
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.departmentname == name)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[Department], int]:
        """Return (page of departments, total count) for paginated listing."""
        count_result = await self.db.execute(
            select(func.count()).select_from(Department)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Department)
            .order_by(Department.createdat.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def create(
        self,
        departmentname: str,
        departmentcode: str,
        description: str | None,
        isactive: bool,
        createdby: UUID,
    ) -> Department:
        dept = Department(
            departmentname=departmentname,
            departmentcode=departmentcode,
            description=description,
            isactive=isactive,
            createdby=createdby,
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
        department.updatedat = datetime.now(timezone.utc)
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
                Mentor.departmentid == department_id,
                Mentor.isactive == True,
            )
        )
        mentor_count = mentor_result.scalar_one()

        trainee_result = await self.db.execute(
            select(func.count())
            .select_from(Trainee)
            .where(
                Trainee.departmentid == department_id,
                Trainee.isactive == True,
            )
        )
        trainee_count = trainee_result.scalar_one()

        return (mentor_count + trainee_count) > 0