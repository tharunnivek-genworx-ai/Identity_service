import uuid

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class QuizQuestionResponse(Base):
    __tablename__ = "quizquestionresponses"

    responseid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    attemptid = Column(
        UUID(as_uuid=True),
        ForeignKey("quizattempts.attemptid", ondelete="RESTRICT"),
        nullable=False,
    )
    questionid = Column(
        UUID(as_uuid=True),
        ForeignKey("quizquestions.questionid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized — avoids joining through attempts to get trainee
    traineeid = Column(
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # NULL when question was skipped
    selectedoption = Column(String(1), nullable=True)
    # NULL when skipped; not retroactively updated if answer key corrected (EC-12)
    iscorrect = Column(Boolean, nullable=True)

    # Number of times trainee attempted this specific question within the attempt
    attemptcount = Column(Integer, nullable=False, default=0)
    # 0 = no hint shown, 1 = hint1 shown, 2 = hint2 shown, 3 = answer + explanation revealed
    hintlevelreached = Column(Integer, nullable=False, default=0)

    wasskipped = Column(Boolean, nullable=False, default=False)
    # TRUE once answered correctly — question is locked from further changes
    waslocked = Column(Boolean, nullable=False, default=False)

    respondedat = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("attemptid", "questionid", name="uq_quizquestionresponses_attempt_question"),
    )

    attempt = relationship("QuizAttempt", back_populates="responses")
    question = relationship("QuizQuestion", back_populates="responses")
    trainee = relationship("Trainee", foreign_keys=[traineeid])