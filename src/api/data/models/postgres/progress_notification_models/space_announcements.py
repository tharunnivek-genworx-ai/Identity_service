import uuid

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class SpaceAnnouncement(Base):
    __tablename__ = "spaceannouncements"

    announcementid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    mentorid = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )

    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)     # supports Markdown
    # 'space_published', 'tree_updated', 'general'
    eventtype = Column(String(50), nullable=False)

    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    # Soft delete / retract by mentor
    isactive = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_spaceannouncements_space_created", "spaceid", "createdat"),
    )

    space = relationship("ESpace", foreign_keys=[spaceid])
    mentor = relationship("Mentor", foreign_keys=[mentorid])