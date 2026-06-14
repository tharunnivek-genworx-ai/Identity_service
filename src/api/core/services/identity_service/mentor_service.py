# src/api/core/services/mentor_service.py
"""Mentor service: IT Admin creates, deactivates, reactivates, and lists mentors.

Endpoints served (Section 3.5.2):
  POST  /admin/mentors              → create_mentor
  GET   /admin/mentors              → list_mentors
  GET   /admin/mentors/:id          → get_mentor
  PATCH /admin/mentors/:id/deactivate  → deactivate_mentor  (EC-27)
  PATCH /admin/mentors/:id/reactivate  → reactivate_mentor  (EC-29)
"""

import math
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.exceptions.identity_exceptions.department_exceptions import (
    DepartmentNotFoundException,
)
from src.api.core.exceptions.identity_exceptions.mentor_exceptions import (
    MentorAlreadyActiveException,
    MentorAlreadyDeactivatedException,
    MentorEmailAlreadyExistsException,
    MentorEmployeeIdAlreadyExistsException,
    MentorNotFoundException,
    TransferTargetNotFoundException,
)
from src.api.data.repositories.identity_repository.department_repository import (
    DepartmentRepository,
)
from src.api.data.repositories.identity_repository.mentor_repository import (
    MentorRepository,
)
from src.api.schemas.identity_schemas.listing_endpoints import (
    MentorListParams,
    MentorListResponse,
)
from src.api.schemas.identity_schemas.mentors_schema import (
    MentorCreate,
    MentorDeactivateRequest,
    MentorOut,
    MentorReactivateRequest,
)
from src.api.utils.identity_utils.build_mentor import build_mentor_out
from src.api.utils.password import hash_password


class MentorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_mentor(
        self,
        payload: MentorCreate,
        created_by: UUID,
    ) -> MentorOut:
        repo = MentorRepository(self.session)
        dept_repo = DepartmentRepository(self.session)

        # Guard: department must exist
        dept = await dept_repo.get_by_id(payload.department_id)
        if not dept:
            raise DepartmentNotFoundException(str(payload.department_id))

        # Guard: email unique across mentor table
        if await repo.get_by_email(payload.email):
            raise MentorEmailAlreadyExistsException(payload.email)

        # Guard: employeeid unique if provided
        if payload.employee_id and await repo.get_by_employee_id(payload.employee_id):
            raise MentorEmployeeIdAlreadyExistsException(payload.employee_id)

        password_hash = hash_password(payload.password)

        mentor = await repo.create(
            email=payload.email,
            password_hash=password_hash,
            full_name=payload.full_name,
            designation=payload.designation,
            department_id=payload.department_id,
            created_by=created_by,
            employee_id=payload.employee_id,
            phone=payload.phone,
            profile_picture_url=payload.profile_picture_url,
            is_active=payload.is_active,
        )
        return build_mentor_out(mentor)

    async def list_mentors(self, params: MentorListParams) -> MentorListResponse:
        repo = MentorRepository(self.session)
        skip = (params.page - 1) * params.limit
        mentors, total = await repo.get_all(
            skip=skip, limit=params.limit, is_active=params.is_active
        )
        pages = math.ceil(total / params.limit) if total > 0 else 1

        return MentorListResponse(
            items=[build_mentor_out(m) for m in mentors],
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )

    async def get_mentor(self, mentor_id: UUID) -> MentorOut:
        repo = MentorRepository(self.session)
        mentor = await repo.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundException(str(mentor_id))
        return build_mentor_out(mentor)

    async def deactivate_mentor(
        self,
        mentor_id: UUID,
        payload: MentorDeactivateRequest,
    ) -> MentorOut:
        """Soft-delete a mentor. Optionally records a space transfer target (EC-27).

        Note: space ownership transfer (e_spaces.transferred_to_mentor_id) is handled
        by the Space & Topic Service. This service validates the transfer target and
        stores the target ID on the mentor row
        so the Space service can query it.
        """
        repo = MentorRepository(self.session)

        mentor = await repo.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundException(str(mentor_id))

        if not mentor.is_active:
            raise MentorAlreadyDeactivatedException()

        # EC-27: validate transfer target if provided
        if payload.transferred_to_mentor_id:
            target = await repo.get_by_id(payload.transferred_to_mentor_id)
            if not target or not target.is_active:
                raise TransferTargetNotFoundException(
                    str(payload.transferred_to_mentor_id)
                )

        mentor = await repo.deactivate(mentor)
        return build_mentor_out(mentor)

    async def reactivate_mentor(
        self,
        mentor_id: UUID,
        payload: MentorReactivateRequest,
    ) -> MentorOut:
        """Re-enable a soft-deleted mentor account. Restores all prior data (EC-29)."""
        repo = MentorRepository(self.session)

        mentor = await repo.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundException(str(mentor_id))

        if mentor.is_active:
            raise MentorAlreadyActiveException()

        mentor = await repo.reactivate(mentor)
        return build_mentor_out(mentor)
