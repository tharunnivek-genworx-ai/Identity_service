from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.api.utils.time import utc_now
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from src.api.data.clients.postgres.database import Base
import uuid

class Department(Base):
    __tablename__ = "departments"
 
    department_id = Column("departmentid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_name = Column("departmentname", String(150), nullable=False)
    department_code = Column("departmentcode", String(30), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column("isactive", Boolean, nullable=False, default=True)
 
    created_by = Column(
        "createdby",
        UUID(as_uuid=True),
        ForeignKey("itadmins.itadminid", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at = Column("createdat", TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    # FIX: added onupdate=utc_now
    updated_at = Column("updatedat", TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
 
    created_by_admin = relationship("ITAdmin", back_populates="departments")
    mentors = relationship("Mentor", back_populates="department")
    trainees = relationship("Trainee", back_populates="department")
    spaces = relationship("ESpace", back_populates="department")