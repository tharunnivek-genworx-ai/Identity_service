# src/api/data/repositories/trainee_repository.py
"""Repository for trainee CRUD and lifecycle operations.
Mirrors mentor_repository structure — same flush-commit-refresh pattern."""

from uuid import UUID
from datetime import datetime, timezone, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.api.data.models.postgres.Identity_models.trainees import Trainee


class TraineeRepository:

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, trainee_id: UUID) -> Trainee | None:
        result = await self.db.execute(
            select(Trainee).where(Trainee.traineeid == trainee_id)
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Trainee | None:
        result = await self.db.execute(
            select(Trainee).where(Trainee.email == email)
        )
        return result.scalars().first()

    async def get_by_employee_id(self, employee_id: str) -> Trainee | None:
        result = await self.db.execute(
            select(Trainee).where(Trainee.employeeid == employee_id)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[Trainee], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(Trainee)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Trainee)
            .order_by(Trainee.createdat.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def create(
        self,
        email: str,
        passwordhash: str,
        fullname: str,
        departmentid: UUID,
        createdby: UUID,
        employeeid: str | None = None,
        dob: date | None = None,
        phone: str | None = None,
        profilepictureurl: str | None = None,
        joiningdate: date | None = None,
        isactive: bool = True,
    ) -> Trainee:
        trainee = Trainee(
            email=email,
            passwordhash=passwordhash,
            fullname=fullname,
            departmentid=departmentid,
            createdby=createdby,
            employeeid=employeeid,
            dob=dob,
            phone=phone,
            profilepictureurl=profilepictureurl,
            joiningdate=joiningdate,
            isactive=isactive,
        )
        self.db.add(trainee)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def update(self, trainee: Trainee, updates: dict) -> Trainee:
        for field, value in updates.items():
            setattr(trainee, field, value)
        trainee.updatedat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def deactivate(self, trainee: Trainee) -> Trainee:
        """Soft-delete: set isactive=False and stamp deletedat (EC-28)."""
        trainee.isactive = False
        trainee.deletedat = datetime.now(timezone.utc)
        trainee.updatedat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee

    async def reactivate(self, trainee: Trainee) -> Trainee:
        """Reverse soft-delete: clear deletedat, set isactive=True (EC-29)."""
        trainee.isactive = True
        trainee.deletedat = None
        trainee.updatedat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(trainee)
        return trainee