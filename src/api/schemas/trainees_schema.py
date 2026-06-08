from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .common_schema import Timestamped


class TraineeBase(BaseModel):
    email: EmailStr
    fullname: str = Field(..., max_length=150)
    departmentid: UUID
    employeeid: Optional[str] = Field(None, max_length=50)
    dob: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=20)
    profilepictureurl: Optional[str] = None
    joiningdate: Optional[date] = None
    isactive: bool = True


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
    model_config = ConfigDict(from_attributes=True)

    traineeid: UUID
    createdby: UUID
    deletedat: Optional[datetime] = None


class TraineeDeactivateRequest(BaseModel):
    """
    Payload for PATCH /admin/trainees/:id/deactivate.
    Sets is_active = False and stamps deleted_at at the service layer (EC-28).
    """
    isactive: bool = False


class TraineeReactivateRequest(BaseModel):
    """
    Payload for PATCH /admin/trainees/:id/reactivate.
    Sets is_active = True and clears deleted_at at the service layer (EC-29).
    """
    isactive: bool = True