# C:\CapStone\Identity_service\src\api\data\models\postgres\study_material_models\study_material_versions.py
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class StudyMaterialVersion(Base):
    __tablename__ = "studymaterialversions"

    versionid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    # Auto-incremented per node at app layer; not a DB sequence
    versionnumber = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)  # full Markdown / rich-text content

    # 'generate', 'regenerate', 'improve', 'manual_edit'
    generationtype = Column(String(20), nullable=False)
    mentorfeedbackused = Column(
        Text, nullable=True
    )  # stored when generationtype = 'improve'

    # Immutable audit anchor — set at creation, never updated (EC-17)
    referencematerialid = Column(
        UUID(as_uuid=True),
        ForeignKey("referencematerials.materialid", ondelete="RESTRICT"),
        nullable=True,
    )
    # Self-referential lineage: points to parent version for 'improve' and 'manual_edit'
    basedonversionid = Column(
        UUID(as_uuid=True),
        ForeignKey("studymaterialversions.versionid", ondelete="RESTRICT"),
        nullable=True,
    )

    llmmodelused = Column(String(100), nullable=True)  # e.g. llama-3.3-70b
    promptsnapshot = Column(Text, nullable=True)  # full prompt for audit/debug
    tokenusage = Column(Integer, nullable=True)

    # Only one version per node has isactive = TRUE at a time (enforced at app layer)
    isactive = Column(Boolean, nullable=False, default=False)
    # Visible to trainees only when ispublished = TRUE
    ispublished = Column(Boolean, nullable=False, default=False)
    publishedat = Column(TIMESTAMP(timezone=True), nullable=True)

    publishedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=True,
    )
    createdby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    isarchived = Column(Boolean, nullable=False, default=False)
    archivedat = Column(TIMESTAMP(timezone=True), nullable=True)
    archivedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=True,
    )

    qcfailedpermanently = Column(
        Boolean, nullable=False, server_default="false", default=False
    )
    qcresult = Column(JSONB, nullable=True)

    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    reference_material = relationship(
        "ReferenceMaterial", back_populates="study_material_versions"
    )
    based_on_version = relationship(
        "StudyMaterialVersion",
        remote_side="StudyMaterialVersion.versionid",
        foreign_keys=[basedonversionid],
    )
    published_by_mentor = relationship("Mentor", foreign_keys=[publishedby])
    created_by_mentor = relationship("Mentor", foreign_keys=[createdby])
    quizzes = relationship("Quiz", back_populates="study_material_version")
