from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .common_schema import Timestamped


class MentorBase(BaseModel):
    email: EmailStr
    fullname: str = Field(..., max_length=150)
    designation: str = Field(..., max_length=100)
    departmentid: UUID
    employeeid: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    profilepictureurl: Optional[str] = None
    isactive: bool = True


class MentorCreate(MentorBase):
    """
    Password is accepted as plain text here and hashed in the service layer
    before being written to passwordhash. Never expose passwordhash in any Out schema.
    """
    password: str


class MentorOut(MentorBase, Timestamped):
    """
    Response schema for mentor data. passwordhash is intentionally excluded.
    deletedat is included so the admin UI can show soft-deleted state.
    """
    model_config = ConfigDict(from_attributes=True) # tells Pydantic that this model is allowed to be built from any object’s attributes, not just from plain dicts.

    mentorid: UUID
    createdby: UUID
    deletedat: Optional[datetime] = None


class MentorDeactivateRequest(BaseModel):
    """
    Payload for PATCH /admin/mentors/:id/deactivate.

    transferred_to_mentor_id: Optional UUID of the active mentor to transfer
    the deactivated mentor's spaces to. Maps to e_spaces.transferred_to_mentor_id
    in the Space service. Per design doc EC-27 and Section 3.2.6.
    If omitted, spaces remain under the original mentor_id (accessible to trainees
    but effectively owner-less until transferred).
    """
    isactive: bool = False
    transferred_to_mentor_id: Optional[UUID] = None


class MentorReactivateRequest(BaseModel):
    """
    Payload for reactivating a soft-deleted mentor account (EC-29).
    Sets is_active = True and clears deleted_at at the service layer.
    """
    isactive: bool = True