from pydantic import BaseModel, Field


class AdminDashboardStatsOut(BaseModel):
    """Organisation-wide counts for the IT Admin dashboard."""

    total_mentors: int = Field(..., ge=0)
    total_trainees: int = Field(..., ge=0)
    total_departments: int = Field(..., ge=0)
    active_mentors: int = Field(..., ge=0)
    active_trainees: int = Field(..., ge=0)
