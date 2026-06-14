# src/api/rest/routes/admin_mentor_route.py
"""IT Admin mentor routes.

Every route here requires role='itadmin' enforced by require_role().
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.identity_service.mentor_service import MentorService
from src.api.core.services.space_node_service.space_service import SpaceService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.identity_schemas.listing_endpoints import (
    MentorListParams,
    MentorListResponse,
)
from src.api.schemas.identity_schemas.listing_endpoints import (
    PageParams as SpacePageParams,
)
from src.api.schemas.identity_schemas.mentors_schema import (
    MentorCreate,
    MentorDeactivateRequest,
    MentorOut,
    MentorReactivateRequest,
)
from src.api.schemas.space_node_schemas.space_schema import (
    AdminMentorSpaceOverviewResponse,
)

router = APIRouter(prefix="/admin/mentors", tags=["IT Admin"])

ITAdminUser = Annotated[TokenPayload, Depends(require_role("itadmin"))]


@router.post("", response_model=MentorOut, status_code=201)
async def create_mentor(
    payload: MentorCreate,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> MentorOut:
    """Create a new mentor account. Password is hashed in the service layer.
    The mentor's department must already exist."""
    service = MentorService(db)
    return await service.create_mentor(payload, created_by=UUID(str(current_user.sub)))


@router.get("", response_model=MentorListResponse)
async def list_mentors(
    current_user: ITAdminUser,
    params: MentorListParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> MentorListResponse:
    """List mentor accounts with pagination. Optional is_active filter."""
    service = MentorService(db)
    return await service.list_mentors(params)


@router.get("/{mentor_id}/spaces", response_model=AdminMentorSpaceOverviewResponse)
async def list_mentor_spaces(
    mentor_id: UUID,
    current_user: ITAdminUser,
    params: SpacePageParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> AdminMentorSpaceOverviewResponse:
    """List audit-owned spaces and spaces transferred to this mentor (EC-27)."""
    service = SpaceService(db)
    return await service.admin_list_spaces_for_mentor(
        mentor_id, current_user.role, params
    )


@router.get("/{mentor_id}", response_model=MentorOut)
async def get_mentor(
    mentor_id: UUID,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> MentorOut:
    """Fetch a single mentor by ID."""
    service = MentorService(db)
    return await service.get_mentor(mentor_id)


@router.patch("/{mentor_id}/deactivate", response_model=MentorOut)
async def deactivate_mentor(
    mentor_id: UUID,
    payload: MentorDeactivateRequest,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> MentorOut:
    """Soft-delete a mentor account (sets isactive=False, stamps deletedat).
    If transferred_to_mentor_id is provided, it is validated to be an active
    mentor - the Space service will use it for ownership transfer (EC-27)."""
    service = MentorService(db)
    return await service.deactivate_mentor(mentor_id, payload)


@router.patch("/{mentor_id}/reactivate", response_model=MentorOut)
async def reactivate_mentor(
    mentor_id: UUID,
    payload: MentorReactivateRequest,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> MentorOut:
    """Re-enable a soft-deleted mentor. Clears deletedat, sets isactive=True.
    All historical data (spaces, content, progress) is fully restored (EC-29)."""
    service = MentorService(db)
    return await service.reactivate_mentor(mentor_id, payload)
