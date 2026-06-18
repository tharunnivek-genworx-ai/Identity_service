"""Department service: all business logic for IT Admin department management.

Endpoints served (Section 3.5.2):
  POST  /admin/departments          → create_department
  GET   /admin/departments          → list_departments
  GET   /admin/departments/:id      → get_department
  PATCH /admin/departments/:id      → update_department
"""

import math
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.exceptions.identity_exceptions.department_exceptions import (
    DepartmentCodeAlreadyExistsException,
    DepartmentHasActiveMembersException,
    DepartmentNameAlreadyExistsException,
    DepartmentNotFoundException,
)
from src.api.data.repositories.identity_repository.department_repository import (
    DepartmentRepository,
)
from src.api.schemas.identity_schemas.departments_schema import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
)
from src.api.schemas.identity_schemas.listing_endpoints import (
    DepartmentListParams,
    DepartmentListResponse,
)


class DepartmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_department(
        self,
        payload: DepartmentCreate,
        created_by: UUID,
    ) -> DepartmentOut:
        repo = DepartmentRepository(self.session)

        # Guard: department code must be unique (business key)
        if await repo.get_by_code(payload.department_code):
            raise DepartmentCodeAlreadyExistsException(payload.department_code)

        # Guard: department name must be unique (UX sanity check)
        if await repo.get_by_name(payload.department_name):
            raise DepartmentNameAlreadyExistsException(payload.department_name)

        dept = await repo.create(
            department_name=payload.department_name,
            department_code=payload.department_code.upper(),  # normalize to uppercase
            description=payload.description,
            is_active=payload.is_active,
            created_by=created_by,
        )
        return cast(DepartmentOut, DepartmentOut.model_validate(dept))

    async def list_departments(
        self, params: DepartmentListParams
    ) -> DepartmentListResponse:
        repo = DepartmentRepository(self.session)
        skip = (params.page - 1) * params.limit
        departments, total = await repo.get_all(
            skip=skip, limit=params.limit, is_active=params.is_active
        )
        pages = math.ceil(total / params.limit) if total > 0 else 1

        return DepartmentListResponse(
            items=[DepartmentOut.model_validate(d) for d in departments],
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )

    async def get_department(self, department_id: UUID) -> DepartmentOut:
        repo = DepartmentRepository(self.session)
        dept = await repo.get_by_id(department_id)
        if not dept:
            raise DepartmentNotFoundException(str(department_id))
        return cast(DepartmentOut, DepartmentOut.model_validate(dept))

    async def update_department(
        self,
        department_id: UUID,
        payload: DepartmentUpdate,
    ) -> DepartmentOut:
        repo = DepartmentRepository(self.session)
        dept = await repo.get_by_id(department_id)
        if not dept:
            raise DepartmentNotFoundException(str(department_id))

        updates = payload.model_dump(exclude_unset=True)

        # Guard: if name is changing, ensure uniqueness
        if "department_name" in updates:
            existing = await repo.get_by_name(updates["department_name"])
            if existing and existing.department_id != department_id:
                raise DepartmentNameAlreadyExistsException(updates["department_name"])

        # Guard: if deactivating, ensure no active members remain
        if updates.get("is_active") is False:
            if await repo.has_active_members(department_id):
                raise DepartmentHasActiveMembersException()

        dept = await repo.update(dept, updates)
        return cast(DepartmentOut, DepartmentOut.model_validate(dept))
