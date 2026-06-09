import uuid

from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ESpace(Base):
    __tablename__ = "espaces"

    spaceid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spacename = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    departmentid = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.departmentid", ondelete="RESTRICT"),
        nullable=False,
    )
    mentorid = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    # EC-27: set by ITAdmin when original mentor is deactivated
    # App layer resolves effective owner as: COALESCE(transferredtomentorid, mentorid)
    transferredtomentorid = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=True,
    )

    defaultteachinginstruction = Column(Text, nullable=True)
    invitecode = Column(String(20), nullable=True, unique=True)
    ispublished = Column(Boolean, nullable=False, default=False)
    isactive = Column(Boolean, nullable=False, default=True)

    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    archivedat = Column(TIMESTAMP(timezone=True), nullable=True)

    department = relationship("Department", back_populates="spaces")
    mentor = relationship("Mentor", foreign_keys=[mentorid], back_populates="owned_spaces")
    transferred_to_mentor = relationship("Mentor", foreign_keys=[transferredtomentorid], back_populates="transferred_spaces")
    space_trainees = relationship("SpaceTrainee", back_populates="space")
    topic_nodes = relationship("TopicNode", back_populates="space")