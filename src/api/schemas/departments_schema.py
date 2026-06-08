from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .common_schema import Timestamped


class DepartmentBase(BaseModel):
    departmentname: str = Field(..., max_length=150)
    departmentcode: str = Field(..., max_length=30)
    description: Optional[str] = None
    isactive: bool = True


class DepartmentCreate(DepartmentBase):
    # createdby is taken from the JWT (itadmin id), never from the request body.
    pass


class DepartmentUpdate(BaseModel):
    """
    All fields optional — caller sends only what changed.
    departmentcode is intentionally NOT updatable (it is a business key
    used by other services for reference; changing it would break FK semantics).
    """
    departmentname: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    isactive: Optional[bool] = None


class DepartmentOut(DepartmentBase, Timestamped):
    """
    Full department response. Inherits Timestamped for createdat/updatedat.
    model_config declared explicitly for clarity (from_attributes allows
    SQLAlchemy ORM objects to be passed directly to this schema).
    """
    model_config = ConfigDict(from_attributes=True)

    departmentid: UUID
    createdby: UUID