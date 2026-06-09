import uuid

from sqlalchemy import Column, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class TraineeSpaceProgress(Base):
    __tablename__ = "traineespaceprogress"

    spaceprogressid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    traineeid = Column(
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )
    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )

    # Recomputed whenever nodes are added/archived or study material published/unpublished (EC-23)
    # COUNT of active nodes with >= 1 published study material version at any depth
    totalnodes = Column(Integer, nullable=False, default=0)
    # COUNT of nodes where trainee's completionstatus = 'completed'
    completednodes = Column(Integer, nullable=False, default=0)
    # Average quizbestscore across all nodes the trainee has attempted
    overallscoreavg = Column(Float, nullable=True)

    lastactivityat = Column(TIMESTAMP(timezone=True), nullable=True)
    updatedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("traineeid", "spaceid", name="uq_traineespaceprogress_trainee_space"),
    )

    trainee = relationship("Trainee", foreign_keys=[traineeid])
    space = relationship("ESpace", foreign_keys=[spaceid])