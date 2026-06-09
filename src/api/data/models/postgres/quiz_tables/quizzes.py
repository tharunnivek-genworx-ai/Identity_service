import uuid

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class Quiz(Base):
    __tablename__ = "quizzes"

    quizid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized for fast queries
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Source version used to generate this quiz — immutable after creation
    studymaterialversionid = Column(
        UUID(as_uuid=True),
        ForeignKey("studymaterialversions.versionid", ondelete="RESTRICT"),
        nullable=False,
    )

    title = Column(String(300), nullable=False)
    # Actual count after mentor edits; kept in sync at app layer on soft-delete of questions
    totalquestions = Column(Integer, nullable=False)
    # 'easy', 'medium', 'hard', 'mixed'
    difficulty = Column(String(20), nullable=False, default="mixed")

    ispublished = Column(Boolean, nullable=False, default=False)
    publishedat = Column(TIMESTAMP(timezone=True), nullable=True)

    createdby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    study_material_version = relationship("StudyMaterialVersion", back_populates="quizzes")
    created_by_mentor = relationship("Mentor", foreign_keys=[createdby])
    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")