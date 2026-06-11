from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .common_schema import Timestamped


class MentorBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    full_name: str = Field(..., max_length=150, alias="fullname")
    designation: str = Field(..., max_length=100)
    department_id: UUID = Field(..., alias="departmentid")
    employee_id: str | None = Field(None, max_length=50, alias="employeeid")
    phone: str | None = Field(None, max_length=20)
    profile_picture_url: str | None = Field(None, alias="profilepictureurl")
    is_active: bool = Field(True, alias="isactive")


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    mentor_id: UUID = Field(..., alias="mentorid")
    created_by: UUID = Field(..., alias="createdby")
    deleted_at: datetime | None = Field(None, alias="deletedat")
    department_name: str | None = None
    department_code: str | None = None


class MentorDeactivateRequest(BaseModel):
    """
    Payload for PATCH /admin/mentors/:id/deactivate.

    transferred_to_mentor_id: Optional UUID of the active mentor to transfer
    the deactivated mentor's spaces to. Maps to e_spaces.transferred_to_mentor_id
    in the Space service. Per design doc EC-27 and Section 3.2.6.
    If omitted, spaces remain under the original mentor_id (accessible to trainees
    but effectively owner-less until transferred).
    """

    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(False, alias="isactive")
    transferred_to_mentor_id: UUID | None = None


class MentorReactivateRequest(BaseModel):
    """
    Payload for reactivating a soft-deleted mentor account (EC-29).
    Sets is_active = True and clears deleted_at at the service layer.
    """

    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(True, alias="isactive")
