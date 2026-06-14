# src/api/core/services/identity_service/node_service.py
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
    NodeReorderIncompleteException,
    NodeReorderSiblingMismatchException,
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
)
from src.api.utils.space_node_utils.build_node import _build_node_response, _build_tree
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
    ) -> NodeTreeResponse:
        """Return the full recursive tree for a space. Only active nodes included."""
        await _assert_space_access(self.session, space_id, user_id, role)

        repo = NodeRepository(self.session)
        nodes = await repo.get_all_active_nodes(space_id)
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

    async def reorder_nodes(
        self, space_id: UUID, request: NodeReorderRequest, user_id: UUID, role: str
    ) -> dict:
        """Bulk-update order_index for siblings. Validates all nodes are siblings
        and that no sibling is missing from the payload."""
        _assert_mentor(role)
        await _get_space_and_assert_owner(self.session, space_id, user_id)

        repo = NodeRepository(self.session)
        node_ids = [item.node_id for item in request.nodes]

        # Fetch all nodes in the payload
        nodes = await repo.get_nodes_by_ids(node_ids, space_id)
        if len(nodes) != len(node_ids):
            raise NodeNotFoundException()

        # All must share the same parent_id (sibling check)
        parent_ids = {n.parent_id for n in nodes}
        if len(parent_ids) != 1:
            raise NodeReorderSiblingMismatchException()

        shared_parent_id = next(iter(parent_ids))

        # All siblings under that parent must be present in the payload
        all_siblings = (
            await repo.get_children(shared_parent_id)
            if shared_parent_id
            else await repo.get_root_nodes(space_id)
        )
        all_sibling_ids = {s.node_id for s in all_siblings if s.is_active}
        payload_ids = set(node_ids)
        if all_sibling_ids != payload_ids:
            raise NodeReorderIncompleteException()

        # Build {node_id: order_index} map and commit
        order_map = {item.node_id: item.order_index for item in request.nodes}
        await repo.bulk_update_order_index(order_map)

        return {"detail": "Nodes reordered successfully."}

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
