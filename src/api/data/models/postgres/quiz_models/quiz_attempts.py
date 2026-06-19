# C:\CapStone\Identity_service\src\api\data\models\postgres\quiz_models\quiz_attempts.py
import uuid

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class QuizAttempt(Base):
    __tablename__ = "quizattempts"

    attempt_id = Column(
        "attemptid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    quiz_id = Column(
        "quizid",
        UUID(as_uuid=True),
        ForeignKey("quizzes.quizid", ondelete="RESTRICT"),
        nullable=False,
    )
    trainee_id = Column(
        "traineeid",
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized
    space_id = Column(
        "spaceid",
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    node_id = Column(
        "nodeid",
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'in_progress', 'submitted', 'abandoned'
    # in_progress enables mid-quiz resume (EC-7); same row reused on resume (EC-8)
    status = Column(String(20), nullable=False, default="in_progress")

    score = Column(Float, nullable=True)  # calculated on submit
    total_correct = Column("totalcorrect", Integer, nullable=True)
    total_with_hints = Column(
        "totalwithhints", Integer, nullable=True
    )  # correct answers that needed hints
    total_skipped = Column("totalskipped", Integer, nullable=True)

    started_at = Column(
        "startedat", TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    submitted_at = Column("submittedat", TIMESTAMP(timezone=True), nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    trainee = relationship("Trainee", foreign_keys=[trainee_id])
    space = relationship("ESpace", foreign_keys=[space_id])
    node = relationship("TopicNode", foreign_keys=[node_id])
    responses = relationship("QuizQuestionResponse", back_populates="attempt")
