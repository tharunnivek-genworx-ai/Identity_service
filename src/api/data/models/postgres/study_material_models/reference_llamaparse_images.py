# C:\CapStone\Identity_service\src\api\data\models\postgres\study_material_models\reference_llamaparse_images.py
import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base


class ReferenceLlamaParseImage(Base):
    __tablename__ = "referencellamaparseimages"

    llamaparseimageid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    llamaparsepdfid = Column(
        UUID(as_uuid=True),
        ForeignKey("referencellamaparsepdf.llamaparsepdfid", ondelete="CASCADE"),
        nullable=False,
    )
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

    title = Column(String(300), nullable=True)
    filename = Column(String(300), nullable=False)
    fileurl = Column(Text, nullable=False)

    sourcepagenumber = Column(Integer, nullable=True)
    figureindexonpage = Column(Integer, nullable=True)
    parseindex = Column(Integer, nullable=True)
    category = Column(String(50), nullable=True)
    orderindex = Column(Integer, nullable=False, default=0)

    llamaparse_pdf = relationship(
        "ReferenceLlamaParsePdf",
        back_populates="images",
        foreign_keys=[llamaparsepdfid],
    )
    reference_material = relationship(
        "ReferenceMaterial", foreign_keys=[referencematerialid]
    )
    node = relationship("TopicNode", foreign_keys=[nodeid])
