# src/api/rest/routes/admin_department_route.py
"""IT Admin department routes.

Every route here requires role='itadmin' enforced by require_role().
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.department_service import DepartmentService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.auth_schema import TokenPayload
from src.api.schemas.departments_schema import DepartmentCreate, DepartmentOut, DepartmentUpdate
from src.api.schemas.listing_endpoints import DepartmentListResponse, PageParams

router = APIRouter(prefix="/admin/departments", tags=["IT Admin"])

ITAdminUser = Annotated[TokenPayload, Depends(require_role("itadmin"))]


@router.post("", response_model=DepartmentOut, status_code=201)
async def create_department(
    payload: DepartmentCreate,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a new department. departmentcode must be unique (e.g. 'FE', 'DEVOPS').
    createdby is taken from the JWT - never from the request body."""
    service = DepartmentService(db)
    return await service.create_department(payload, created_by=UUID(str(current_user.sub)))


@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    current_user: ITAdminUser,
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List all departments with pagination. Default: page=1, limit=20."""
    service = DepartmentService(db)
    return await service.list_departments(params)


@router.get("/{department_id}", response_model=DepartmentOut)
async def get_department(
    department_id: UUID,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single department by ID."""
    service = DepartmentService(db)
    return await service.get_department(department_id)


@router.patch("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Partially update a department. Only provided fields are changed.
    departmentcode is intentionally not updatable (it is a business key)."""
    service = DepartmentService(db)
    return await service.update_department(department_id, payload)
