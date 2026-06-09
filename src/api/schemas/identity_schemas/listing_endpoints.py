from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

from src.api.schemas.identity_schemas.departments_schema import DepartmentOut
from src.api.schemas.identity_schemas.mentors_schema import MentorOut
from src.api.schemas.identity_schemas.trainees_schema import TraineeOut

# Generic type variable for the paginated item type
T = TypeVar("T")


class PageParams(BaseModel):
    """
    Reusable query-parameter schema for paginated list endpoints.
    Use as: params: PageParams = Depends() in your router functions.

    Example request: GET /admin/mentors?page=2&limit=20
    """
    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page, max 100")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated wrapper. Wrap any Out schema:
        PaginatedResponse[MentorOut]
        PaginatedResponse[TraineeOut]

    Fields:
        items  — The current page of results.
        total  — Total number of records matching the query (for frontend pagination UI).
        page   — Current page number.
        limit  — Page size used for this response.
        pages  — Total number of pages (ceil(total / limit)).
    """
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int


# ---------- Typed list responses for each domain entity ----------

class DepartmentListResponse(PaginatedResponse[DepartmentOut]):
    """Paginated list of departments. Used by GET /admin/departments."""
    pass


class MentorListResponse(PaginatedResponse[MentorOut]):
    """Paginated list of mentors. Used by GET /admin/mentors."""
    pass


class TraineeListResponse(PaginatedResponse[TraineeOut]):
    """Paginated list of trainees. Used by GET /admin/trainees."""
    pass
