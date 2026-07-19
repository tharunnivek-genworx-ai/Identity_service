from uuid import UUID

from src.api.data.models.postgres.e_spaces_trees.topic_nodes import TopicNode
from src.api.schemas.space_node_schemas.node_schema import (
    EffectiveInstructionPart,
    NodeResponse,
    NodeTreeNode,
    TraineeNodeTreeNode,
)

# ── Instruction resolver ────────────────────────────────────────────────────────


def _nonempty(s: str | None) -> str | None:
    stripped = s.strip() if s else None
    return stripped if stripped else None


def resolve_effective_instruction_parts(
    node: TopicNode,
    ancestors: list[TopicNode],
) -> list[EffectiveInstructionPart]:
    """Return the labeled instruction parts for *node* using the canonical rules.

    ancestors must be ordered root → parent. Only tree_default_instruction is
    inherited from ancestors; node_additive_instruction applies to the current
    node only and must never be included in a descendant's ancestor chain.
    """

    # Rule 1: node-specific override
    nsi = _nonempty(node.node_specific_instruction)
    if nsi:
        return [
            EffectiveInstructionPart(
                source_node_id=node.node_id,
                source_node_title=node.title,
                text=nsi,
                type="override",
                label="Your custom instruction:",
            )
        ]

    # Rule 2: inherited tree-default chain + current node defaults/additive.
    parts: list[EffectiveInstructionPart] = []

    for ancestor in ancestors:
        val = _nonempty(ancestor.tree_default_instruction)
        if val:
            parts.append(
                EffectiveInstructionPart(
                    source_node_id=ancestor.node_id,
                    source_node_title=ancestor.title,
                    text=val,
                    type="inherited",
                    label=f"From parent section ({ancestor.title}):",
                )
            )

    current_tdi = _nonempty(node.tree_default_instruction)
    if current_tdi:
        parts.append(
            EffectiveInstructionPart(
                source_node_id=node.node_id,
                source_node_title=node.title,
                text=current_tdi,
                type="branch-default",
                label="Instruction for This Topic Branch:",
            )
        )

    current_nai = _nonempty(node.node_additive_instruction)
    if current_nai:
        parts.append(
            EffectiveInstructionPart(
                source_node_id=node.node_id,
                source_node_title=node.title,
                text=current_nai,
                type="extra",
                label="Prompt for this topic:",
            )
        )

    return parts


# ── Response builders ───────────────────────────────────────────────────────────


def _build_node_response(
    node: TopicNode,
    ancestors: list[TopicNode] | None = None,
) -> NodeResponse:
    ancestor_chain = ancestors or []
    effective_parts = resolve_effective_instruction_parts(node, ancestor_chain)
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
        effective_instruction=(
            "\n\n".join(part.text for part in effective_parts)
            if effective_parts
            else None
        ),
        effective_instruction_parts=effective_parts,
        is_primary_learning_unit=node.is_primary_learning_unit,
        is_active=node.is_active,
        created_by=node.created_by,
        created_at=node.created_at,
        updated_at=node.updated_at,
        source_pdf_id=node.source_pdf_id,
        source_section_path=node.source_section_path,
        auto_generated=node.auto_generated,
    )


def _build_tree(
    nodes: list,
) -> list[NodeTreeNode]:
    """Build recursive NodeTreeNode tree from a flat list of ORM node objects."""
    node_map: dict[UUID, TopicNode] = {node.node_id: node for node in nodes}
    children_by_parent: dict[UUID | None, list[TopicNode]] = {}
    roots: list[NodeTreeNode] = []

    for node in nodes:
        children_by_parent.setdefault(node.parent_id, []).append(node)

    for children in children_by_parent.values():
        children.sort(key=lambda item: item.order_index)

    def build_subtree(node: TopicNode, ancestors: list[TopicNode]) -> NodeTreeNode:
        effective_parts = resolve_effective_instruction_parts(node, ancestors)
        tree_node = NodeTreeNode(
            node_id=node.node_id,
            parent_id=node.parent_id,
            title=node.title,
            level=node.level,
            order_index=node.order_index,
            node_specific_instruction=node.node_specific_instruction,
            tree_default_instruction=node.tree_default_instruction,
            node_additive_instruction=node.node_additive_instruction,
            effective_instruction=(
                "\n\n".join(part.text for part in effective_parts)
                if effective_parts
                else None
            ),
            effective_instruction_parts=effective_parts,
            is_active=node.is_active,
            auto_generated=node.auto_generated,
            children=[
                build_subtree(child, [*ancestors, node])
                for child in children_by_parent.get(node.node_id, [])
                if child.node_id in node_map
            ],
        )
        return tree_node

    for root_node in children_by_parent.get(None, []):
        roots.append(build_subtree(root_node, []))

    return roots


def _build_tree_for_trainee(
    nodes: list,
    nodes_with_published_material: set[UUID],
    access_by_node: dict[UUID, str] | None = None,
    blocked_by_node: dict[UUID, UUID] | None = None,
) -> list[TraineeNodeTreeNode]:
    """Build trainee tree with hasPublishedMaterial per node."""
    access_by_node = access_by_node or {}
    blocked_by_node = blocked_by_node or {}
    node_map: dict[UUID, TopicNode] = {node.node_id: node for node in nodes}
    children_by_parent: dict[UUID | None, list[TopicNode]] = {}
    roots: list[TraineeNodeTreeNode] = []

    for node in nodes:
        children_by_parent.setdefault(node.parent_id, []).append(node)

    for children in children_by_parent.values():
        children.sort(key=lambda item: item.order_index)

    def build_subtree(
        node: TopicNode,
        ancestors: list[TopicNode],
    ) -> TraineeNodeTreeNode:
        effective_parts = resolve_effective_instruction_parts(node, ancestors)
        blocker_id = blocked_by_node.get(node.node_id)
        blocker = node_map.get(blocker_id) if blocker_id else None
        return TraineeNodeTreeNode(
            node_id=node.node_id,
            parent_id=node.parent_id,
            title=node.title,
            level=node.level,
            order_index=node.order_index,
            node_specific_instruction=node.node_specific_instruction,
            tree_default_instruction=node.tree_default_instruction,
            node_additive_instruction=node.node_additive_instruction,
            effective_instruction=(
                "\n\n".join(part.text for part in effective_parts)
                if effective_parts
                else None
            ),
            effective_instruction_parts=effective_parts,
            is_active=node.is_active,
            auto_generated=node.auto_generated,
            hasPublishedMaterial=node.node_id in nodes_with_published_material,
            access_status=access_by_node.get(node.node_id, "coming_soon"),
            blocked_by_node_id=blocker_id,
            blocked_by_title=blocker.title if blocker else None,
            unlock_message=f"Finish {blocker.title} first" if blocker else None,
            children=[
                build_subtree(child, [*ancestors, node])
                for child in children_by_parent.get(node.node_id, [])
                if child.node_id in node_map
            ],
        )

    for root_node in children_by_parent.get(None, []):
        roots.append(build_subtree(root_node, []))

    return roots
