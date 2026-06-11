from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class Timestamped(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    created_at: datetime = Field(..., alias="createdat")
    updated_at: datetime = Field(..., alias="updatedat")