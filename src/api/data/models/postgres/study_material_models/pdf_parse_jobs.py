import uuid

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class PdfParseJob(Base):
    __tablename__ = "pdfparsejobs"

    jobid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    materialid = Column(
        UUID(as_uuid=True),
        ForeignKey("referencematerials.materialid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'pending' -> 'parsing' -> 'llm_cleaning' -> 'preview_ready' -> 'applied' | 'failed'
    status = Column(String(30), nullable=False)
    rawjson = Column(Text, nullable=True)  # raw output from LlamaParse
    cleanedskeleton = Column(Text, nullable=True)  # LLM-restructured heading tree
    errormessage = Column(Text, nullable=True)  # set on failure (EC-24)

    initiatedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    updatedat = Column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    space = relationship("ESpace", foreign_keys=[spaceid])
    material = relationship("ReferenceMaterial", foreign_keys=[materialid])
    initiated_by_mentor = relationship("Mentor", foreign_keys=[initiatedby])
    preview_nodes = relationship("PdfParseJobNode", back_populates="job")
