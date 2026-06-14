# src/api/schemas/identity_schemas/space_schema.py
"""Pydantic schemas for e-learning space operations.

Covers:
  - Space creation, update, and response shapes
  - Trainee membership management (add/remove)
  - Invite code join
  - Space publish
  - Ownership transfer (called by ITAdmin route, schema lives here)

All UUIDs are validated as proper UUID types.
Effective mentor resolution (COALESCE logic) is handled at the service layer —
these schemas only carry raw field values.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.api.schemas.identity_schemas.listing_endpoints import (
    PaginatedResponse,
)

# ── Create ─────────────────────────────────────────────────────────────────


class SpaceCreateRequest(BaseModel):
    """Mentor creates a new e-learning space."""

    space_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None)
    department_id: UUID
    # invite_code is auto-generated at service layer; not accepted from client


# ── Update ─────────────────────────────────────────────────────────────────


class SpaceUpdateRequest(BaseModel):
    """Partial update — all fields optional. Only provided fields are applied."""

    space_name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None)


# ── Publish ────────────────────────────────────────────────────────────────


class SpacePublishRequest(BaseModel):
    """
    Explicit publish toggle. Accepts is_published to support both
    publish and unpublish actions from the same endpoint.
    """

    is_published: bool


# ── Ownership Transfer (IT Admin) ──────────────────────────────────────────


class SpaceTransferOwnershipRequest(BaseModel):
    """
    Called by ITAdmin when deactivating a mentor (EC-27).
    Sets e_spaces.transferred_to_mentor_id for all spaces owned
    by the deactivated mentor — or a targeted single space.
    """

    transferred_to_mentor_id: UUID


# ── Membership: Manual Add ─────────────────────────────────────────────────


class SpaceAddTraineesRequest(BaseModel):
    """
    Mentor manually adds one or more trainees to a space.
    Raises 409 if any trainee is already an active member.
    Previously removed members (is_active = false) are reactivated.
    """

    trainee_ids: list[UUID] = Field(..., min_length=1)


class SpaceRemoveTraineeRequest(BaseModel):
    """
    Mentor soft-removes a trainee (sets space_trainees.is_active = false).
    Historical attempts and progress are preserved (EC-13, EC-15).
    """

    trainee_id: UUID


# ── Membership: Join via Invite Code ───────────────────────────────────────


class SpaceJoinRequest(BaseModel):
    """Trainee joins a published space using its invite code."""

    invite_code: str = Field(..., min_length=1, max_length=20)


# ── Response Shapes ────────────────────────────────────────────────────────


class SpaceMemberSummary(BaseModel):
    """Compact trainee info embedded in space responses."""

    model_config = ConfigDict(from_attributes=True)

    trainee_id: UUID
    full_name: str
    email: str
    joined_via: str
    joined_at: datetime
    is_active: bool


class SpaceResponse(BaseModel):
    """
    Full space payload returned to the mentor after create / get.
    effective_mentor_id resolves COALESCE(transferred_to_mentor_id, mentor_id)
    at the service layer so the frontend always has one authoritative owner ID.
    """

    model_config = ConfigDict(from_attributes=True)

    space_id: UUID
    space_name: str
    description: str | None
    department_id: UUID
    mentor_id: UUID
    transferred_to_mentor_id: UUID | None
    effective_mentor_id: UUID  # resolved at service layer
    invite_code: str | None
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class SpaceListResponse(PaginatedResponse[SpaceResponse]):
    """Paginated list of spaces for mentor/trainee dashboards."""

    pass


class AdminMentorSpaceOut(SpaceResponse):
    """IT Admin view of a mentor's owned space with transfer eligibility."""

    needs_ownership_transfer: bool = Field(
        ...,
        description=(
            "True when this mentor is still the effective owner and "
            "ownership should be transferred (EC-27)."
        ),
    )


class AdminMentorSpaceListResponse(PaginatedResponse[AdminMentorSpaceOut]):
    """Paginated spaces owned by a mentor (audit mentor_id)."""

    pass


class AdminMentorTransferredSpaceIn(AdminMentorSpaceOut):
    """Space whose effective owner was transferred to the viewed mentor."""

    original_mentor_id: UUID
    original_mentor_name: str


class AdminMentorSpaceOverviewResponse(BaseModel):
    """IT Admin mentor space transfer dashboard (EC-27)."""

    owned_spaces: list[AdminMentorSpaceOut] = Field(default_factory=list)
    transferred_in_spaces: list[AdminMentorTransferredSpaceIn] = Field(
        default_factory=list
    )


class SpaceJoinResponse(BaseModel):
    """Returned to trainee after successfully joining a space."""

    space_id: UUID
    space_name: str
    joined_via: str
    joined_at: datetime
