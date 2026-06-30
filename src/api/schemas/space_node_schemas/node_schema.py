# src/api/schemas/identity_schemas/node_schema.py
"""Pydantic schemas for topic tree (topic_nodes) operations.

Covers:
  - Node creation (single node or bulk for auto-tree preview)
  - Rename, reparent, reorder, archive
  - Tree read responses (flat list and nested recursive tree)

Design rules from TDD §3.3.1 topic_nodes table:
  - parent_id = None → root node (level 1)
  - level is maintained at the service layer on insert/reparent
  - order_index is an explicit sibling position integer (0-based)
  - is_primary_learning_unit is stored but NOT used in MVP logic
  - Every node at every depth is a full learning unit

Instruction fields — three independent columns, resolved by the service layer:
  - tree_default_instruction  : subtree-scoped inherited default (set on a node, inherited by descendants)
  - node_additive_instruction : current-node-only additive instruction, appended on top of inherited defaults;
                                NOT inherited by descendants
  - node_specific_instruction : current-node-only full override; when set, inherited defaults and
                                node_additive_instruction are ignored for this node

  Resolution order (see resolve_effective_instruction_parts in build_node.py):
    1. node_specific_instruction set → use only it
    2. else: collect inherited tree_default_instruction chain (root → current node)
             + append this node's node_additive_instruction

Partial-update semantics for PATCH /nodes/{id}/instruction:
  - Field omitted from payload → existing DB value is preserved
  - Field sent as null         → DB value is cleared (set to NULL)
  - Field sent with text       → DB value is written
  (service layer uses model_fields_set to distinguish omit vs null)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Create ─────────────────────────────────────────────────────────────────


class NodeCreateRequest(BaseModel):
    """
    Mentor creates a single node in the topic tree.
    parent_id = None creates a root-level topic.
    order_index defaults to appending at the end (service layer resolves this
    by querying MAX(order_index) + 1 among siblings if not provided).
    """

    title: str = Field(..., min_length=1, max_length=300)
    parent_id: UUID | None = Field(
        default=None,
        description="NULL for root nodes. Must belong to the same space.",
    )
    order_index: int | None = Field(
        default=None,
        ge=0,
        description="Explicit sibling position. Omit to auto-append.",
    )
    node_specific_instruction: str | None = Field(
        default=None,
        description="Full override for this node only. Ignores inherited defaults when set.",
    )
    tree_default_instruction: str | None = Field(
        default=None,
        description="Default instruction inherited by all descendants of this node.",
    )
    node_additive_instruction: str | None = Field(
        default=None,
        description=(
            "Additive instruction for this node only. "
            "Appended on top of inherited tree_default_instruction chain. "
            "NOT inherited by descendants."
        ),
    )


# ── Rename ─────────────────────────────────────────────────────────────────


class NodeRenameRequest(BaseModel):
    """
    Rename a node's title only.
    node_id is stable — all downstream FKs (attempts, progress, versions)
    remain valid after rename (EC-1).
    """

    title: str = Field(..., min_length=1, max_length=300)


# ── Update Instruction ─────────────────────────────────────────────────────


class NodeUpdateInstructionRequest(BaseModel):
    """
    Partial update for any combination of the three instruction fields.

    Preferred mentor flow: send instruction_mode + instruction_text +
    branch_default_instruction and let the service map to DB columns.

    Legacy/direct flow: send node_specific_instruction, tree_default_instruction,
    and node_additive_instruction with PATCH semantics below.

    Partial-update semantics (direct fields):
      - Field omitted from the JSON body → existing DB value is PRESERVED
      - Field sent as null               → DB value is CLEARED (set to NULL)
      - Field sent with a string         → DB value is WRITTEN

    Instruction meanings:
      node_specific_instruction  — full override for this node only
      tree_default_instruction   — default inherited by all descendants
      node_additive_instruction  — additive extra for this node only; not inherited
    """

    instruction_mode: Literal["inherit", "extend", "replace"] | None = Field(
        default=None,
        description=(
            "Mentor UI mode. When set, instruction_text and "
            "branch_default_instruction are mapped to DB columns by the service."
        ),
    )
    instruction_text: str | None = Field(
        default=None,
        description="Mode-specific instruction body (extend/replace). Ignored for inherit.",
    )
    branch_default_instruction: str | None = Field(
        default=None,
        description="tree_default_instruction for this node's branch.",
    )
    node_specific_instruction: str | None = Field(default=None)
    tree_default_instruction: str | None = Field(default=None)
    node_additive_instruction: str | None = Field(default=None)


# ── Reparent ───────────────────────────────────────────────────────────────


class NodeReparentRequest(BaseModel):
    """
    Move a node to a different parent (or to root level if new_parent_id = None).
    Service layer recalculates level after reparenting (EC-2).
    node_id remains stable; breadcrumbs are recomputed from the live tree.
    new_order_index controls position among new siblings.
    """

    new_parent_id: UUID | None = Field(
        default=None,
        description="Target parent node. None = promote to root.",
    )
    new_order_index: int | None = Field(
        default=None,
        ge=0,
        description="Position among new siblings. Omit to auto-append.",
    )


# ── Reorder ────────────────────────────────────────────────────────────────


class NodeReorderRequest(BaseModel):
    """
    Reorder a sibling node by moving it up or down.
    """

    direction: Literal["up", "down"]


# ── Archive ────────────────────────────────────────────────────────────────


class NodeArchiveRequest(BaseModel):
    """
    Soft-archive a node (is_active = false).
    Archived nodes no longer contribute to space progress total_nodes.
    Historical attempts remain readable in reports (EC-3).
    archive_children controls whether child nodes are also archived
    — service applies this recursively when True.
    """

    archive_children: bool = Field(
        default=True,
        description="If True, all descendant nodes are also archived.",
    )


class NodeArchiveOut(BaseModel):
    """Confirmation after soft-archiving one or more topic nodes."""

    detail: str = "Node archived."
    archived_count: int
    archived_node_ids: list[UUID] = Field(default_factory=list)


# ── Response: Flat Node ────────────────────────────────────────────────────


InstructionPartType = Literal["inherited", "branch-default", "extra", "override"]


class EffectiveInstructionPart(BaseModel):
    """One labeled part of the backend-resolved teaching instruction preview."""

    source_node_id: UUID
    source_node_title: str
    text: str
    type: InstructionPartType
    label: str


class NodeResponse(BaseModel):
    """
    Single node as returned from create / rename / reparent endpoints.
    Does not include children — use NodeTreeResponse for full tree reads.
    """

    model_config = ConfigDict(from_attributes=True)

    node_id: UUID
    space_id: UUID
    parent_id: UUID | None
    title: str
    level: int
    order_index: int
    node_specific_instruction: str | None
    tree_default_instruction: str | None
    node_additive_instruction: str | None
    effective_instruction: str | None = None
    effective_instruction_parts: list[EffectiveInstructionPart] = Field(
        default_factory=list
    )
    is_primary_learning_unit: bool
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    # Phase 2 fields — present in response but None in MVP
    source_pdf_id: UUID | None
    source_section_path: str | None
    auto_generated: bool


# ── Response: Recursive Tree ───────────────────────────────────────────────


class NodeTreeNode(BaseModel):
    """
    Recursive node shape used in GET /spaces/{space_id}/tree.
    children is a sorted (by order_index) list of child NodeTreeNodes.
    Frontend uses this to render the full collapsible topic tree.
    """

    model_config = ConfigDict(from_attributes=True)

    node_id: UUID
    parent_id: UUID | None
    title: str
    level: int
    order_index: int
    node_specific_instruction: str | None
    tree_default_instruction: str | None
    node_additive_instruction: str | None
    effective_instruction: str | None = None
    effective_instruction_parts: list[EffectiveInstructionPart] = Field(
        default_factory=list
    )
    is_active: bool
    auto_generated: bool
    children: list[NodeTreeNode] = Field(default_factory=list)

    # Resolved at service layer from Engagement & Chat Service data (omitted
    # in this service's own response; included when aggregated by gateway):
    # completion_status: Optional[str] = None


class NodeTreeResponse(BaseModel):
    """Full recursive topic tree for a space, roots only at the top level."""

    space_id: UUID
    roots: list[NodeTreeNode]
    total_nodes: int  # count of all is_active nodes in the space


class TraineeNodeTreeNode(BaseModel):
    """Trainee tree node shape with published-material visibility flag."""

    model_config = ConfigDict(from_attributes=True)

    node_id: UUID
    parent_id: UUID | None
    title: str
    level: int
    order_index: int
    node_specific_instruction: str | None
    tree_default_instruction: str | None
    node_additive_instruction: str | None
    effective_instruction: str | None = None
    effective_instruction_parts: list[EffectiveInstructionPart] = Field(
        default_factory=list
    )
    is_active: bool
    auto_generated: bool
    hasPublishedMaterial: bool
    children: list[TraineeNodeTreeNode] = Field(default_factory=list)


class TraineeNodeTreeResponse(BaseModel):
    """Trainee tree response with hasPublishedMaterial per node."""

    space_id: UUID
    roots: list[TraineeNodeTreeNode]
    total_nodes: int
