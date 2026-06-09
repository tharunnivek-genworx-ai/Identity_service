import uuid

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ChatMessage(Base):
    __tablename__ = "chatmessages"

    messageid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    sessionid = Column(
        UUID(as_uuid=True),
        ForeignKey("chatsessions.sessionid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized
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

    # 'user' or 'assistant'
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)

    tokencount = Column(Integer, nullable=True)
    llmmodelused = Column(String(100), nullable=True)       # e.g. llama-3.3-70b; NULL for user messages
    contextwindowsnapshot = Column(Text, nullable=True)     # serialized context sent to LLM at this call

    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    isdeleted = Column(Boolean, nullable=False, default=False)  # soft delete

    session = relationship("ChatSession", back_populates="messages")
    trainee = relationship("Trainee", foreign_keys=[traineeid])
    node = relationship("TopicNode", foreign_keys=[nodeid])