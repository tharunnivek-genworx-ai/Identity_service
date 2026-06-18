# C:\CapStone\Identity_service\src\api\data\models\postgres\study_material_models\reference_llamaparse_pdf.py
import uuid

from sqlalchemy import Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ReferenceLlamaParsePdf(Base):
    __tablename__ = "referencellamaparsepdf"
    __table_args__ = (
        UniqueConstraint(
            "referencematerialid",
            "nodeid",
            name="uq_referencellamaparsepdf_material_node",
        ),
    )

    llamaparsepdfid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    referencematerialid = Column(
        UUID(as_uuid=True),
        ForeignKey("referencematerials.materialid", ondelete="RESTRICT"),
        nullable=False,
    )
    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )

    # LlamaCloud extract job id (structured JSON extraction)
    llamaparsejobid = Column(String(200), nullable=False)
    # LlamaCloud parsing job id used when downloading figure binaries (nullable)
    llamaparseparsejobid = Column(String(200), nullable=True)
    # SHA-256 of source PDF bytes — reserved for cross-upload deduplication
    contenthash = Column(String(64), nullable=False, index=True)

    structuredjson = Column(JSONB, nullable=False)
    formattedtext = Column(Text, nullable=False)

    parsedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    updatedat = Column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    reference_material = relationship(
        "ReferenceMaterial", foreign_keys=[referencematerialid]
    )
    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    parsed_by_mentor = relationship("Mentor", foreign_keys=[parsedby])
    images = relationship(
        "ReferenceLlamaParseImage",
        back_populates="llamaparse_pdf",
        cascade="all, delete-orphan",
    )
