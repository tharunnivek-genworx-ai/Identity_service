import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class Mentor(Base):
    __tablename__ = "mentors"

    mentor_id = Column(
        "mentorid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column("passwordhash", String(255), nullable=False)
    full_name = Column("fullname", String(150), nullable=False)
    designation = Column(String(100), nullable=False)

    department_id = Column(
        "departmentid",
        UUID(as_uuid=True),
        ForeignKey("departments.departmentid", ondelete="RESTRICT"),
        nullable=False,
    )

    employee_id = Column("employeeid", String(50), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    profile_picture_url = Column("profilepictureurl", Text, nullable=True)
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

    department = relationship("Department", back_populates="mentors")
    created_by_admin = relationship("ITAdmin", back_populates="mentors_created")

    # ADD THESE:
    owned_spaces = relationship(
        "ESpace", foreign_keys="ESpace.mentor_id", back_populates="mentor"
    )
    transferred_spaces = relationship(
        "ESpace",
        foreign_keys="ESpace.transferred_to_mentor_id",
        back_populates="transferred_to_mentor",
    )
    created_nodes = relationship(
        "TopicNode",
        foreign_keys="TopicNode.created_by",
        back_populates="created_by_mentor",
    )

    @property
    def department_name(self) -> str | None:
        return self.department.department_name if self.department else None

    @property
    def department_code(self) -> str | None:
        return self.department.department_code if self.department else None
