import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now
 
class ITAdmin(Base):
    __tablename__ = "itadmins"
 
    itadminid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    passwordhash = Column(String(255), nullable=False)
    fullname = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    isactive = Column(Boolean, nullable=False, default=True)
 
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    # FIX: added onupdate=utc_now — without this, updatedat never changes on UPDATE
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    deletedat = Column(TIMESTAMP(timezone=True), nullable=True)
 
    departments = relationship("Department", back_populates="created_by_admin")
    mentors_created = relationship("Mentor", back_populates="created_by_admin")
    trainees_created = relationship("Trainee", back_populates="created_by_admin")