# C:\CapStone\Identity_service\src\api\core\services\space_node_service\space_service.py
"""Space service: all business logic for e-learning space lifecycle.

Flow per TDD §3.5.1 and §3.3.1:
  CREATE  → validate dept → generate unique invite code → insert → return
  LIST    → filter by effective ownership (mentor) or membership (trainee)
  GET     → ownership/membership guard → return
  UPDATE  → ownership guard → partial apply → return
  PUBLISH → ownership guard → toggle is_published → return
  TRANSFER→ itadmin only → validate target mentor active → set transferred_to
  ADD     → ownership guard → reject active members (409) → bulk insert/reactivate
  REMOVE  → ownership guard → set is_active = false on membership row
  JOIN    → trainee only → validate invite code → insert membership row

Effective mentor resolution (EC-27):
  COALESCE(transferred_to_mentor_id, mentor_id) is computed at this layer
  and exposed as effective_mentor_id on SpaceResponse.
"""

import math
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.exceptions.identity_exceptions.mentor_exceptions import (
    MentorNotFoundException,
)
from src.api.core.exceptions.space_node_exceptions.space_exceptions import (
    CannotTransferToSameMentorException,
    DepartmentNotFoundException,
    InvalidInviteCodeException,
    InviteCodeGenerationFailedException,
    SpaceAlreadyPublishedException,
    SpaceForbiddenException,
    SpaceNotFoundException,
    SpaceNotPublishedException,
    TraineeAlreadyJoinedViaInviteException,
    TraineeAlreadyMemberException,
    TraineeNotMemberException,
    TraineeRemovedFromSpaceException,
    TransferTargetNotFoundException,
)
from src.api.data.repositories.space_node_repository.space_repository import (
    SpaceRepository,
)
from src.api.schemas.identity_schemas.listing_endpoints import (
    PageParams,
)
from src.api.schemas.space_node_schemas.space_schema import (
    AdminMentorSpaceOut,
    AdminMentorSpaceOverviewResponse,
    AdminMentorTransferredSpaceIn,
    SpaceAddTraineesRequest,
    SpaceCreateRequest,
    SpaceJoinRequest,
    SpaceJoinResponse,
    SpaceListResponse,
    SpaceMemberSummary,
    SpacePublishRequest,
    SpaceRemoveTraineeRequest,
    SpaceResponse,
    SpaceTransferOwnershipRequest,
    SpaceUnpublishPreviewOut,
    SpaceUpdateRequest,
)
from src.api.utils.invite_code import _INVITE_CODE_MAX_ATTEMPTS, _generate_invite_code
from src.api.utils.space_node_utils.build_space_response import _build_space_response
from src.api.utils.space_node_utils.space_role_assert import (
    _assert_effective_owner,
    _assert_itadmin,
    _assert_mentor,
    _assert_not_archived,
    _assert_trainee,
    _resolve_effective_mentor,
)


class SpaceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── create ─────────────────────────────────────────────────────────

    async def create_space(
        self, request: SpaceCreateRequest, user_id: UUID, role: str
    ) -> SpaceResponse:
        """Validate department, generate invite code, insert space row."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)

        # Validate department exists and is active
        dept = await repo.get_department_by_id(request.department_id)
        if dept is None or not dept.is_active:
            raise DepartmentNotFoundException()

        # Generate a unique invite code with collision guard
        invite_code = None
        for _ in range(_INVITE_CODE_MAX_ATTEMPTS):
            candidate = _generate_invite_code()
            existing = await repo.get_space_by_invite_code(candidate)
            if existing is None:
                invite_code = candidate
                break

        if invite_code is None:
            raise InviteCodeGenerationFailedException()

        space = await repo.create_space(request, user_id, invite_code)
        return _build_space_response(space)

    # ── list ───────────────────────────────────────────────────────────

    async def list_spaces(
        self, user_id: UUID, role: str, params: PageParams
    ) -> SpaceListResponse:
        """Mentor sees spaces they own. Trainee sees spaces they are enrolled in."""
        repo = SpaceRepository(self.session)
        skip = (params.page - 1) * params.limit

        if role == "mentor":
            spaces, total = await repo.list_spaces_by_mentor(
                user_id,
                skip=skip,
                limit=params.limit,
            )
        elif role == "trainee":
            spaces, total = await repo.list_spaces_by_trainee(
                user_id,
                skip=skip,
                limit=params.limit,
            )
        else:
            raise SpaceForbiddenException()

        pages = math.ceil(total / params.limit) if total > 0 else 1

        return SpaceListResponse(
            items=[_build_space_response(s) for s in spaces],
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )

    # ── get ────────────────────────────────────────────────────────────

    async def get_space(
        self, space_id: UUID, user_id: UUID, role: str
    ) -> SpaceResponse:
        """Fetch single space with ownership / membership guard."""
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        if role == "mentor":
            _assert_effective_owner(space, user_id)
        elif role == "trainee":
            is_member = await repo.is_active_member(space_id, user_id)
            if not is_member:
                raise SpaceForbiddenException()
        else:
            raise SpaceForbiddenException()

        return _build_space_response(space)

    # ── update ─────────────────────────────────────────────────────────

    async def update_space(
        self, space_id: UUID, request: SpaceUpdateRequest, user_id: UUID, role: str
    ) -> SpaceResponse:
        """Partial update — only fields present in the request are applied."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        _assert_effective_owner(space, user_id)
        _assert_not_archived(space)

        space = await repo.update_space(space, request)
        return _build_space_response(space)

    # ── publish ────────────────────────────────────────────────────────

    async def publish_space(
        self, space_id: UUID, request: SpacePublishRequest, user_id: UUID, role: str
    ) -> SpaceResponse:
        """Toggle is_published. Guard against publishing an already-published space."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        _assert_effective_owner(space, user_id)
        _assert_not_archived(space)

        # Guard: raise if no state change on publish
        if request.is_published and space.is_published:
            raise SpaceAlreadyPublishedException()

        space = await repo.set_published(space, request.is_published)
        return _build_space_response(space)

    async def preview_unpublish_space(
        self, space_id: UUID, user_id: UUID, role: str
    ) -> SpaceUnpublishPreviewOut:
        """Return published content counts before espace unpublish."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)
        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()
        _assert_effective_owner(space, user_id)
        _assert_not_archived(space)

        material_count = await repo.count_published_materials_in_space(space_id)
        quiz_count = await repo.count_published_quizzes_in_space(space_id)
        return SpaceUnpublishPreviewOut(
            published_material_count=material_count,
            published_quiz_count=quiz_count,
        )

    # ── transfer ownership ─────────────────────────────────────────────

    async def transfer_ownership(
        self,
        space_id: UUID,
        request: SpaceTransferOwnershipRequest,
        role: str,
    ) -> SpaceResponse:
        """ITAdmin sets transferred_to_mentor_id on a space (EC-27).
        Target mentor must exist and be active."""
        _assert_itadmin(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        # Cannot transfer to the already-effective owner
        if _resolve_effective_mentor(space) == request.transferred_to_mentor_id:
            raise CannotTransferToSameMentorException()

        # Target mentor must exist and be active
        target = await repo.get_mentor_by_id(request.transferred_to_mentor_id)
        if target is None or not target.is_active:
            raise TransferTargetNotFoundException()

        space = await repo.set_transferred_mentor(
            space, request.transferred_to_mentor_id
        )
        return _build_space_response(space)

    async def admin_list_spaces_for_mentor(
        self,
        mentor_id: UUID,
        role: str,
        params: PageParams,
    ) -> AdminMentorSpaceOverviewResponse:
        """IT Admin space transfer dashboard for a mentor (EC-27)."""
        _assert_itadmin(role)
        repo = SpaceRepository(self.session)

        mentor = await repo.get_mentor_by_id(mentor_id)
        if mentor is None:
            raise MentorNotFoundException(str(mentor_id))

        skip = (params.page - 1) * params.limit
        owned, _total = await repo.list_spaces_by_original_owner(
            mentor_id, skip=skip, limit=params.limit
        )
        owned_items = [
            AdminMentorSpaceOut(
                **_build_space_response(space).model_dump(),
                needs_ownership_transfer=_resolve_effective_mentor(space) == mentor_id,
            )
            for space in owned
        ]

        transferred_in = await repo.list_spaces_transferred_to_mentor(mentor_id)
        original_mentor_cache: dict[UUID, str] = {}
        transferred_items: list[AdminMentorTransferredSpaceIn] = []
        for space in transferred_in:
            original_id = space.mentor_id
            if original_id not in original_mentor_cache:
                original = await repo.get_mentor_by_id(original_id)
                original_mentor_cache[original_id] = (
                    original.full_name if original is not None else "Unknown mentor"
                )
            transferred_items.append(
                AdminMentorTransferredSpaceIn(
                    **_build_space_response(space).model_dump(),
                    needs_ownership_transfer=False,
                    original_mentor_id=original_id,
                    original_mentor_name=original_mentor_cache[original_id],
                )
            )

        return AdminMentorSpaceOverviewResponse(
            owned_spaces=owned_items,
            transferred_in_spaces=transferred_items,
        )

    # ── add trainees ───────────────────────────────────────────────────

    async def add_trainees(
        self, space_id: UUID, request: SpaceAddTraineesRequest, user_id: UUID, role: str
    ) -> dict:
        """Mentor manually adds trainees. Active members raise 409.
        Previously removed members (is_active = false) are reactivated."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        _assert_effective_owner(space, user_id)
        _assert_not_archived(space)

        for trainee_id in request.trainee_ids:
            existing = await repo.get_membership(space_id, trainee_id)
            if existing is not None and existing.is_active:
                raise TraineeAlreadyMemberException()

        added, _skipped = await repo.add_trainees_to_space(
            space_id, request.trainee_ids, joined_via="manual_add"
        )

        return {
            "detail": "Trainees processed.",
            "added": added,
        }

    # ── list trainees ──────────────────────────────────────────────────

    async def list_space_trainees(
        self, space_id: UUID, user_id: UUID, role: str
    ) -> list[SpaceMemberSummary]:
        """Mentor lists all active trainees enrolled in a space."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        _assert_effective_owner(space, user_id)

        rows = await repo.list_active_members(space_id)
        return [
            SpaceMemberSummary(
                trainee_id=trainee.trainee_id,
                full_name=trainee.full_name,
                email=trainee.email,
                joined_via=membership.joined_via,
                joined_at=membership.joined_at,
                is_active=membership.is_active,
            )
            for membership, trainee in rows
        ]

    # ── remove trainee ─────────────────────────────────────────────────

    async def remove_trainee(
        self,
        space_id: UUID,
        request: SpaceRemoveTraineeRequest,
        user_id: UUID,
        role: str,
    ) -> dict:
        """Mentor soft-removes one trainee. Historical data is preserved."""
        _assert_mentor(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_id(space_id)
        if space is None or not space.is_active:
            raise SpaceNotFoundException()

        _assert_effective_owner(space, user_id)

        membership = await repo.get_active_membership(space_id, request.trainee_id)
        if membership is None:
            raise TraineeNotMemberException()

        await repo.deactivate_membership(membership)
        return {"detail": "Trainee removed from space."}

    # ── join via invite code ───────────────────────────────────────────

    async def join_space(
        self, request: SpaceJoinRequest, user_id: UUID, role: str
    ) -> SpaceJoinResponse:
        """Trainee joins via invite code. Space must be published and active.
        Previously removed trainees cannot rejoin by invite; only mentor manual
        add can reactivate them."""
        _assert_trainee(role)
        repo = SpaceRepository(self.session)

        space = await repo.get_space_by_invite_code(request.invite_code)
        if space is None or not space.is_active:
            raise InvalidInviteCodeException()

        if not space.is_published:
            raise SpaceNotPublishedException()

        existing_membership = await repo.get_membership(space.space_id, user_id)
        if existing_membership and existing_membership.is_active:
            raise TraineeAlreadyJoinedViaInviteException()
        if existing_membership:
            raise TraineeRemovedFromSpaceException()

        membership = await repo.create_trainee_membership(
            space.space_id, user_id, joined_via="invite_code"
        )

        return SpaceJoinResponse(
            space_id=space.space_id,
            space_name=space.space_name,
            joined_via=membership.joined_via,
            joined_at=membership.joined_at,
        )
