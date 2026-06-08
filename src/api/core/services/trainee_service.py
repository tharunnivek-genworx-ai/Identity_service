# src/api/core/services/trainee_service.py
"""Trainee service: IT Admin creates, deactivates, reactivates, and lists trainees.

Endpoints served (Section 3.5.2):
  POST  /admin/trainees                  → create_trainee
  GET   /admin/trainees                  → list_trainees
  GET   /admin/trainees/:id              → get_trainee
  PATCH /admin/trainees/:id/deactivate   → deactivate_trainee  (EC-28)
  PATCH /admin/trainees/:id/reactivate   → reactivate_trainee  (EC-29)
"""

import math
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.repositories.trainee_repository import TraineeRepository
from src.api.data.repositories.department_repository import DepartmentRepository
from src.api.schemas.trainees_schema import TraineeCreate, TraineeOut, TraineeDeactivateRequest, TraineeReactivateRequest
from src.api.schemas.listing_endpoints import TraineeListResponse, PageParams
from src.api.core.exceptions.trainee_exceptions import (
    TraineeNotFoundException,
    TraineeEmailAlreadyExistsException,
    TraineeEmployeeIdAlreadyExistsException,
    TraineeAlreadyDeactivatedException,
    TraineeAlreadyActiveException,
)
from src.api.core.exceptions.department_exceptions import DepartmentNotFoundException
from src.api.utils.password import hash_password


class TraineeService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_trainee(
        self,
        payload: TraineeCreate,
        created_by: UUID,
    ) -> TraineeOut:
        repo = TraineeRepository(self.session)
        dept_repo = DepartmentRepository(self.session)

        # Guard: department must exist
        dept = await dept_repo.get_by_id(payload.departmentid)
        if not dept:
            raise DepartmentNotFoundException(str(payload.departmentid))

        # Guard: email unique across trainee table
        if await repo.get_by_email(payload.email):
            raise TraineeEmailAlreadyExistsException(payload.email)

        # Guard: employeeid unique if provided
        if payload.employeeid and await repo.get_by_employee_id(payload.employeeid):
            raise TraineeEmployeeIdAlreadyExistsException(payload.employeeid)

        passwordhash = hash_password(payload.password)

        trainee = await repo.create(
            email=payload.email,
            passwordhash=passwordhash,
            fullname=payload.fullname,
            departmentid=payload.departmentid,
            createdby=created_by,
            employeeid=payload.employeeid,
            dob=payload.dob,
            phone=payload.phone,
            profilepictureurl=payload.profilepictureurl,
            joiningdate=payload.joiningdate,
            isactive=payload.isactive,
        )
        return TraineeOut.model_validate(trainee)

    async def list_trainees(self, params: PageParams) -> TraineeListResponse:
        repo = TraineeRepository(self.session)
        skip = (params.page - 1) * params.limit
        trainees, total = await repo.get_all(skip=skip, limit=params.limit)
        pages = math.ceil(total / params.limit) if total > 0 else 1

        return TraineeListResponse(
            items=[TraineeOut.model_validate(t) for t in trainees],
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )

    async def get_trainee(self, trainee_id: UUID) -> TraineeOut:
        repo = TraineeRepository(self.session)
        trainee = await repo.get_by_id(trainee_id)
        if not trainee:
            raise TraineeNotFoundException(str(trainee_id))
        return TraineeOut.model_validate(trainee)

    async def deactivate_trainee(
        self,
        trainee_id: UUID,
        payload: TraineeDeactivateRequest,
    ) -> TraineeOut:
        """Soft-delete a trainee. All progress and attempt history is retained (EC-28)."""
        repo = TraineeRepository(self.session)

        trainee = await repo.get_by_id(trainee_id)
        if not trainee:
            raise TraineeNotFoundException(str(trainee_id))

        if not trainee.isactive:
            raise TraineeAlreadyDeactivatedException()

        trainee = await repo.deactivate(trainee)
        return TraineeOut.model_validate(trainee)

    async def reactivate_trainee(
        self,
        trainee_id: UUID,
        payload: TraineeReactivateRequest,
    ) -> TraineeOut:
        """Re-enable a soft-deleted trainee. Restores all historical data (EC-29)."""
        repo = TraineeRepository(self.session)

        trainee = await repo.get_by_id(trainee_id)
        if not trainee:
            raise TraineeNotFoundException(str(trainee_id))

        if trainee.isactive:
            raise TraineeAlreadyActiveException()

        trainee = await repo.reactivate(trainee)
        return TraineeOut.model_validate(trainee)
