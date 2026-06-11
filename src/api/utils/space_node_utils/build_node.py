from uuid import UUID

from src.api.data.models.postgres.e_spaces_trees.topic_nodes import TopicNode
from src.api.schemas.space_node_schemas.node_schema import NodeResponse, NodeTreeNode

# ── Instruction resolver ────────────────────────────────────────────────────────


def resolve_effective_instruction(
    node: TopicNode,
    ancestors: list[TopicNode],
) -> str | None:
    """Return the effective instruction string for *node* given its ancestor chain.

    Parameters
    ----------
    node:
        The current node whose effective instruction is being resolved.
    ancestors:
        Ordered list of ancestor TopicNode objects from root down to (but NOT
        including) the current node.  The current node's own
        node_additive_instruction is appended last; it must NOT appear in
        this list — that would accidentally add it to descendants.

    Resolution order
    ----------------
    1. If node.node_specific_instruction is non-empty → return it alone (full override).
    2. Otherwise collect tree_default_instruction from each ancestor (root → parent)
       that is non-empty, then include this node's tree_default_instruction if set,
       then append this node's node_additive_instruction if set.
    3. Null, empty-string, and whitespace-only values are silently ignored.
    4. Parts are joined with two newlines ("\\n\\n") for readability.
    5. Returns None when no effective instruction is present.

    Business rules
    --------------
    - node_additive_instruction is NEVER passed to descendants (callers must not
      include the parent's additive instruction in the ancestors list for child nodes).
    - The frontend uses the same logic for its live preview (computed from the
      in-memory tree passed via the roots prop).
    """

    def _nonempty(s: str | None) -> str | None:
        stripped = s.strip() if s else None
        return stripped if stripped else None

    # Rule 1: node-specific override
    nsi = _nonempty(node.node_specific_instruction)
    if nsi:
        return nsi

    # Rule 2: inherited treedefault chain + this node's additive
    parts: list[str] = []

    for ancestor in ancestors:
        val = _nonempty(ancestor.tree_default_instruction)
        if val:
            parts.append(val)

    current_tdi = _nonempty(node.tree_default_instruction)
    if current_tdi:
        parts.append(current_tdi)

    current_nai = _nonempty(node.node_additive_instruction)
    if current_nai:
        parts.append(current_nai)

    return "\n\n".join(parts) if parts else None


# ── Response builders ───────────────────────────────────────────────────────────


def _build_node_response(node: TopicNode) -> NodeResponse:
    return NodeResponse(
        node_id=node.node_id,
        space_id=node.space_id,
        parent_id=node.parent_id,
        title=node.title,
        level=node.level,
        order_index=node.order_index,
        node_specific_instruction=node.node_specific_instruction,
        tree_default_instruction=node.tree_default_instruction,
        node_additive_instruction=node.node_additive_instruction,
        is_primary_learning_unit=node.is_primary_learning_unit,
        is_active=node.is_active,
        created_by=node.created_by,
        created_at=node.created_at,
        updated_at=node.updated_at,
        source_pdf_id=node.source_pdf_id,
        source_section_path=node.source_section_path,
        auto_generated=node.auto_generated,
    )


def _build_tree(nodes: list) -> list[NodeTreeNode]:
    """Build recursive NodeTreeNode tree from a flat list of ORM node objects."""
    node_map: dict[UUID, NodeTreeNode] = {}
    roots: list[NodeTreeNode] = []

    for node in sorted(nodes, key=lambda item: item.order_index):
        node_map[node.node_id] = NodeTreeNode(
            node_id=node.node_id,
            parent_id=node.parent_id,
            title=node.title,
            level=node.level,
            order_index=node.order_index,
            node_specific_instruction=node.node_specific_instruction,
            tree_default_instruction=node.tree_default_instruction,
            node_additive_instruction=node.node_additive_instruction,
            is_active=node.is_active,
            auto_generated=node.auto_generated,
            children=[],
        )

    for node in nodes:
        tree_node = node_map[node.node_id]
        if node.parent_id is None:
            roots.append(tree_node)
        else:
            parent = node_map.get(node.parent_id)
            if parent:
                parent.children.append(tree_node)

    return roots
