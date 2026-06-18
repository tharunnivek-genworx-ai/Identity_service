# C:\CapStone\Identity_service\src\api\utils\space_node_utils\build_space_response.py
from src.api.data.models.postgres.e_spaces_trees.espaces import ESpace
from src.api.schemas.space_node_schemas.space_schema import SpaceResponse
from src.api.utils.space_node_utils.space_role_assert import _resolve_effective_mentor


def _build_space_response(space: ESpace) -> SpaceResponse:
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
    )
