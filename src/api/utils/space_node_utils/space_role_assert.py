from uuid import UUID

from src.api.core.exceptions.space_node_exceptions.space_exceptions import (
    SpaceArchivedConflictException,
    SpaceForbiddenException,
)


def _resolve_effective_mentor(space) -> UUID:
    """COALESCE(transferred_to_mentor_id, mentor_id) — TDD EC-27."""
    return space.transferred_to_mentor_id if space.transferred_to_mentor_id else space.mentor_id


def _assert_mentor(role: str) -> None:
    """Raise SpaceForbiddenException if the caller is not a mentor."""
    if role != "mentor":
        raise SpaceForbiddenException()


def _assert_itadmin(role: str) -> None:
    """Raise SpaceForbiddenException if the caller is not an itadmin."""
    if role != "itadmin":
        raise SpaceForbiddenException()


def _assert_trainee(role: str) -> None:
    """Raise SpaceForbiddenException if the caller is not a trainee."""
    if role != "trainee":
        raise SpaceForbiddenException()


def _assert_effective_owner(space, mentor_id: UUID) -> None:
    """Raises SpaceForbiddenException if mentor is not the effective owner."""
    if _resolve_effective_mentor(space) != mentor_id:
        raise SpaceForbiddenException()


def _assert_not_archived(space) -> None:
    """Raises SpaceArchivedConflictException if space is archived."""
    if space.archived_at is not None:
        raise SpaceArchivedConflictException()
