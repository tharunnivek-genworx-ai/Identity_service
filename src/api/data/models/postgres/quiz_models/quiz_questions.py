# C:\CapStone\Identity_service\src\api\data\models\postgres\quiz_models\quiz_questions.py
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base


class QuizQuestion(Base):
    __tablename__ = "quizquestions"

    question_id = Column(
        "questionid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    quiz_id = Column(
        "quizid",
        UUID(as_uuid=True),
        ForeignKey("quizzes.quizid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized — avoids joining through quizzes to get the node
    node_id = Column(
        "nodeid",
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )

    question_text = Column("questiontext", Text, nullable=False)

    # Options A and B are always required; C and D are optional (3 or 4 option MCQ)
    option_a = Column("optiona", Text, nullable=False)
    option_b = Column("optionb", Text, nullable=False)
    option_c = Column("optionc", Text, nullable=True)
    option_d = Column("optiond", Text, nullable=True)

    # 'A', 'B', 'C', or 'D'
    correct_option = Column("correctoption", String(1), nullable=False)

    # Progressive hint system — all three hints are pre-generated at quiz creation time.
    # On each consecutive wrong attempt, the next hint level is revealed.
    # IMPORTANT: the correct answer is NEVER revealed automatically during a live attempt.
    #   hint1: subtle nudge (revealed on 1st wrong attempt, hint_level_reached=1)
    #   hint2: more explicit, narrows reasoning (2nd wrong, hint_level_reached=2)
    #   hint3: most explicit hint possible, but still does NOT reveal the answer (3rd wrong, hint_level_reached=3)
    hint1 = Column(Text, nullable=True)
    hint2 = Column(Text, nullable=True)
    hint3 = Column(Text, nullable=True)
    # explanation: post-submit review only — shown after attempt submission, never during a live attempt
    explanation = Column(Text, nullable=True)

    order_index = Column("orderindex", Integer, nullable=False)
    # Soft delete — historical attempts retain reference with '(Removed)' label (EC-10)
    is_active = Column("isactive", Boolean, nullable=False, default=True)
    # 'ai_generated' or 'mentor_manual'
    source = Column(String(20), nullable=False, default="ai_generated")

    quiz = relationship("Quiz", back_populates="questions")
    node = relationship("TopicNode", foreign_keys=[node_id])
    responses = relationship("QuizQuestionResponse", back_populates="question")
