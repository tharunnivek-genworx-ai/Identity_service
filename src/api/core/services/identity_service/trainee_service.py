# C:\CapStone\Identity_service\src\api\core\services\identity_service\trainee_service.py
"""Trainee service: IT Admin creates, deactivates, reactivates, and lists trainees.

Endpoints served (Section 3.5.2):
  POST  /admin/trainees                  → create_trainee
  GET   /admin/trainees                  → list_trainees
  GET   /admin/trainees/:id              → get_trainee
  PATCH /admin/trainees/:id/deactivate   → deactivate_trainee  (EC-28)
  PATCH /admin/trainees/:id/reactivate   → reactivate_trainee  (EC-29)
"""

import math
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.exceptions.identity_exceptions.department_exceptions import (
    DepartmentNotFoundException,
)
from src.api.core.exceptions.identity_exceptions.trainee_exceptions import (
    TraineeAlreadyActiveException,
    TraineeAlreadyDeactivatedException,
    TraineeEmailAlreadyExistsException,
    TraineeEmployeeIdAlreadyExistsException,
    TraineeNotFoundException,
)
from src.api.data.repositories.identity_repository.department_repository import (
    DepartmentRepository,
)
from src.api.data.repositories.identity_repository.trainee_repository import (
    TraineeRepository,
)
from src.api.schemas.identity_schemas.listing_endpoints import (
    PageParams,
    TraineeListResponse,
)
from src.api.schemas.identity_schemas.trainees_schema import (
    TraineeCreate,
    TraineeDeactivateRequest,
    TraineeOut,
    TraineeReactivateRequest,
)
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
        dept = await dept_repo.get_by_id(payload.department_id)
        if not dept:
            raise DepartmentNotFoundException(str(payload.department_id))

        # Guard: email unique across trainee table
        if await repo.get_by_email(payload.email):
            raise TraineeEmailAlreadyExistsException(payload.email)

        # Guard: employeeid unique if provided
        if payload.employee_id and await repo.get_by_employee_id(payload.employee_id):
            raise TraineeEmployeeIdAlreadyExistsException(payload.employee_id)

        password_hash = hash_password(payload.password)

        trainee = await repo.create(
            email=payload.email,
            password_hash=password_hash,
            full_name=payload.full_name,
            department_id=payload.department_id,
            created_by=created_by,
            employee_id=payload.employee_id,
            dob=payload.dob,
            phone=payload.phone,
            profile_picture_url=payload.profile_picture_url,
            joining_date=payload.joining_date,
            is_active=payload.is_active,
        )
        return cast(TraineeOut, TraineeOut.model_validate(trainee))

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
        return cast(TraineeOut, TraineeOut.model_validate(trainee))

    async def deactivate_trainee(
        self,
        trainee_id: UUID,
        payload: TraineeDeactivateRequest,
    ) -> TraineeOut:
        """Soft-delete a trainee. Progress and attempt history retained (EC-28)."""
        repo = TraineeRepository(self.session)

        trainee = await repo.get_by_id(trainee_id)
        if not trainee:
            raise TraineeNotFoundException(str(trainee_id))

        if not trainee.is_active:
            raise TraineeAlreadyDeactivatedException()

        trainee = await repo.deactivate(trainee)
        return cast(TraineeOut, TraineeOut.model_validate(trainee))

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

        if trainee.is_active:
            raise TraineeAlreadyActiveException()

        trainee = await repo.reactivate(trainee)
        return cast(TraineeOut, TraineeOut.model_validate(trainee))

    async def search_trainees(self, query: str, limit: int = 20) -> list[TraineeOut]:
        """Search trainees by name, email, or employee ID for mentor assignment."""
        repo = TraineeRepository(self.session)
        trainees = await repo.search_trainees(query, limit)
        return [TraineeOut.model_validate(t) for t in trainees]
