# src/api/rest/routes/admin_route.py
"""Combined IT Admin router.

Admin routes are split by resource in:
- admin_department_route.py
- admin_mentor_route.py
- admin_trainee_route.py
"""

from fastapi import APIRouter

from src.api.rest.routes.identity_routes.admin_CRUD_routes import (
    admin_department_route,
    admin_mentor_route,
    admin_trainee_route,
)

router = APIRouter()
router.include_router(admin_department_route.router)
router.include_router(admin_mentor_route.router)
router.include_router(admin_trainee_route.router)
