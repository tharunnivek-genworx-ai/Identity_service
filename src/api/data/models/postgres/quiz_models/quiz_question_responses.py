import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base


class QuizQuestionResponse(Base):
    __tablename__ = "quizquestionresponses"

    response_id = Column(
        "responseid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    attempt_id = Column(
        "attemptid",
        UUID(as_uuid=True),
        ForeignKey("quizattempts.attemptid", ondelete="RESTRICT"),
        nullable=False,
    )
    question_id = Column(
        "questionid",
        UUID(as_uuid=True),
        ForeignKey("quizquestions.questionid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized — avoids joining through attempts to get trainee
    trainee_id = Column(
        "traineeid",
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # NULL when question was skipped
    selected_option = Column("selectedoption", String(1), nullable=True)
    # NULL when skipped; not retroactively updated if answer key corrected (EC-12)
    is_correct = Column("iscorrect", Boolean, nullable=True)

    # Number of times trainee attempted this specific question within the attempt
    attempt_count = Column("attemptcount", Integer, nullable=False, default=0)
    # 0 = no hint shown, 1 = hint1 shown, 2 = hint2 shown, 3 = answer + explanation revealed
    hint_level_reached = Column("hintlevelreached", Integer, nullable=False, default=0)

    was_skipped = Column("wasskipped", Boolean, nullable=False, default=False)
    # TRUE once answered correctly — question is locked from further changes
    was_locked = Column("waslocked", Boolean, nullable=False, default=False)

    responded_at = Column("respondedat", TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "attemptid", "questionid", name="uq_quizquestionresponses_attempt_question"
        ),
    )

    attempt = relationship("QuizAttempt", back_populates="responses")
    question = relationship("QuizQuestion", back_populates="responses")
    trainee = relationship("Trainee", foreign_keys=[trainee_id])
