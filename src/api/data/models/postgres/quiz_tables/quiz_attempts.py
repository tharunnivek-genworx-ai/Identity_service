import uuid

from sqlalchemy import Column, String, Boolean, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class QuizAttempt(Base):
    __tablename__ = "quizattempts"

    attemptid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    quizid = Column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.quizid", ondelete="RESTRICT"),
        nullable=False,
    )
    traineeid = Column(
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'in_progress', 'submitted', 'abandoned'
    # in_progress enables mid-quiz resume (EC-7); same row reused on resume (EC-8)
    status = Column(String(20), nullable=False, default="in_progress")

    score = Column(Float, nullable=True)            # calculated on submit
    totalcorrect = Column(Integer, nullable=True)
    totalwithhints = Column(Integer, nullable=True) # correct answers that needed hints
    totalskipped = Column(Integer, nullable=True)

    startedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    submittedat = Column(TIMESTAMP(timezone=True), nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    trainee = relationship("Trainee", foreign_keys=[traineeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    node = relationship("TopicNode", foreign_keys=[nodeid])
    responses = relationship("QuizQuestionResponse", back_populates="attempt")