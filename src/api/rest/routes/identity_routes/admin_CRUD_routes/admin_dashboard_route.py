"""IT Admin dashboard routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.identity_service.dashboard_service import DashboardService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.identity_schemas.dashboard_schema import AdminDashboardStatsOut

router = APIRouter(prefix="/admin/dashboard", tags=["IT Admin"])

ITAdminUser = Annotated[TokenPayload, Depends(require_role("itadmin"))]


@router.get("/stats", response_model=AdminDashboardStatsOut)
async def get_dashboard_stats(
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> AdminDashboardStatsOut:
    """Organisation-wide account and department counts for the admin dashboard."""
    service = DashboardService(db)
    return await service.get_dashboard_stats()
