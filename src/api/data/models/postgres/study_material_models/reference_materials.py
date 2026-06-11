import uuid

from sqlalchemy import Column, String, Boolean, Text, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ReferenceMaterial(Base):
    __tablename__ = "referencematerials"

    materialid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    # NULL = space-level material; set = node-level material
    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=True,
    )

    title = Column(String(300), nullable=False)
    fileurl = Column(Text, nullable=False)          # GCS signed URL
    filename = Column(String(300), nullable=False)  # original filename
    filesizebytes = Column(BigInteger, nullable=True)
    mimetype = Column(String(100), nullable=False)  # e.g. application/pdf
    # 'space' or 'node'
    scope = Column(String(20), nullable=False)
    isvisibletotrainees = Column(Boolean, nullable=False, default=True)

    uploadedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    # Soft delete on replacement — old row preserved for audit; new row gets new materialid (EC-17)
    deletedat = Column(TIMESTAMP(timezone=True), nullable=True)

    space = relationship("ESpace", foreign_keys=[spaceid])
    node = relationship("TopicNode", foreign_keys=[nodeid])
    uploaded_by_mentor = relationship("Mentor", foreign_keys=[uploadedby])
    node_media = relationship("NodeMedia", back_populates="source_pdf_material")
    study_material_versions = relationship("StudyMaterialVersion", back_populates="reference_material")