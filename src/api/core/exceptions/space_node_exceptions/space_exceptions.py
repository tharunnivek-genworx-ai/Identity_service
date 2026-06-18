"""HTTP exceptions for e-learning space operations.

All exceptions map to a specific HTTP status and carry a detail string
that is safe to surface to the client.

Naming convention (mirrors auth_exceptions.py):
  - XxxNotFoundException   → 404
  - XxxAlreadyExistsException → 409
  - XxxForbiddenException  → 403
  - XxxConflictException   → 409 (state-based conflicts)
  - XxxBadRequestException → 400 (invalid input that passes schema validation)
"""

from fastapi import HTTPException, status

# ── Space Not Found ─────────────────────────────────────────────────────────


class SpaceNotFoundException(HTTPException):
    """Raised when a space_id does not exist or is not active."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E-learning space not found.",
        )


# ── Space Access / Ownership ────────────────────────────────────────────────


class SpaceForbiddenException(HTTPException):
    """
    Raised when a mentor attempts to modify a space they do not own
    (neither original mentor_id nor transferred_to_mentor_id).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this space.",
        )


class SpaceNotPublishedException(HTTPException):
    """
    Raised when a trainee attempts to join or access a space that
    has not been published by the mentor (is_published = false).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This space is not published and cannot be joined.",
        )


# ── Space State Conflicts ───────────────────────────────────────────────────


class SpaceAlreadyPublishedException(HTTPException):
    """
    Raised when a mentor tries to publish a space that is already published.
    Guards against duplicate publish events creating spurious notifications.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Space is already published.",
        )


class SpaceArchivedConflictException(HTTPException):
    """
    Raised when attempting to modify (add trainees, create nodes, etc.)
    on a space that has been archived (archived_at is not None).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot modify an archived space.",
        )


# ── Invite Code ─────────────────────────────────────────────────────────────


class InvalidInviteCodeException(HTTPException):
    """
    Raised when a trainee provides an invite code that does not match
    any active, published space.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite code.",
        )


class InviteCodeGenerationFailedException(HTTPException):
    """
    Raised when the service fails to produce a unique invite code after
    the maximum number of retry attempts (collision guard).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a unique invite code. Please try again.",
        )


# ── Membership ──────────────────────────────────────────────────────────────


class TraineeAlreadyMemberException(HTTPException):
    """
    Raised when a mentor tries to manually add a trainee who is already
    an active member of the space (space_trainees.is_active = true).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trainee is already an active member of this space.",
        )


class TraineeNotMemberException(HTTPException):
    """
    Raised when a mentor tries to remove a trainee who is not a member
    (or is already inactive) in the space.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainee is not an active member of this space.",
        )


class TraineeAlreadyJoinedViaInviteException(HTTPException):
    """
    Raised when a trainee tries to join a space via invite code but
    already has an active space_trainees record for that space.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this space.",
        )


class TraineeRemovedFromSpaceException(HTTPException):
    """
    Raised when a trainee who was manually removed from a space attempts
    to rejoin via invite code. Only a mentor manual add can reactivate them.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You were removed from this space. Ask the mentor to add you again.",
        )


# ── Department ──────────────────────────────────────────────────────────────


class DepartmentNotFoundException(HTTPException):
    """
    Raised when a space is being created with a department_id that does
    not exist or is not active.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )


# ── Ownership Transfer ──────────────────────────────────────────────────────


class TransferTargetNotFoundException(HTTPException):
    """
    Raised during mentor deactivation ownership transfer (EC-27) when
    the target transferred_to_mentor_id does not exist or is inactive.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer target mentor not found or is not active.",
        )


class CannotTransferToSameMentorException(HTTPException):
    """
    Raised when ITAdmin tries to transfer ownership to the mentor who
    already owns the space (no-op guard).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer target is the same as the current space owner.",
        )
