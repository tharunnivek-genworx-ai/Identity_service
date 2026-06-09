import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class SpaceTrainee(Base):
    __tablename__ = "spacetrainees"

    spacetraineeid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    spaceid = Column(
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )
    traineeid = Column(
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'invite_code' or 'manual_add'
    joinedvia = Column(String(20), nullable=False)
    joinedat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)
    # EC-13, EC-15: soft-removal by mentor; read-only access retained after deactivation
    isactive = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("spaceid", "traineeid", name="uq_spacetrainees_space_trainee"),
    )

    space = relationship("ESpace", back_populates="space_trainees")
    trainee = relationship("Trainee", back_populates="space_trainees")