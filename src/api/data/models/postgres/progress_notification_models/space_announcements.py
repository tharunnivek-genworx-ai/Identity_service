import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class SpaceAnnouncement(Base):
    __tablename__ = "spaceannouncements"

    announcement_id = Column(
        "announcementid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    space_id = Column(
        "spaceid",
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    mentor_id = Column(
        "mentorid",
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )

    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)  # supports Markdown
    # 'space_published', 'tree_updated', 'general'
    event_type = Column("eventtype", String(50), nullable=False)

    created_at = Column(
        "createdat", TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at = Column(
        "updatedat",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    # Soft delete / retract by mentor
    is_active = Column("isactive", Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_spaceannouncements_space_created", "spaceid", "createdat"),
    )

    space = relationship("ESpace", foreign_keys=[space_id])
    mentor = relationship("Mentor", foreign_keys=[mentor_id])
