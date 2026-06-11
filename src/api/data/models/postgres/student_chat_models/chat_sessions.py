import uuid

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ChatSession(Base):
    __tablename__ = "chatsessions"

    sessionid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    traineeid = Column(
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )
    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Which published version's content is used as primary LLM context for this session
    studymaterialversionid = Column(
        UUID(as_uuid=True),
        ForeignKey("studymaterialversions.versionid", ondelete="RESTRICT"),
        nullable=False,
    )

    sessiontitle = Column(String(300), nullable=True)
    # 'active' or 'closed'
    status = Column(String(20), nullable=False, default="active")

    totalmessages = Column(Integer, nullable=False, default=0)
    # Approximate token count of context passed to LLM at last call
    contexttokencount = Column(Integer, nullable=True)

    startedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    lastmessageat = Column(TIMESTAMP(timezone=True), nullable=True)
    closedat = Column(TIMESTAMP(timezone=True), nullable=True)

    trainee = relationship("Trainee", foreign_keys=[traineeid])
    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    study_material_version = relationship("StudyMaterialVersion", foreign_keys=[studymaterialversionid])
    messages = relationship("ChatMessage", back_populates="session")