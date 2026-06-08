# src/api/data/repositories/mentor_repository.py
"""Repository for mentor CRUD and lifecycle operations.
Flush before commit so the caller can read generated fields (UUID, timestamps)
before the transaction fully closes."""

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.api.data.models.postgres.mentors import Mentor


class MentorRepository:

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, mentor_id: UUID) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.mentorid == mentor_id)
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.email == email)
        )
        return result.scalars().first()

    async def get_by_employee_id(self, employee_id: str) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.employeeid == employee_id)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[Mentor], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(Mentor)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Mentor)
            .order_by(Mentor.createdat.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def create(
        self,
        email: str,
        passwordhash: str,
        fullname: str,
        designation: str,
        departmentid: UUID,
        createdby: UUID,
        employeeid: str | None = None,
        phone: str | None = None,
        profilepictureurl: str | None = None,
        isactive: bool = True,
    ) -> Mentor:
        mentor = Mentor(
            email=email,
            passwordhash=passwordhash,
            fullname=fullname,
            designation=designation,
            departmentid=departmentid,
            createdby=createdby,
            employeeid=employeeid,
            phone=phone,
            profilepictureurl=profilepictureurl,
            isactive=isactive,
        )
        self.db.add(mentor)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor

    async def update(self, mentor: Mentor, updates: dict) -> Mentor:
        for field, value in updates.items():
            setattr(mentor, field, value)
        mentor.updatedat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor

    async def deactivate(self, mentor: Mentor) -> Mentor:
        """Soft-delete: set isactive=False and stamp deletedat."""
        mentor.isactive = False
        mentor.deletedat = datetime.now(timezone.utc)
        mentor.updatedat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor

    async def reactivate(self, mentor: Mentor) -> Mentor:
        """Reverse a soft-delete: set isactive=True and clear deletedat (EC-29)."""
        mentor.isactive = True
        mentor.deletedat = None
        mentor.updatedat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mentor)
        return mentor