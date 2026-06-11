import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class Trainee(Base):
    __tablename__ = "trainees"

    trainee_id = Column(
        "traineeid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column("passwordhash", String(255), nullable=False)
    full_name = Column("fullname", String(150), nullable=False)

    employee_id = Column("employeeid", String(50), nullable=True, unique=True)
    department_id = Column(
        "departmentid",
        UUID(as_uuid=True),
        ForeignKey("departments.departmentid", ondelete="RESTRICT"),
        nullable=False,
    )

    dob = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True)
    profile_picture_url = Column("profilepictureurl", Text, nullable=True)
    joining_date = Column("joiningdate", Date, nullable=True)
    is_active = Column("isactive", Boolean, nullable=False, default=True)

    created_by = Column(
        "createdby",
        UUID(as_uuid=True),
        ForeignKey("itadmins.itadminid", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at = Column(
        "createdat", TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    # FIX: added onupdate=utc_now
    updated_at = Column(
        "updatedat",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at = Column("deletedat", TIMESTAMP(timezone=True), nullable=True)

    department = relationship("Department", back_populates="trainees")
    created_by_admin = relationship("ITAdmin", back_populates="trainees_created")
    space_trainees = relationship("SpaceTrainee", back_populates="trainee")
