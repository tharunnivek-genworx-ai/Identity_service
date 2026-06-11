# src/api/rest/routes/admin_trainee_route.py
"""IT Admin trainee routes.

Every route here requires role='itadmin' enforced by require_role().
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.identity_service.trainee_service import TraineeService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
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

router = APIRouter(prefix="/admin/trainees", tags=["IT Admin"])

ITAdminUser = Annotated[TokenPayload, Depends(require_role("itadmin"))]


@router.post("", response_model=TraineeOut, status_code=201)
async def create_trainee(
    payload: TraineeCreate,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> TraineeOut:
    """Create a new trainee account. Password is hashed in the service layer.
    The trainee's home department must already exist."""
    service = TraineeService(db)
    return await service.create_trainee(payload, created_by=UUID(str(current_user.sub)))


@router.get("", response_model=TraineeListResponse)
async def list_trainees(
    current_user: ITAdminUser,
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TraineeListResponse:
    """List all trainee accounts with pagination."""
    service = TraineeService(db)
    return await service.list_trainees(params)


@router.get("/{trainee_id}", response_model=TraineeOut)
async def get_trainee(
    trainee_id: UUID,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> TraineeOut:
    """Fetch a single trainee by ID."""
    service = TraineeService(db)
    return await service.get_trainee(trainee_id)


@router.patch("/{trainee_id}/deactivate", response_model=TraineeOut)
async def deactivate_trainee(
    trainee_id: UUID,
    payload: TraineeDeactivateRequest,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> TraineeOut:
    """Soft-delete a trainee account. All progress and quiz history is retained (EC-28).
    The trainee cannot log in after deactivation."""
    service = TraineeService(db)
    return await service.deactivate_trainee(trainee_id, payload)


@router.patch("/{trainee_id}/reactivate", response_model=TraineeOut)
async def reactivate_trainee(
    trainee_id: UUID,
    payload: TraineeReactivateRequest,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> TraineeOut:
    """Re-enable a soft-deleted trainee. Restores login access and all historical data (EC-29)."""
    service = TraineeService(db)
    return await service.reactivate_trainee(trainee_id, payload)
