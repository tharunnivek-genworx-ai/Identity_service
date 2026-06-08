from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class Timestamped(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    createdat: datetime
    updatedat: datetime