import uuid

from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class NodeEventNotification(Base):
    __tablename__ = "nodeeventnotifications"

    notificationid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    # Enum values: study_material_published, study_material_regenerated, quiz_published,
    # quiz_regenerated, quiz_questions_edited, quiz_deleted, reference_material_added,
    # reference_material_updated, node_deleted, node_completion_reset
    eventtype = Column(String(60), nullable=False)

    triggeredby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )

    # Optional FK anchors for the specific resource that changed
    relatedversionid = Column(
        UUID(as_uuid=True),
        ForeignKey("studymaterialversions.versionid", ondelete="RESTRICT"),
        nullable=True,
    )
    relatedquizid = Column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.quizid", ondelete="RESTRICT"),
        nullable=True,
    )
    relatedmaterialid = Column(
        UUID(as_uuid=True),
        ForeignKey("referencematerials.materialid", ondelete="RESTRICT"),
        nullable=True,
    )

    systemmessage = Column(Text, nullable=False)        # auto-generated description
    mentorcustommessage = Column(Text, nullable=True)   # optional mentor-written note

    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_nodeeventnotifications_space_node_created", "spaceid", "nodeid", "createdat"),
    )

    space = relationship("ESpace", foreign_keys=[spaceid])
    node = relationship("TopicNode", foreign_keys=[nodeid])
    triggered_by_mentor = relationship("Mentor", foreign_keys=[triggeredby])
    related_version = relationship("StudyMaterialVersion", foreign_keys=[relatedversionid])
    related_quiz = relationship("Quiz", foreign_keys=[relatedquizid])
    related_material = relationship("ReferenceMaterial", foreign_keys=[relatedmaterialid])