from uuid import UUID

from src.api.data.models.postgres.e_spaces_trees.espaces import ESpace
from src.api.schemas.space_node_schemas.space_schema import SpaceResponse
from src.api.utils.space_node_utils.space_role_assert import _resolve_effective_mentor


def _build_space_response(
    space: ESpace, current_user_id: UUID | None = None
) -> SpaceResponse:
    """Builds a SpaceResponse schema from an ESpace database model.

    If current_user_id is provided, checks whether ownership of the space has
    been transferred away from this mentor to another active mentor.
    """
    is_transferred_away = False
    if current_user_id is not None and space.transferred_to_mentor_id is not None:
        # Ownership has been transferred away if the current user is the original owner
        # (mentor_id) but the effective ownership belongs to someone else.
        is_transferred_away = (
            space.mentor_id == current_user_id
            and space.transferred_to_mentor_id != current_user_id
        )

    return SpaceResponse(
        space_id=space.space_id,
        space_name=space.space_name,
        description=space.description,
        department_id=space.department_id,
        mentor_id=space.mentor_id,
        transferred_to_mentor_id=space.transferred_to_mentor_id,
        effective_mentor_id=_resolve_effective_mentor(space),
        invite_code=space.invite_code,
        is_published=space.is_published,
        is_active=space.is_active,
        created_at=space.created_at,
        updated_at=space.updated_at,
        archived_at=space.archived_at,
        is_transferred_away=is_transferred_away,
    )
