# src/api/rest/routes/node_route.py
"""Node (topic tree) routes: create, rename, update instruction,
reparent, reorder siblings, archive, get tree, get single node.

All node mutations are mentor-only and require the caller to be
the effective owner of the parent space.
Trainees can only read the tree (GET /spaces/{space_id}/tree).

Note: GET /spaces/{space_id}/tree lives here but is nested under
the space path for REST clarity."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.services.space_node_service.node_service import NodeService
from src.api.data.clients.postgres.database import get_db
from src.api.rest.routes.dependencies import get_current_user
from src.api.schemas.identity_schemas.auth_schema import TokenPayload
from src.api.schemas.space_node_schemas.node_schema import (
    NodeArchiveRequest,
    NodeCreateRequest,
    NodeRenameRequest,
    NodeReorderRequest,
    NodeReparentRequest,
    NodeResponse,
    NodeTreeResponse,
    NodeUpdateInstructionRequest,
)

router = APIRouter(tags=["Topic Tree"])


@router.post(
    "/spaces/{space_id}/nodes",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_node(
    space_id: UUID,
    payload: NodeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> NodeResponse:
    """Mentor creates a node in the topic tree of a space.
    parent_id = None creates a root-level topic (level 1).
    level is auto-computed; order_index defaults to appending at end of siblings."""
    service = NodeService(db)
    return await service.create_node(
        space_id, payload, current_user.sub, current_user.role
    )


@router.get("/spaces/{space_id}/tree", response_model=NodeTreeResponse)
async def get_tree(
    space_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> NodeTreeResponse:
    """Return the full recursive topic tree for a space.
    Mentor must be effective owner. Trainee must be an active member.
    Only is_active = True nodes are included."""
    service = NodeService(db)
    return await service.get_tree(space_id, current_user.sub, current_user.role)


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> NodeResponse:
    """Fetch a single node by ID. Caller must have access to the parent space."""
    service = NodeService(db)
    return await service.get_node(node_id, current_user.sub, current_user.role)


@router.patch("/nodes/{node_id}/rename", response_model=NodeResponse)
async def rename_node(
    node_id: UUID,
    payload: NodeRenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> NodeResponse:
    """Mentor renames a node's title. node_id is stable — all downstream
    FKs (attempts, progress, study material) remain valid after rename (EC-1)."""
    service = NodeService(db)
    return await service.rename_node(
        node_id, payload, current_user.sub, current_user.role
    )


@router.patch("/nodes/{node_id}/instruction", response_model=NodeResponse)
async def update_node_instruction(
    node_id: UUID,
    payload: NodeUpdateInstructionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> NodeResponse:
    """Mentor updates any combination of the three node instruction fields.

    Instruction modes:
      node_specific_instruction  — full override for this node only; when set,
                                   inherited tree defaults are ignored for this node
      tree_default_instruction   — default instruction inherited by all descendants
      node_additive_instruction  — additive extra for this node only; appended on top
                                   of inherited defaults; NOT inherited by descendants

    Partial-update semantics (field-level PATCH):
      - Omitting a field from the JSON body → existing DB value is PRESERVED
      - Sending null                         → field is CLEARED
      - Sending a string                     → field is WRITTEN
    """
    service = NodeService(db)
    return await service.update_node_instruction(
        node_id, payload, current_user.sub, current_user.role
    )


@router.patch("/nodes/{node_id}/reparent", response_model=NodeResponse)
async def reparent_node(
    node_id: UUID,
    payload: NodeReparentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> NodeResponse:
    """Mentor moves a node to a new parent (or promotes it to root if
    new_parent_id = None). Service validates against circular references
    and cross-space moves. level is recomputed on commit (EC-2)."""
    service = NodeService(db)
    return await service.reparent_node(
        node_id, payload, current_user.sub, current_user.role
    )


@router.patch("/spaces/{space_id}/nodes/reorder", status_code=status.HTTP_200_OK)
async def reorder_nodes(
    space_id: UUID,
    payload: NodeReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, object]:
    """Bulk-update order_index for a set of sibling nodes under the same parent.
    All nodes in the payload must be siblings. Partial sibling sets are rejected."""
    service = NodeService(db)
    return await service.reorder_nodes(
        space_id, payload, current_user.sub, current_user.role
    )


@router.patch("/nodes/{node_id}/archive", status_code=status.HTTP_200_OK)
async def archive_node(
    node_id: UUID,
    payload: NodeArchiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, object]:
    """Mentor soft-archives a node (is_active = false). If archive_children = True,
    all descendants are archived recursively. Historical attempts remain readable
    and archived nodes no longer count toward space progress (EC-3)."""
    service = NodeService(db)
    return await service.archive_node(
        node_id, payload, current_user.sub, current_user.role
    )
