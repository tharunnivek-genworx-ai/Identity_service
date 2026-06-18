"""Repository for all topic_nodes DB operations.

Handles:
  - Single node lookups (by id, by ids batch)
  - Full space tree fetch (all active nodes)
  - Children and root node queries
  - order_index resolution (MAX + 1 for appending siblings)
  - Node insert, title update, instruction update, reparent, archive
  - Bulk order_index update for sibling reorder

Instruction partial-update semantics (update_node_instruction):
  node_specific_instruction and tree_default_instruction follow the same
  always-write pattern as before.
  node_additive_instruction uses an UNSET sentinel — pass UNSET to preserve
  the existing DB value, or pass None/str to clear/write it.
  The service layer resolves which sentinel value to use based on
  model_fields_set from the incoming Pydantic request.
"""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.data.models.postgres.e_spaces_trees.topic_nodes import TopicNode
from src.api.data.models.postgres.study_material_models.study_material_versions import (
    StudyMaterialVersion,
)


# Sentinel object — distinct from None, signals "caller did not provide this field"
class _UnsetType:
    """Singleton sentinel for 'not provided' in partial-update calls."""

    _instance = None

    def __new__(cls) -> "_UnsetType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _UnsetType()


class NodeRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    # ── Lookups ─────────────────────────────────────────────────────────

    async def get_node_by_id(self, node_id: UUID) -> TopicNode | None:
        result = await self.db.execute(
            select(TopicNode).where(TopicNode.node_id == node_id)
        )
        return cast(TopicNode | None, result.scalars().first())

    async def get_nodes_by_ids(
        self, node_ids: list[UUID], space_id: UUID
    ) -> list[TopicNode]:
        """Fetch nodes by ID within a space. Used for reorder validation."""
        result = await self.db.execute(
            select(TopicNode).where(
                and_(
                    TopicNode.node_id.in_(node_ids),
                    TopicNode.space_id == space_id,
                )
            )
        )
        return list(result.scalars().all())

    async def get_all_active_nodes(self, space_id: UUID) -> list[TopicNode]:
        """Fetch all is_active nodes in a space for tree construction."""
        result = await self.db.execute(
            select(TopicNode).where(
                and_(
                    TopicNode.space_id == space_id,
                    TopicNode.is_active.is_(True),
                )
            )
        )
        return list(result.scalars().all())

    async def get_nodes_with_published_material(self, space_id: UUID) -> set[UUID]:
        """Return node IDs that currently have at least one published material row."""
        result = await self.db.execute(
            select(StudyMaterialVersion.nodeid)
            .where(
                and_(
                    StudyMaterialVersion.spaceid == space_id,
                    StudyMaterialVersion.ispublished.is_(True),
                )
            )
            .distinct()
        )
        return set(result.scalars().all())

    async def get_children(self, parent_id: UUID) -> list[TopicNode]:
        """Fetch all direct children (active and inactive) of a parent node."""
        result = await self.db.execute(
            select(TopicNode).where(TopicNode.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def get_root_nodes(self, space_id: UUID) -> list[TopicNode]:
        """Fetch all root-level nodes (parent_id = NULL) for a space."""
        result = await self.db.execute(
            select(TopicNode).where(
                and_(
                    TopicNode.space_id == space_id,
                    TopicNode.parent_id.is_(None),
                    TopicNode.is_active.is_(True),
                )
            )
        )
        return list(result.scalars().all())

    async def get_ancestors(self, node: TopicNode) -> list[TopicNode]:
        """Return active ancestors ordered from root down to the node's parent."""
        ancestors: list[TopicNode] = []
        parent_id = node.parent_id

        while parent_id is not None:
            parent = await self.get_node_by_id(parent_id)
            if (
                parent is None
                or parent.space_id != node.space_id
                or not parent.is_active
            ):
                break
            ancestors.append(parent)
            parent_id = parent.parent_id

        ancestors.reverse()
        return ancestors

    async def get_next_order_index(self, space_id: UUID, parent_id: UUID | None) -> int:
        """Return MAX(order_index) + 1 among siblings. Returns 0 if no siblings."""
        result = await self.db.execute(
            select(func.max(TopicNode.order_index)).where(
                and_(
                    TopicNode.space_id == space_id,
                    TopicNode.parent_id == parent_id,
                    TopicNode.is_active.is_(True),
                )
            )
        )
        max_index = result.scalar()
        return (max_index + 1) if max_index is not None else 0

    # ── Writes ──────────────────────────────────────────────────────────

    async def create_node(
        self,
        space_id: UUID,
        parent_id: UUID | None,
        title: str,
        level: int,
        order_index: int,
        node_specific_instruction: str | None,
        tree_default_instruction: str | None,
        node_additive_instruction: str | None,
        created_by: UUID,
    ) -> TopicNode:
        now = datetime.now(UTC)
        node = TopicNode(
            node_id=uuid4(),
            space_id=space_id,
            parent_id=parent_id,
            title=title,
            level=level,
            order_index=order_index,
            node_specific_instruction=node_specific_instruction,
            tree_default_instruction=tree_default_instruction,
            node_additive_instruction=node_additive_instruction,
            is_primary_learning_unit=False,  # MVP: not used, always False
            is_active=True,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            source_pdf_id=None,
            source_section_path=None,
            auto_generated=False,
        )
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def update_node_title(self, node: TopicNode, title: str) -> TopicNode:
        node.title = title
        node.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def update_node_instruction(
        self,
        node: TopicNode,
        node_specific_instruction: str | None,
        tree_default_instruction: str | None,
        node_additive_instruction: str | None | _UnsetType = UNSET,
    ) -> TopicNode:
        """Update instruction fields on a node.

        node_specific_instruction and tree_default_instruction are always
        written (pass None to clear).

        node_additive_instruction uses the UNSET sentinel:
          - UNSET  → field is not touched (existing DB value preserved)
          - None   → field is cleared (set to NULL)
          - str    → field is written with that value
        """
        node.node_specific_instruction = node_specific_instruction
        node.tree_default_instruction = tree_default_instruction
        if not isinstance(node_additive_instruction, _UnsetType):
            node.node_additive_instruction = node_additive_instruction
        node.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def reparent_node(
        self,
        node: TopicNode,
        new_parent_id: UUID | None,
        new_level: int,
        new_order_index: int,
    ) -> TopicNode:
        node.parent_id = new_parent_id
        node.level = new_level
        node.order_index = new_order_index
        node.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def bulk_update_order_index(self, order_map: dict[UUID, int]) -> None:
        """Update order_index for multiple nodes in one transaction."""
        now = datetime.now(UTC)
        for node_id, order_index in order_map.items():
            await self.db.execute(
                update(TopicNode)
                .where(TopicNode.node_id == node_id)
                .values(order_index=order_index, updated_at=now)
            )
        await self.db.commit()

    async def archive_nodes(self, node_ids: list[UUID]) -> None:
        """Bulk soft-archive: set is_active = False for all given node_ids."""
        now = datetime.now(UTC)
        await self.db.execute(
            update(TopicNode)
            .where(TopicNode.node_id.in_(node_ids))
            .values(is_active=False, updated_at=now)
        )
        await self.db.commit()
