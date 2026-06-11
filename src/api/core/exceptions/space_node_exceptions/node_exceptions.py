# src/api/core/exceptions/identity_exceptions/node_exceptions.py
"""HTTP exceptions for topic tree (topic_nodes) operations.

Edge cases covered:
  EC-1  NodeRenameStableIdException  — informational; rename is always safe
  EC-2  NodeReparentLevelMismatch    — caught before commit if parent is in wrong space
  EC-3  NodeArchiveWithAttemptsWarning — not raised; archive always succeeds
  EC-6  Not applicable here (Learning Content concern)

All exceptions extend HTTPException for direct FastAPI raise compatibility.
"""

from fastapi import HTTPException, status


# ── Node Not Found ──────────────────────────────────────────────────────────

class NodeNotFoundException(HTTPException):
    """Raised when a node_id does not exist or does not belong to the given space."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic node not found.",
        )


# ── Node Access ─────────────────────────────────────────────────────────────

class NodeForbiddenException(HTTPException):
    """
    Raised when a mentor attempts to modify a node that belongs to a space
    they do not own (not effective owner via COALESCE check).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this node.",
        )


# ── Node State ──────────────────────────────────────────────────────────────

class NodeAlreadyArchivedException(HTTPException):
    """
    Raised when attempting to archive a node that is already archived
    (is_active = false). Prevents duplicate archive operations.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node is already archived.",
        )


class NodeArchivedModificationException(HTTPException):
    """
    Raised when a mentor attempts to rename, reparent, or add children
    to a node that has been archived (is_active = false).
    Archived nodes are read-only.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot modify an archived node.",
        )


# ── Tree Structure Violations ───────────────────────────────────────────────

class NodeParentSpaceMismatchException(HTTPException):
    """
    Raised during node creation or reparenting when the provided
    parent_id belongs to a different space than the node being created/moved.
    Prevents cross-space tree contamination.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent node does not belong to the same space.",
        )


class NodeCircularReferenceException(HTTPException):
    """
    Raised during reparent (EC-2) when the new_parent_id is a descendant
    of the node being moved — which would create a cycle in the tree.
    Service validates this by walking the ancestor chain before committing.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reparent a node under one of its own descendants.",
        )


class NodeParentArchivedException(HTTPException):
    """
    Raised when a mentor tries to create a new child node under an archived
    parent node. Children can only be added to active nodes.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot add a child to an archived parent node.",
        )


# ── Reorder Violations ──────────────────────────────────────────────────────

class NodeReorderSiblingMismatchException(HTTPException):
    """
    Raised during bulk reorder when the submitted node_ids do not all share
    the same parent_id within the same space. All nodes in a reorder
    batch must be siblings (same parent).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All nodes in a reorder batch must be siblings (same parent).",
        )


class NodeReorderIncompleteException(HTTPException):
    """
    Raised when a reorder payload is missing one or more siblings that exist
    under the same parent. Partial reorders are rejected to prevent
    order_index gaps or duplicates.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reorder payload must include all siblings under this parent.",
        )