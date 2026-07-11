# C:\CapStone\Identity_service\src\api\rest\routes\identity_routes\mentor_route.py
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.identity_service.mentor_service import MentorService
from src.api.core.services.identity_service.trainee_service import TraineeService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.identity_schemas.mentors_schema import MentorOut
from src.api.schemas.identity_schemas.trainees_schema import TraineeOut

router = APIRouter(prefix="/mentor/trainees", tags=["Mentor Identity"])
profile_router = APIRouter(prefix="/mentor", tags=["Mentor Identity"])

MentorUser = Annotated[TokenPayload, Depends(require_role("mentor"))]


@profile_router.get("/me", response_model=MentorOut)
async def get_mentor_profile(
    current_user: MentorUser,
    db: AsyncSession = Depends(get_db),
) -> MentorOut:
    """Return the logged-in mentor's profile, including assigned department."""
    service = MentorService(db)
    return await service.get_mentor(current_user.sub)


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
