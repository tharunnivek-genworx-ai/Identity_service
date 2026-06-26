# C:\CapStone\Identity_service\src\api\data\models\postgres\quiz_models\quizzes.py
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column("quizid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    node_id = Column(
        "nodeid",
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized for fast queries
    space_id = Column(
        "spaceid",
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Metadata snapshot of the SM version used at generation time; nullable after discard
    study_material_version_id = Column(
        "studymaterialversionid",
        UUID(as_uuid=True),
        ForeignKey("studymaterialversions.versionid", ondelete="SET NULL"),
        nullable=True,
    )

    title = Column(String(300), nullable=False)
    # Actual count after mentor edits; kept in sync at app layer on soft-delete of questions
    total_questions = Column("totalquestions", Integer, nullable=False)
    # 'easy', 'medium', 'hard', 'mixed'
    difficulty = Column(String(20), nullable=False, default="mixed")

    qc_failed_permanently = Column(
        "qcfailedpermanently", Boolean, nullable=False, default=False
    )
    qc_result = Column("qcresult", JSONB, nullable=True)
    next_llm_retry_at = Column(
        "nextllmretryat", TIMESTAMP(timezone=True), nullable=True
    )

    is_published = Column("ispublished", Boolean, nullable=False, default=False)
    published_at = Column("publishedat", TIMESTAMP(timezone=True), nullable=True)

    # draft | active | archived | hidden — trainee lifecycle
    lifecycle_status = Column(
        "lifecyclestatus", String(20), nullable=False, default="draft"
    )
    superseded_at = Column("supersededat", TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(
        "createdby",
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
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

    node = relationship("TopicNode", foreign_keys=[node_id])
    space = relationship("ESpace", foreign_keys=[space_id])
    study_material_version = relationship(
        "StudyMaterialVersion", back_populates="quizzes"
    )
    created_by_mentor = relationship("Mentor", foreign_keys=[created_by])
    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")
