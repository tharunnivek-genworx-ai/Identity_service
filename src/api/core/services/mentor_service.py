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

from src.api.data.repositories.mentor_repository import MentorRepository
from src.api.data.repositories.department_repository import DepartmentRepository
from src.api.schemas.mentors_schema import MentorCreate, MentorOut, MentorDeactivateRequest, MentorReactivateRequest
from src.api.schemas.listing_endpoints import MentorListResponse, PageParams
from src.api.core.exceptions.mentor_exceptions import (
    MentorNotFoundException,
    MentorEmailAlreadyExistsException,
    MentorEmployeeIdAlreadyExistsException,
    MentorAlreadyDeactivatedException,
    MentorAlreadyActiveException,
    TransferTargetNotFoundException,
)
from src.api.core.exceptions.department_exceptions import DepartmentNotFoundException
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
        dept = await dept_repo.get_by_id(payload.departmentid)
        if not dept:
            raise DepartmentNotFoundException(str(payload.departmentid))

        # Guard: email unique across mentor table
        if await repo.get_by_email(payload.email):
            raise MentorEmailAlreadyExistsException(payload.email)

        # Guard: employeeid unique if provided
        if payload.employeeid and await repo.get_by_employee_id(payload.employeeid):
            raise MentorEmployeeIdAlreadyExistsException(payload.employeeid)

        passwordhash = hash_password(payload.password)

        mentor = await repo.create(
            email=payload.email,
            passwordhash=passwordhash,
            fullname=payload.fullname,
            designation=payload.designation,
            departmentid=payload.departmentid,
            createdby=created_by,
            employeeid=payload.employeeid,
            phone=payload.phone,
            profilepictureurl=payload.profilepictureurl,
            isactive=payload.isactive,
        )
        return MentorOut.model_validate(mentor) #maps that ORM object into the response schema and enforces types again (UUIDs, timestamps, etc.).

    async def list_mentors(self, params: PageParams) -> MentorListResponse:
        repo = MentorRepository(self.session)
        skip = (params.page - 1) * params.limit
        mentors, total = await repo.get_all(skip=skip, limit=params.limit)
        pages = math.ceil(total / params.limit) if total > 0 else 1

        return MentorListResponse(
            items=[MentorOut.model_validate(m) for m in mentors],
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
        return MentorOut.model_validate(mentor)

    async def deactivate_mentor(
        self,
        mentor_id: UUID,
        payload: MentorDeactivateRequest,
    ) -> MentorOut:
        """Soft-delete a mentor. Optionally records a space transfer target (EC-27).

        Note: the actual space ownership transfer (setting e_spaces.transferred_to_mentor_id)
        is performed by the Space & Topic Service. This service only validates that the
        transfer target exists and is active, then stores the target ID on the mentor row
        so the Space service can query it.
        """
        repo = MentorRepository(self.session)

        mentor = await repo.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundException(str(mentor_id))

        if not mentor.isactive:
            raise MentorAlreadyDeactivatedException()

        # EC-27: validate transfer target if provided
        if payload.transferred_to_mentor_id:
            target = await repo.get_by_id(payload.transferred_to_mentor_id)
            if not target or not target.isactive:
                raise TransferTargetNotFoundException(str(payload.transferred_to_mentor_id))

        mentor = await repo.deactivate(mentor)
        return MentorOut.model_validate(mentor)

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

        if mentor.isactive:
            raise MentorAlreadyActiveException()

        mentor = await repo.reactivate(mentor)
        return MentorOut.model_validate(mentor)
