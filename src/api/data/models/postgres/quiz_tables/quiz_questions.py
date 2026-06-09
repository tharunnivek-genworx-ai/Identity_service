import uuid

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base


class QuizQuestion(Base):
    __tablename__ = "quizquestions"

    questionid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    quizid = Column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.quizid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized — avoids joining through quizzes to get the node
    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )

    questiontext = Column(Text, nullable=False)

    # Options A and B are always required; C and D are optional (3 or 4 option MCQ)
    optiona = Column(Text, nullable=False)
    optionb = Column(Text, nullable=False)
    optionc = Column(Text, nullable=True)
    optiond = Column(Text, nullable=True)

    # 'A', 'B', 'C', or 'D'
    correctoption = Column(String(1), nullable=False)

    # Progressive hint system: hint1 on 1st wrong, hint2 on 2nd, explanation revealed on 3rd (EC-7)
    hint1 = Column(Text, nullable=True)
    hint2 = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    orderindex = Column(Integer, nullable=False)
    # Soft delete — historical attempts retain reference with '(Removed)' label (EC-10)
    isactive = Column(Boolean, nullable=False, default=True)
    # 'ai_generated' or 'mentor_manual'
    source = Column(String(20), nullable=False, default="ai_generated")

    quiz = relationship("Quiz", back_populates="questions")
    node = relationship("TopicNode", foreign_keys=[nodeid])
    responses = relationship("QuizQuestionResponse", back_populates="question")