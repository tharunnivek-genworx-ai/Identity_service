import uuid

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class NodeEventNotification(Base):
    __tablename__ = "nodeeventnotifications"

    notification_id = Column(
        "notificationid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

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

    # Enum values: study_material_published, study_material_regenerated, quiz_published,
    # quiz_regenerated, quiz_questions_edited, quiz_deleted, reference_material_added,
    # reference_material_updated, node_deleted, node_completion_reset
    event_type = Column("eventtype", String(60), nullable=False)

    triggered_by = Column(
        "triggeredby",
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )

    # Optional FK anchors for the specific resource that changed
    related_version_id = Column(
        "relatedversionid",
        UUID(as_uuid=True),
        ForeignKey("studymaterialversions.versionid", ondelete="RESTRICT"),
        nullable=True,
    )
    related_quiz_id = Column(
        "relatedquizid",
        UUID(as_uuid=True),
        ForeignKey("quizzes.quizid", ondelete="RESTRICT"),
        nullable=True,
    )
    related_material_id = Column(
        "relatedmaterialid",
        UUID(as_uuid=True),
        ForeignKey("referencematerials.materialid", ondelete="RESTRICT"),
        nullable=True,
    )

    system_message = Column(
        "systemmessage", Text, nullable=False
    )  # auto-generated description
    mentor_custom_message = Column(
        "mentorcustommessage", Text, nullable=True
    )  # optional mentor-written note

    created_at = Column(
        "createdat", TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )

    __table_args__ = (
        Index(
            "ix_nodeeventnotifications_space_node_created",
            "spaceid",
            "nodeid",
            "createdat",
        ),
    )

    space = relationship("ESpace", foreign_keys=[space_id])
    node = relationship("TopicNode", foreign_keys=[node_id])
    triggered_by_mentor = relationship("Mentor", foreign_keys=[triggered_by])
    related_version = relationship(
        "StudyMaterialVersion", foreign_keys=[related_version_id]
    )
    related_quiz = relationship("Quiz", foreign_keys=[related_quiz_id])
    related_material = relationship(
        "ReferenceMaterial", foreign_keys=[related_material_id]
    )
