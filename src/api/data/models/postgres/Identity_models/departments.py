from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.api.utils.time import utc_now
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from src.api.data.clients.postgres.database import Base
import uuid

class Department(Base):
    __tablename__ = "departments"
 
    departmentid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    departmentname = Column(String(150), nullable=False)
    departmentcode = Column(String(30), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    isactive = Column(Boolean, nullable=False, default=True)
 
    createdby = Column(
        UUID(as_uuid=True),
        ForeignKey("itadmins.itadminid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    # FIX: added onupdate=utc_now
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
 
    created_by_admin = relationship("ITAdmin", back_populates="departments")
    mentors = relationship("Mentor", back_populates="department")
    trainees = relationship("Trainee", back_populates="department")
    spaces = relationship("ESpace", back_populates="department")