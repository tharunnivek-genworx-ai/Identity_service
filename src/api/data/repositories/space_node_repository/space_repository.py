# src/api/data/repositories/space_node_repository/space_repository.py
"""Repository for all e-learning space DB operations.

Handles:
  - Space CRUD (insert, update, publish, transfer, archive)
  - Department and mentor lookups needed by the service layer
  - Space membership (space_trainees): add, remove, upsert, check
  - Invite code lookup
"""

from uuid import UUID, uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.models.postgres.e_spaces_trees.espaces import ESpace
from src.api.data.models.postgres.e_spaces_trees.space_trainees import SpaceTrainee
from src.api.data.models.postgres.Identity_models.departments import Department
from src.api.data.models.postgres.Identity_models.mentors import Mentor
from src.api.data.models.postgres.Identity_models.trainees import Trainee
from src.api.schemas.space_node_schemas.space_schema import SpaceCreateRequest, SpaceUpdateRequest
from src.api.utils.time import utc_now as get_current_utc_time

class SpaceRepository:

    def __init__(self, session: AsyncSession):
        self.db = session

    # ── Department lookup ───────────────────────────────────────────────

    async def get_department_by_id(self, department_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.department_id == department_id)
        )
        return result.scalars().first()

    # ── Mentor lookup (for ownership transfer) ──────────────────────────

    async def get_mentor_by_id(self, mentor_id: UUID) -> Mentor | None:
        result = await self.db.execute(
            select(Mentor).where(Mentor.mentor_id == mentor_id)
        )
        return result.scalars().first()

    # ── Space lookups ───────────────────────────────────────────────────

    async def get_space_by_id(self, space_id: UUID) -> ESpace | None:
        result = await self.db.execute(
            select(ESpace).where(ESpace.space_id == space_id)
        )
        return result.scalars().first()

    async def get_space_by_invite_code(self, invite_code: str) -> ESpace | None:
        result = await self.db.execute(
            select(ESpace).where(ESpace.invite_code == invite_code)
        )
        return result.scalars().first()

    async def list_spaces_by_mentor(
        self, mentor_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ESpace], int]:
        """Return paginated active spaces where mentor is original owner or transfer target."""
        filters = and_(
            ESpace.is_active == True,
            # Effective owner: either original or transferred
            (ESpace.mentor_id == mentor_id) |
            (ESpace.transferred_to_mentor_id == mentor_id),
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

    async def list_spaces_by_trainee(
        self, trainee_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ESpace], int]:
        """Return paginated active published spaces the trainee is an active member of."""
        join_filters = and_(
            SpaceTrainee.space_id == ESpace.space_id,
            SpaceTrainee.trainee_id == trainee_id,
            SpaceTrainee.is_active == True,
        )
        filters = and_(
            ESpace.is_active == True,
            ESpace.is_published == True,
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
        await self.db.commit()
        await self.db.refresh(space)
        return space

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
                    SpaceTrainee.is_active == True,
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
                    SpaceTrainee.is_active == True,
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
                    SpaceTrainee.is_active == True,
                )
            )
        )
        return result.scalars().first()

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
        return result.scalars().first()

    async def add_trainees_to_space(
        self,
        space_id: UUID,
        trainee_ids: list[UUID],
        joined_via: str,
    ) -> tuple[int, int]:
        """Insert or reactivate membership rows. Returns (added_count, skipped_count)."""
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
