import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base


class NodeMedia(Base):
    __tablename__ = "nodemedia"

    mediaid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized for fast queries without joining through topicnodes
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'image', 'video_url', 'article_link'
    mediatype = Column(String(20), nullable=False)
    title = Column(String(300), nullable=True)
    url = Column(Text, nullable=True)  # for video_url and article_link types
    fileurl = Column(Text, nullable=True)  # GCS URL for image type

    orderindex = Column(Integer, nullable=False, default=0)

    uploadedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )

    # Phase 2A: populated by LlamaParse image extraction pipeline
    sourcepdfmaterialid = Column(
        UUID(as_uuid=True),
        ForeignKey("referencematerials.materialid", ondelete="RESTRICT"),
        nullable=True,
    )
    sourcepagenumber = Column(Integer, nullable=True)

    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    uploaded_by_mentor = relationship("Mentor", foreign_keys=[uploadedby])
    source_pdf_material = relationship("ReferenceMaterial", back_populates="node_media")
