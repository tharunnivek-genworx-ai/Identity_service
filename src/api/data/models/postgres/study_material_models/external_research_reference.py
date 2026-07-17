import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class ExternalResearchReference(Base):
    __tablename__ = "externalresearchreference"
    __table_args__ = (
        UniqueConstraint("nodeid", name="uq_externalresearchreference_node"),
    )

    externalresearchid = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
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
        index=True,
    )

    # 'success' | 'fail_soft'
    status = Column(String(20), nullable=False)
    failreason = Column(String(100), nullable=True)

    searchqueryused = Column(Text, nullable=True)
    resolvedtopic = Column(Text, nullable=True)
    resolvedsubtopic = Column(Text, nullable=True)

    # NULL when status='fail_soft'
    groundtruthreference = Column(Text, nullable=True)
    # Only URLs that survived into the final merge
    sourceurls = Column(JSONB, nullable=False, default=list)
    perwebsitesummarycount = Column(Integer, nullable=False, default=0)
    tokencount = Column(Integer, nullable=True)

    knowledgedistillationmodelused = Column(Text, nullable=True)

    requestedby = Column(
        UUID(as_uuid=True),
        ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
        nullable=False,
    )
    # Write-once cache row — no updatedat (no refresh path in MVP)
    createdat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)

    node = relationship("TopicNode", foreign_keys=[nodeid])
    space = relationship("ESpace", foreign_keys=[spaceid])
    requested_by_mentor = relationship("Mentor", foreign_keys=[requestedby])
