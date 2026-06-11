import uuid

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base


class PdfParseJobNode(Base):
    __tablename__ = "pdfparsejobnodes"

    previewnodeid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    jobid = Column(
        UUID(as_uuid=True),
        ForeignKey("pdfparsejobs.jobid", ondelete="RESTRICT"),
        nullable=False,
    )

    title = Column(String(300), nullable=False)     # heading extracted from PDF
    level = Column(Integer, nullable=False)          # depth level in heading hierarchy
    orderindex = Column(Integer, nullable=False)

    # 'pending', 'approved', 'renamed', 'skipped' — set by mentor during skeleton review (EC-25)
    mentoraction = Column(String(20), nullable=False, default="pending")

    # Set after mentor clicks Apply; links preview heading to the created topic node
    appliednodeid = Column(
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=True,
    )

    job = relationship("PdfParseJob", back_populates="preview_nodes")
    applied_node = relationship("TopicNode", foreign_keys=[appliednodeid])