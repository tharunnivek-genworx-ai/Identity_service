import uuid

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ITAdmin(Base):
    __tablename__ = "itadmins"

    it_admin_id = Column(
        "itadminid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column("passwordhash", String(255), nullable=False)
    full_name = Column("fullname", String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column("isactive", Boolean, nullable=False, default=True)

    created_at = Column(
        "createdat", TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    # FIX: added onupdate=utc_now — without this, updatedat never changes on UPDATE
    updated_at = Column(
        "updatedat",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at = Column("deletedat", TIMESTAMP(timezone=True), nullable=True)

    departments = relationship("Department", back_populates="created_by_admin")
    mentors_created = relationship("Mentor", back_populates="created_by_admin")
    trainees_created = relationship("Trainee", back_populates="created_by_admin")
