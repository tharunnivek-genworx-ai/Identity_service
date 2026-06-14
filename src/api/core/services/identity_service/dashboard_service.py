"""IT Admin dashboard aggregate stats."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.repositories.identity_repository.department_repository import (
    DepartmentRepository,
)
from src.api.data.repositories.identity_repository.mentor_repository import (
    MentorRepository,
)
from src.api.data.repositories.identity_repository.trainee_repository import (
    TraineeRepository,
)
from src.api.schemas.identity_schemas.dashboard_schema import AdminDashboardStatsOut


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_stats(self) -> AdminDashboardStatsOut:
        mentor_repo = MentorRepository(self.session)
        trainee_repo = TraineeRepository(self.session)
        dept_repo = DepartmentRepository(self.session)

        total_mentors, active_mentors = await mentor_repo.count_all_and_active()
        total_trainees, active_trainees = await trainee_repo.count_all_and_active()
        total_departments = await dept_repo.count_all()

        return AdminDashboardStatsOut(
            total_mentors=total_mentors,
            total_trainees=total_trainees,
            total_departments=total_departments,
            active_mentors=active_mentors,
            active_trainees=active_trainees,
        )
