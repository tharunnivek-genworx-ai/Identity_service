from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.identity_service.trainee_service import TraineeService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.identity_schemas.trainees_schema import TraineeOut

router = APIRouter(prefix="/mentor/trainees", tags=["Mentor Identity"])

MentorUser = Annotated[TokenPayload, Depends(require_role("mentor"))]


@router.get("/search", response_model=list[TraineeOut])
async def search_trainees(
    current_user: MentorUser,
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[TraineeOut]:
    """Search trainees by name, email, or employee ID."""
    service = TraineeService(db)
    return await service.search_trainees(query=q, limit=limit)
