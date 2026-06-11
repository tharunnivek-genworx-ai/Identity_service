from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.exceptions.space_node_exceptions.node_exceptions import (
    NodeForbiddenException,
)
from src.api.core.exceptions.space_node_exceptions.space_exceptions import (
    SpaceNotFoundException,
)
from src.api.data.models.postgres.e_spaces_trees.espaces import ESpace
from src.api.data.repositories.space_node_repository.node_repository import (
    NodeRepository,
)
from src.api.data.repositories.space_node_repository.space_repository import (
    SpaceRepository,
)
from src.api.utils.space_node_utils.space_role_assert import (
    _resolve_effective_mentor,
)


def _assert_mentor(role: str) -> None:
    """Raise NodeForbiddenException if the caller is not a mentor."""
    if role != "mentor":
        raise NodeForbiddenException()


async def _get_space_and_assert_owner(
    session: AsyncSession, space_id: UUID, mentor_id: UUID
) -> ESpace:
    """Fetch space, assert it exists and caller is effective owner."""
    space_repo = SpaceRepository(session)
    space = await space_repo.get_space_by_id(space_id)
    if space is None or not space.is_active:
        raise SpaceNotFoundException()
    if _resolve_effective_mentor(space) != mentor_id:
        raise NodeForbiddenException()
    return space


async def _assert_space_access(
    session: AsyncSession, space_id: UUID, user_id: UUID, role: str
) -> None:
    """Used for read operations — mentors (owner) and trainees (member) allowed."""
    space_repo = SpaceRepository(session)
    space = await space_repo.get_space_by_id(space_id)
    if space is None or not space.is_active:
        raise SpaceNotFoundException()

    if role == "mentor":
        if _resolve_effective_mentor(space) != user_id:
            raise NodeForbiddenException()
    elif role == "trainee":
        is_member = await space_repo.is_active_member(space_id, user_id)
        if not is_member:
            raise NodeForbiddenException()
    else:
        raise NodeForbiddenException()


async def _get_ancestor_ids(node_id: UUID, repo: NodeRepository) -> set[UUID]:
    """Walk up the tree collecting all ancestor node_ids."""
    ancestors: set[UUID] = set()
    current_id = node_id
    while current_id is not None:
        node = await repo.get_node_by_id(current_id)
        if node is None:
            break
        ancestors.add(node.node_id)
        current_id = node.parent_id
    return ancestors


async def _get_descendant_ids(node_id: UUID, repo: NodeRepository) -> list[UUID]:
    """Collect node_id of all descendants recursively."""
    result: list[UUID] = []
    queue: list[UUID] = [node_id]
    while queue:
        current_id = queue.pop()
        children = await repo.get_children(current_id)
        for child in children:
            result.append(child.node_id)
            queue.append(child.node_id)
    return result
