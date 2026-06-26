# C:\CapStone\Identity_service\src\api\core\services\space_node_service\node_service.py
"""Node service: all business logic for topic tree management.

Flow per TDD §3.3.1 topic_nodes and §3.5.3:
  CREATE    → validate space ownership → validate parent (same space, active)
              → compute level → resolve order_index → insert
  GET TREE  → access guard → fetch all active nodes → build recursive tree
  GET NODE  → access guard → return flat node
  RENAME    → ownership guard → update title only (node_id stable, EC-1)
  INSTRUCTION → ownership guard → partial-update three instruction fields:
                  node_specific_instruction  : full override for this node
                  tree_default_instruction   : inherited default for subtree
                  node_additive_instruction  : additive extra for this node only;
                                               not inherited; uses UNSET sentinel
                                               to distinguish omit vs null
  REPARENT  → ownership guard → validate no cycle → validate same space
              → recompute level → update parent_id (EC-2)
  REORDER   → ownership guard → validate all same parent → bulk update order_index
  ARCHIVE   → ownership guard → set is_active = false → optionally recurse
              to children (EC-3)
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.exceptions.space_node_exceptions.node_exceptions import (
    NodeAlreadyArchivedException,
    NodeArchivedModificationException,
    NodeCircularReferenceException,
    NodeNotFoundException,
    NodeParentArchivedException,
    NodeParentSpaceMismatchException,
)
from src.api.data.models.postgres.e_spaces_trees.topic_nodes import TopicNode
from src.api.data.repositories.space_node_repository.node_repository import (
    UNSET,
    NodeRepository,
)
from src.api.schemas.space_node_schemas.node_schema import (
    NodeArchiveRequest,
    NodeCreateRequest,
    NodeRenameRequest,
    NodeReorderRequest,
    NodeReparentRequest,
    NodeResponse,
    NodeTreeResponse,
    NodeUpdateInstructionRequest,
    TraineeNodeTreeResponse,
)
from src.api.utils.space_node_utils.build_node import (
    _build_node_response,
    _build_tree,
    _build_tree_for_trainee,
)
from src.api.utils.space_node_utils.instruction_mode import (
    resolve_instruction_fields_from_mode,
)
from src.api.utils.space_node_utils.node_role_assert import (
    _assert_mentor,
    _assert_space_access,
    _get_descendant_ids,
    _get_space_and_assert_owner,
)


class NodeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _build_node_response_with_effective_instruction(
        self,
        repo: NodeRepository,
        node: TopicNode,
    ) -> NodeResponse:
        ancestors = await repo.get_ancestors(node)
        return _build_node_response(node, ancestors)

    # ── create ─────────────────────────────────────────────────────────

    async def create_node(
        self, space_id: UUID, request: NodeCreateRequest, user_id: UUID, role: str
    ) -> NodeResponse:
        """Validate parent, compute level, resolve order_index, insert node."""
        _assert_mentor(role)
        await _get_space_and_assert_owner(self.session, space_id, user_id)

        repo = NodeRepository(self.session)
        level = 1
        parent_id = request.parent_id

        if parent_id is not None:
            parent = await repo.get_node_by_id(parent_id)
            if parent is None or parent.space_id != space_id:
                raise NodeParentSpaceMismatchException()
            if not parent.is_active:
                raise NodeParentArchivedException()
            level = parent.level + 1

        # Resolve order_index: if not provided, append after last sibling
        order_index = request.order_index
        if order_index is None:
            order_index = await repo.get_next_order_index(space_id, parent_id)

        node = await repo.create_node(
            space_id=space_id,
            parent_id=parent_id,
            title=request.title,
            level=level,
            order_index=order_index,
            node_specific_instruction=request.node_specific_instruction,
            tree_default_instruction=request.tree_default_instruction,
            node_additive_instruction=request.node_additive_instruction,
            created_by=user_id,
        )
        return await self._build_node_response_with_effective_instruction(repo, node)

    # ── get tree ───────────────────────────────────────────────────────

    async def get_tree(
        self, space_id: UUID, user_id: UUID, role: str
    ) -> NodeTreeResponse | TraineeNodeTreeResponse:
        """Return the full recursive tree for a space. Only active nodes included."""
        await _assert_space_access(self.session, space_id, user_id, role)

        repo = NodeRepository(self.session)
        nodes = await repo.get_all_active_nodes(space_id)

        if role == "trainee":
            nodes_with_published_material = (
                await repo.get_nodes_with_published_material(space_id)
            )
            roots = _build_tree_for_trainee(
                nodes,
                nodes_with_published_material=nodes_with_published_material,
            )
            return TraineeNodeTreeResponse(
                space_id=space_id,
                roots=roots,
                total_nodes=len(nodes),
            )

        roots = _build_tree(nodes)

        return NodeTreeResponse(
            space_id=space_id,
            roots=roots,
            total_nodes=len(nodes),
        )

    # ── get single node ────────────────────────────────────────────────

    async def get_node(self, node_id: UUID, user_id: UUID, role: str) -> NodeResponse:
        """Fetch a single node. Validates space access for the caller's role."""
        repo = NodeRepository(self.session)
        node = await repo.get_node_by_id(node_id)
        if node is None:
            raise NodeNotFoundException()

        await _assert_space_access(self.session, node.space_id, user_id, role)
        return await self._build_node_response_with_effective_instruction(repo, node)

    # ── rename ─────────────────────────────────────────────────────────

    async def rename_node(
        self, node_id: UUID, request: NodeRenameRequest, user_id: UUID, role: str
    ) -> NodeResponse:
        """Update title only. node_id is stable; all FKs remain valid (EC-1)."""
        _assert_mentor(role)
        repo = NodeRepository(self.session)

        node = await repo.get_node_by_id(node_id)
        if node is None:
            raise NodeNotFoundException()

        await _get_space_and_assert_owner(self.session, node.space_id, user_id)

        if not node.is_active:
            raise NodeArchivedModificationException()

        node = await repo.update_node_title(node, request.title)
        return await self._build_node_response_with_effective_instruction(repo, node)

    # ── update instruction ─────────────────────────────────────────────

    async def update_node_instruction(
        self,
        node_id: UUID,
        request: NodeUpdateInstructionRequest,
        user_id: UUID,
        role: str,
    ) -> NodeResponse:
        """Partial update for node instruction fields.

        Three instruction modes:
          node_specific_instruction  — full override; ignores inherited defaults
          tree_default_instruction   — default inherited by all descendants
          node_additive_instruction  — additive extra for this node only; NOT inherited

        Partial-update rule (PATCH semantics):
          - node_specific_instruction and tree_default_instruction are always written
            (pass null to clear).
          - node_additive_instruction uses the UNSET sentinel:
              field omitted in payload  → existing DB value preserved
              field sent as null        → field cleared (set to NULL)
              field sent with string    → field written
        """
        _assert_mentor(role)
        repo = NodeRepository(self.session)

        node = await repo.get_node_by_id(node_id)
        if node is None:
            raise NodeNotFoundException()

        await _get_space_and_assert_owner(self.session, node.space_id, user_id)

        if not node.is_active:
            raise NodeArchivedModificationException()

        if "instruction_mode" in request.model_fields_set and request.instruction_mode:
            node_specific, additive, tree_default = (
                resolve_instruction_fields_from_mode(
                    instruction_mode=request.instruction_mode,
                    instruction_text=request.instruction_text,
                    branch_default_instruction=request.branch_default_instruction,
                )
            )
        else:
            node_specific = request.node_specific_instruction
            tree_default = request.tree_default_instruction
            additive = (
                request.node_additive_instruction
                if "node_additive_instruction" in request.model_fields_set
                else UNSET
            )

        node = await repo.update_node_instruction(
            node,
            node_specific_instruction=node_specific,
            tree_default_instruction=tree_default,
            node_additive_instruction=additive,
        )
        return await self._build_node_response_with_effective_instruction(repo, node)

    # ── reparent ───────────────────────────────────────────────────────

    async def reparent_node(
        self, node_id: UUID, request: NodeReparentRequest, user_id: UUID, role: str
    ) -> NodeResponse:
        """Move node to a new parent. Validates: same space, no cycle, active parent."""
        _assert_mentor(role)
        repo = NodeRepository(self.session)

        node = await repo.get_node_by_id(node_id)
        if node is None:
            raise NodeNotFoundException()

        await _get_space_and_assert_owner(self.session, node.space_id, user_id)

        if not node.is_active:
            raise NodeArchivedModificationException()

        new_parent_id = request.new_parent_id
        new_level = 1

        if new_parent_id is not None:
            new_parent = await repo.get_node_by_id(new_parent_id)

            # Must belong to the same space
            if new_parent is None or new_parent.space_id != node.space_id:
                raise NodeParentSpaceMismatchException()

            # Parent must be active
            if not new_parent.is_active:
                raise NodeParentArchivedException()

            # Circular reference guard: new_parent must not be a descendant of node
            descendants = await _get_descendant_ids(node_id, repo)
            if new_parent_id in descendants or new_parent_id == node_id:
                raise NodeCircularReferenceException()

            new_level = new_parent.level + 1

        # Resolve new order_index
        new_order_index = request.new_order_index
        if new_order_index is None:
            new_order_index = await repo.get_next_order_index(
                node.space_id, new_parent_id
            )

        node = await repo.reparent_node(node, new_parent_id, new_level, new_order_index)
        return await self._build_node_response_with_effective_instruction(repo, node)

    # ── reorder ────────────────────────────────────────────────────────

    async def reorder_node(
        self, node_id: UUID, request: NodeReorderRequest, user_id: UUID, role: str
    ) -> dict:
        """Reorder a node by shifting it up or down among its active siblings."""
        _assert_mentor(role)
        repo = NodeRepository(self.session)

        node = await repo.get_node_by_id(node_id)
        if node is None:
            raise NodeNotFoundException()

        await _get_space_and_assert_owner(self.session, node.space_id, user_id)

        if not node.is_active:
            raise NodeArchivedModificationException()

        # Fetch all siblings under the same parent
        siblings = (
            await repo.get_children(node.parent_id)
            if node.parent_id
            else await repo.get_root_nodes(node.space_id)
        )

        # Filter active siblings and sort them by current order_index
        active_siblings = sorted(
            [s for s in siblings if s.is_active], key=lambda s: s.order_index
        )

        # Find index of current node
        idx = next(
            (i for i, s in enumerate(active_siblings) if s.node_id == node_id),
            -1,
        )
        if idx == -1:
            raise NodeNotFoundException()

        # Swap based on direction
        if request.direction == "up":
            if idx > 0:
                active_siblings[idx], active_siblings[idx - 1] = (
                    active_siblings[idx - 1],
                    active_siblings[idx],
                )
        elif request.direction == "down":
            if idx < len(active_siblings) - 1:
                active_siblings[idx], active_siblings[idx + 1] = (
                    active_siblings[idx + 1],
                    active_siblings[idx],
                )

        # Build {node_id: order_index} map and commit bulk update
        order_map = {item.node_id: i for i, item in enumerate(active_siblings)}
        await repo.bulk_update_order_index(order_map)

        return {"detail": "Node reordered successfully."}

    # ── archive ────────────────────────────────────────────────────────

    async def archive_node(
        self, node_id: UUID, request: NodeArchiveRequest, user_id: UUID, role: str
    ) -> dict:
        """Soft-archive a node and optionally all its descendants (EC-3)."""
        _assert_mentor(role)
        repo = NodeRepository(self.session)

        node = await repo.get_node_by_id(node_id)
        if node is None:
            raise NodeNotFoundException()

        await _get_space_and_assert_owner(self.session, node.space_id, user_id)

        if not node.is_active:
            raise NodeAlreadyArchivedException()

        ids_to_archive = [node_id]

        if "archive_children" in request.model_fields_set:
            archive_children = request.archive_children
        else:
            descendant_ids = await _get_descendant_ids(node_id, repo)
            archive_children = len(descendant_ids) > 0

        if archive_children:
            descendant_ids = await _get_descendant_ids(node_id, repo)
            ids_to_archive.extend(descendant_ids)

        await repo.archive_nodes(ids_to_archive)
        return {
            "detail": "Node archived.",
            "archived_count": len(ids_to_archive),
        }
