import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Text,
    Date,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class Trainee(Base):
    __tablename__ = "trainees"
 
    traineeid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    passwordhash = Column(String(255), nullable=False)
    fullname = Column(String(150), nullable=False)
 
    employeeid = Column(String(50), nullable=True, unique=True)
    departmentid = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.departmentid", ondelete="RESTRICT"),
        nullable=False,
    )
 
    dob = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True)
    profilepictureurl = Column(Text, nullable=True)
    joiningdate = Column(Date, nullable=True)
    isactive = Column(Boolean, nullable=False, default=True)
 
    createdby = Column(
        UUID(as_uuid=True),
        ForeignKey("itadmins.itadminid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    # FIX: added onupdate=utc_now
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    deletedat = Column(TIMESTAMP(timezone=True), nullable=True)
 
    department = relationship("Department", back_populates="trainees")
    created_by_admin = relationship("ITAdmin", back_populates="trainees_created")