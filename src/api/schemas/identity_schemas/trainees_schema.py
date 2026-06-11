from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .common_schema import Timestamped


class TraineeBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    full_name: str = Field(..., max_length=150, alias="fullname")
    department_id: UUID = Field(..., alias="departmentid")
    employee_id: Optional[str] = Field(None, max_length=50, alias="employeeid")
    dob: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=20)
    profile_picture_url: Optional[str] = Field(None, alias="profilepictureurl")
    joining_date: Optional[date] = Field(None, alias="joiningdate")
    is_active: bool = Field(True, alias="isactive")


class TraineeCreate(TraineeBase):
    """
    Password accepted as plain text; hashed in the service layer before DB write.
    Never expose passwordhash in any Out schema.
    """
    password: str


class TraineeOut(TraineeBase, Timestamped):
    """
    Response schema for trainee data. passwordhash intentionally excluded.
    deletedat included so admin UI can display soft-deleted state.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    trainee_id: UUID = Field(..., alias="traineeid")
    created_by: UUID = Field(..., alias="createdby")
    deleted_at: Optional[datetime] = Field(None, alias="deletedat")


class TraineeDeactivateRequest(BaseModel):
    """
    Payload for PATCH /admin/trainees/:id/deactivate.
    Sets is_active = False and stamps deleted_at at the service layer (EC-28).
    """
    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(False, alias="isactive")


class TraineeReactivateRequest(BaseModel):
    """
    Payload for PATCH /admin/trainees/:id/reactivate.
    Sets is_active = True and clears deleted_at at the service layer (EC-29).
    """
    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(True, alias="isactive")