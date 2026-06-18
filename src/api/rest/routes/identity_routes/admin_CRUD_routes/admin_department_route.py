# C:\CapStone\Identity_service\src\api\rest\routes\identity_routes\admin_CRUD_routes\admin_department_route.py
"""IT Admin department routes.

Every route here requires role='itadmin' enforced by require_role().
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.identity_service.department_service import DepartmentService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import require_role
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.identity_schemas.departments_schema import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
)
from src.api.schemas.identity_schemas.listing_endpoints import (
    DepartmentListParams,
    DepartmentListResponse,
)

router = APIRouter(prefix="/admin/departments", tags=["IT Admin"])

ITAdminUser = Annotated[TokenPayload, Depends(require_role("itadmin"))]
ITAdminOrMentorUser = Annotated[
    TokenPayload, Depends(require_role("itadmin", "mentor"))
]


@router.post("", response_model=DepartmentOut, status_code=201)
async def create_department(
    payload: DepartmentCreate,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> DepartmentOut:
    """Create a new department. departmentcode must be unique (e.g. 'FE', 'DEVOPS').
    createdby is taken from the JWT - never from the request body."""
    service = DepartmentService(db)
    return await service.create_department(
        payload, created_by=UUID(str(current_user.sub))
    )


@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    current_user: ITAdminOrMentorUser,
    params: DepartmentListParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> DepartmentListResponse:
    """List departments with pagination. Optional is_active filter for dropdowns."""
    service = DepartmentService(db)
    return await service.list_departments(params)


@router.get("/{department_id}", response_model=DepartmentOut)
async def get_department(
    department_id: UUID,
    current_user: ITAdminOrMentorUser,
    db: AsyncSession = Depends(get_db),
) -> DepartmentOut:
    """Fetch a single department by ID."""
    service = DepartmentService(db)
    return await service.get_department(department_id)


@router.patch("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    current_user: ITAdminUser,
    db: AsyncSession = Depends(get_db),
) -> DepartmentOut:
    """Partially update a department. Only provided fields are changed.
    departmentcode is intentionally not updatable (it is a business key)."""
    service = DepartmentService(db)
    return await service.update_department(department_id, payload)
