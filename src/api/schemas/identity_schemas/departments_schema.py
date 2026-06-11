from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .common_schema import Timestamped


class DepartmentBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    department_name: str = Field(..., max_length=150, alias="departmentname")
    department_code: str = Field(..., max_length=30, alias="departmentcode")
    description: Optional[str] = None
    is_active: bool = Field(True, alias="isactive")


class DepartmentCreate(DepartmentBase):
    # createdby is taken from the JWT (itadmin id), never from the request body.
    pass


class DepartmentUpdate(BaseModel):
    """
    All fields optional — caller sends only what changed.
    departmentcode is intentionally NOT updatable (it is a business key
    used by other services for reference; changing it would break FK semantics).
    """
    model_config = ConfigDict(populate_by_name=True)

    department_name: Optional[str] = Field(None, max_length=150, alias="departmentname")
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isactive")


class DepartmentOut(DepartmentBase, Timestamped):
    """
    Full department response. Inherits Timestamped for created_at/updated_at.
    model_config declared explicitly for clarity (from_attributes allows
    SQLAlchemy ORM objects to be passed directly to this schema).
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    department_id: UUID = Field(..., alias="departmentid")
    created_by: UUID = Field(..., alias="createdby")