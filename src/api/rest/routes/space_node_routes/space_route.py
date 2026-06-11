# src/api/rest/routes/space_route.py
"""Space routes: create, list, get, update, publish, transfer ownership,
add trainees, remove trainee, join via invite code.

Role guards:
  Mentor  — create, update, publish, add/remove trainees, get own spaces
  Trainee — join via invite code, get enrolled spaces
  ITAdmin — transfer ownership (called when deactivating a mentor, EC-27)

current_user is injected by get_current_user dependency which decodes
the JWT and returns a TokenPayload."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.space_node_service.space_service import SpaceService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import get_current_user
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.space_node_schemas.space_schema import (
    PageParams,
    SpaceAddTraineesRequest,
    SpaceCreateRequest,
    SpaceJoinRequest,
    SpaceJoinResponse,
    SpaceListResponse,
    SpaceMemberSummary,
    SpacePublishRequest,
    SpaceRemoveTraineeRequest,
    SpaceResponse,
    SpaceTransferOwnershipRequest,
    SpaceUpdateRequest,
)

router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.post("", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_space(
    payload: SpaceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceResponse:
    """Mentor creates a new e-learning space under a department.
    Auto-generates a unique invite code. Space is unpublished by default."""
    service = SpaceService(db)
    return await service.create_space(payload, current_user.sub, current_user.role)


@router.get("", response_model=SpaceListResponse)
async def list_spaces(
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceListResponse:
    """Return all active spaces where the caller is the effective owner (mentor)
    or is an enrolled member (trainee)."""
    service = SpaceService(db)
    return await service.list_spaces(current_user.sub, current_user.role, params)


@router.get("/{space_id}", response_model=SpaceResponse)
async def get_space(
    space_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceResponse:
    """Fetch a single space by ID. Mentor must be effective owner.
    Trainee must be an active member of the space."""
    service = SpaceService(db)
    return await service.get_space(space_id, current_user.sub, current_user.role)


@router.patch("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: UUID,
    payload: SpaceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceResponse:
    """Mentor partially updates space metadata (name, description). Only provided fields are applied."""
    service = SpaceService(db)
    return await service.update_space(
        space_id, payload, current_user.sub, current_user.role
    )


@router.patch("/{space_id}/publish", response_model=SpaceResponse)
async def publish_space(
    space_id: UUID,
    payload: SpacePublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceResponse:
    """Mentor publishes or unpublishes a space. Published spaces are
    visible and joinable by trainees. Unpublishing does not remove members."""
    service = SpaceService(db)
    return await service.publish_space(
        space_id, payload, current_user.sub, current_user.role
    )


@router.patch("/{space_id}/transfer-ownership", response_model=SpaceResponse)
async def transfer_ownership(
    space_id: UUID,
    payload: SpaceTransferOwnershipRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceResponse:
    """ITAdmin transfers a space's effective ownership to another active mentor.
    Called during mentor deactivation flow (EC-27). Original mentor_id is
    preserved as the audit owner; transferred_to_mentor_id is the new UI owner."""
    service = SpaceService(db)
    return await service.transfer_ownership(space_id, payload, current_user.role)


@router.get("/{space_id}/trainees", response_model=list[SpaceMemberSummary])
async def list_space_trainees(
    space_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> list[SpaceMemberSummary]:
    """Mentor lists all active trainees enrolled in a space."""
    service = SpaceService(db)
    return await service.list_space_trainees(
        space_id, current_user.sub, current_user.role
    )


@router.post("/{space_id}/trainees", status_code=status.HTTP_200_OK)
async def add_trainees(
    space_id: UUID,
    payload: SpaceAddTraineesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, object]:
    """Mentor manually adds one or more trainees to the space.
    Already-active members in the batch are silently skipped."""
    service = SpaceService(db)
    return await service.add_trainees(
        space_id, payload, current_user.sub, current_user.role
    )


@router.delete("/{space_id}/trainees", status_code=status.HTTP_200_OK)
async def remove_trainee(
    space_id: UUID,
    payload: SpaceRemoveTraineeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, str]:
    """Mentor soft-removes a trainee from a space (space_trainees.is_active = false).
    Historical progress and attempt data are fully preserved (EC-13, EC-15)."""
    service = SpaceService(db)
    return await service.remove_trainee(
        space_id, payload, current_user.sub, current_user.role
    )


@router.post("/join", response_model=SpaceJoinResponse, status_code=status.HTTP_200_OK)
async def join_space(
    payload: SpaceJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> SpaceJoinResponse:
    """Trainee joins a published space using a valid invite code.
    Already-active members receive a 409. Previously removed trainees
    cannot rejoin by invite code; only mentor manual add can reactivate them."""
    service = SpaceService(db)
    return await service.join_space(payload, current_user.sub, current_user.role)
