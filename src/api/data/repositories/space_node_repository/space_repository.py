"""Repository for all e-learning space DB operations.

Handles:
  - Space CRUD (insert, update, publish, transfer, archive)
  - Department and mentor lookups needed by the service layer
  - Space membership (space_trainees): add, remove, upsert, check
  - Invite code lookup
"""

from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.models.postgres.e_spaces_trees.espaces import ESpace
from src.api.data.models.postgres.e_spaces_trees.space_trainees import SpaceTrainee
from src.api.data.models.postgres.Identity_models.departments import Department
from src.api.data.models.postgres.Identity_models.mentors import Mentor
from src.api.data.models.postgres.Identity_models.trainees import Trainee
from src.api.schemas.space_node_schemas.space_schema import (
    SpaceCreateRequest,
    SpaceUpdateRequest,
)
from src.api.utils.time import utc_now as get_current_utc_time


class SpaceRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    # ── Department lookup ───────────────────────────────────────────────

    async def get_department_by_id(self, department_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.department_id == department_id)
        )
        return cast(Department | None, result.scalars().first())

    # ── Mentor lookup (for ownership transfer) ──────────────────────────

    async def get_mentor_by_id(self, mentor_id: UUID) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.mentor_id == mentor_id)
        )
        return cast(Mentor | None, result.scalars().first())

    # ── Space lookups ───────────────────────────────────────────────────

    async def get_space_by_id(self, space_id: UUID) -> ESpace | None:
        result = await self.db.execute(
            select(ESpace).where(ESpace.space_id == space_id)
        )
        return cast(ESpace | None, result.scalars().first())

    async def get_space_by_invite_code(self, invite_code: str) -> ESpace | None:
        result = await self.db.execute(
            select(ESpace).where(ESpace.invite_code == invite_code)
        )
        return cast(ESpace | None, result.scalars().first())

    async def list_spaces_by_mentor(
        self, mentor_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ESpace], int]:
        """Paginated active spaces where mentor is owner or transfer target."""
        filters = and_(
            ESpace.is_active,
            # Effective owner: either original or transferred
            (ESpace.mentor_id == mentor_id)
            | (ESpace.transferred_to_mentor_id == mentor_id),
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(ESpace).where(filters)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(ESpace)
            .where(filters)
            .order_by(ESpace.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_spaces_by_original_owner(
        self, mentor_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[ESpace], int]:
        """Paginated active spaces where mentor_id is the audit owner."""
        filters = and_(ESpace.is_active, ESpace.mentor_id == mentor_id)

        count_result = await self.db.execute(
            select(func.count()).select_from(ESpace).where(filters)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(ESpace)
            .where(filters)
            .order_by(ESpace.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_spaces_transferred_to_mentor(self, mentor_id: UUID) -> list[ESpace]:
        """Active spaces where this mentor is the effective owner via transfer."""
        result = await self.db.execute(
            select(ESpace)
            .where(
                and_(
                    ESpace.is_active,
                    ESpace.transferred_to_mentor_id == mentor_id,
                )
            )
            .order_by(ESpace.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_spaces_by_trainee(
        self, trainee_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ESpace], int]:
        """Paginated published spaces the trainee is an active member of."""
        join_filters = and_(
            SpaceTrainee.space_id == ESpace.space_id,
            SpaceTrainee.trainee_id == trainee_id,
            SpaceTrainee.is_active,
        )
        filters = and_(
            ESpace.is_active,
            ESpace.is_published,
        )

        count_result = await self.db.execute(
            select(func.count())
            .select_from(ESpace)
            .join(SpaceTrainee, join_filters)
            .where(filters)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(ESpace)
            .join(SpaceTrainee, join_filters)
            .where(filters)
            .order_by(ESpace.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    # ── Space writes ────────────────────────────────────────────────────

    async def create_space(
        self,
        request: SpaceCreateRequest,
        mentor_id: UUID,
        invite_code: str,
    ) -> ESpace:
        space = ESpace(
            space_id=uuid4(),
            space_name=request.space_name,
            description=request.description,
            department_id=request.department_id,
            mentor_id=mentor_id,
            transferred_to_mentor_id=None,
            invite_code=invite_code,
            is_published=False,
            is_active=True,
            created_at=get_current_utc_time(),
            updated_at=get_current_utc_time(),
            archived_at=None,
        )
        self.db.add(space)
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def update_space(self, space: ESpace, request: SpaceUpdateRequest) -> ESpace:
        """Partial update — only non-None fields from request are applied."""
        if request.space_name is not None:
            space.space_name = request.space_name
        if request.description is not None:
            space.description = request.description
        space.updated_at = get_current_utc_time()
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def set_published(self, space: ESpace, is_published: bool) -> ESpace:
        space.is_published = is_published
        space.updated_at = get_current_utc_time()

        if not is_published:
            from sqlalchemy import update

            from src.api.data.models.postgres.quiz_models.quizzes import Quiz
            from src.api.data.models.postgres.study_material_models.study_material_versions import (  # noqa: E501
                StudyMaterialVersion,
            )

            # Unpublish all study material versions in this space
            await self.db.execute(
                update(StudyMaterialVersion)
                .where(
                    StudyMaterialVersion.spaceid == space.space_id,
                    StudyMaterialVersion.ispublished.is_(True),
                )
                .values(
                    ispublished=False,
                    publishedat=None,
                    publishedby=None,
                )
            )
            # Unpublish all quizzes in this space
            await self.db.execute(
                update(Quiz)
                .where(
                    Quiz.space_id == space.space_id,
                    Quiz.is_published.is_(True),
                )
                .values(
                    is_published=False,
                    published_at=None,
                )
            )

        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def count_published_materials_in_space(self, space_id: UUID) -> int:
        from src.api.data.models.postgres.study_material_models.study_material_versions import (  # noqa: E501
            StudyMaterialVersion,
        )

        result = await self.db.execute(
            select(func.count())
            .select_from(StudyMaterialVersion)
            .where(
                StudyMaterialVersion.spaceid == space_id,
                StudyMaterialVersion.ispublished.is_(True),
            )
        )
        return int(result.scalar() or 0)

    async def count_published_quizzes_in_space(self, space_id: UUID) -> int:
        from src.api.data.models.postgres.quiz_models.quizzes import Quiz

        result = await self.db.execute(
            select(func.count())
            .select_from(Quiz)
            .where(
                Quiz.space_id == space_id,
                Quiz.is_published.is_(True),
            )
        )
        return int(result.scalar() or 0)

    async def set_transferred_mentor(
        self, space: ESpace, transferred_to_mentor_id: UUID
    ) -> ESpace:
        space.transferred_to_mentor_id = transferred_to_mentor_id
        space.updated_at = get_current_utc_time()
        await self.db.commit()
        await self.db.refresh(space)
        return space

    # ── Membership ──────────────────────────────────────────────────────

    async def list_active_members(
        self, space_id: UUID
    ) -> list[tuple[SpaceTrainee, Trainee]]:
        """Return all active memberships joined with Trainee data for a space."""
        result = await self.db.execute(
            select(SpaceTrainee, Trainee)
            .join(Trainee, SpaceTrainee.trainee_id == Trainee.trainee_id)
            .where(
                and_(
                    SpaceTrainee.space_id == space_id,
                    SpaceTrainee.is_active,
                )
            )
            .order_by(Trainee.full_name)
        )
        return list(result.all())

    async def is_active_member(self, space_id: UUID, trainee_id: UUID) -> bool:
        result = await self.db.execute(
            select(SpaceTrainee).where(
                and_(
                    SpaceTrainee.space_id == space_id,
                    SpaceTrainee.trainee_id == trainee_id,
                    SpaceTrainee.is_active,
                )
            )
        )
        return result.scalars().first() is not None

    async def get_active_membership(
        self, space_id: UUID, trainee_id: UUID
    ) -> SpaceTrainee | None:
        result = await self.db.execute(
            select(SpaceTrainee).where(
                and_(
                    SpaceTrainee.space_id == space_id,
                    SpaceTrainee.trainee_id == trainee_id,
                    SpaceTrainee.is_active,
                )
            )
        )
        return cast(SpaceTrainee | None, result.scalars().first())

    async def get_membership(
        self, space_id: UUID, trainee_id: UUID
    ) -> SpaceTrainee | None:
        """Fetch a membership row regardless of active/inactive state."""
        result = await self.db.execute(
            select(SpaceTrainee).where(
                and_(
                    SpaceTrainee.space_id == space_id,
                    SpaceTrainee.trainee_id == trainee_id,
                )
            )
        )
        return cast(SpaceTrainee | None, result.scalars().first())

    async def add_trainees_to_space(
        self,
        space_id: UUID,
        trainee_ids: list[UUID],
        joined_via: str,
    ) -> tuple[int, int]:
        """Insert or reactivate membership rows. Returns added/skipped counts."""
        added = 0
        skipped = 0
        now = get_current_utc_time()

        for trainee_id in trainee_ids:
            # Check for any existing row (active or inactive)
            result = await self.db.execute(
                select(SpaceTrainee).where(
                    and_(
                        SpaceTrainee.space_id == space_id,
                        SpaceTrainee.trainee_id == trainee_id,
                    )
                )
            )
            existing = result.scalars().first()

            if existing:
                if existing.is_active:
                    skipped += 1
                else:
                    # Reactivate previously removed member
                    existing.is_active = True
                    existing.joined_via = joined_via
                    existing.joined_at = now
                    added += 1
            else:
                membership = SpaceTrainee(
                    space_trainee_id=uuid4(),
                    space_id=space_id,
                    trainee_id=trainee_id,
                    joined_via=joined_via,
                    joined_at=now,
                    is_active=True,
                )
                self.db.add(membership)
                added += 1

        await self.db.commit()
        return added, skipped

    async def deactivate_membership(self, membership: SpaceTrainee) -> None:
        membership.is_active = False
        await self.db.commit()

    async def create_trainee_membership(
        self,
        space_id: UUID,
        trainee_id: UUID,
        joined_via: str,
    ) -> SpaceTrainee:
        """Insert a new membership row for invite-code joins.

        Previously removed trainees must not be reactivated here; mentor manual
        add is the only path that can reactivate an inactive membership.
        """
        now = get_current_utc_time()

        membership = SpaceTrainee(
            space_trainee_id=uuid4(),
            space_id=space_id,
            trainee_id=trainee_id,
            joined_via=joined_via,
            joined_at=now,
            is_active=True,
        )
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return membership
