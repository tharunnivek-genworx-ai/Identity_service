import uuid

from sqlalchemy import Column, String, Boolean, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class TraineeNodeProgress(Base):
    __tablename__ = "traineenodeprogress"

    progressid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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
    # Denormalized
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )

    # TRUE as soon as trainee opens the study material page
    studymaterialviewed = Column(Boolean, nullable=False, default=False)
    firstviewedat = Column(TIMESTAMP(timezone=True), nullable=True)
    lastviewedat = Column(TIMESTAMP(timezone=True), nullable=True)

    # 0-100; updated by frontend scroll events
    studymaterialreadpercent = Column(Integer, nullable=False, default=0)
    # TRUE when readpercent = 100 (scroll-to-bottom confirmed) — earns 50% of node progress
    studymaterialcompleted = Column(Boolean, nullable=False, default=False)

    # MAX() across all submitted attempts (EC-9, EC-22)
    quizbestscore = Column(Float, nullable=True)
    quizattemptcount = Column(Integer, nullable=False, default=0)
    # Stays TRUE once achieved — never reverted by a later failed attempt (EC-22)
    # Reset to FALSE only when mentor adds a new quiz to a completed node (EC-20)
    quizpassed = Column(Boolean, nullable=False, default=False)

    # Phase 2B: incremented when trainee starts a chat session on this node
    chatsessioncount = Column(Integer, nullable=False, default=0)

    # 'not_started', 'in_progress', 'completed'
    # completed = studymaterialcompleted AND quizpassed both TRUE
    completionstatus = Column(String(20), nullable=False, default="not_started")

    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("traineeid", "nodeid", name="uq_traineenodeprogress_trainee_node"),
    )

    trainee = relationship("Trainee", foreign_keys=[traineeid])
    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])