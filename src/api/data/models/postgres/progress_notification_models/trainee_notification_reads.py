import uuid

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class TraineeNotificationRead(Base):
    __tablename__ = "traineenotificationreads"

    readid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    traineeid = Column(
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'announcement' or 'node_event'
    notificationtype = Column(String(20), nullable=False)

    # Polymorphic UUID — references either spaceannouncements.announcementid or
    # nodeeventnotifications.notificationid depending on notificationtype.
    # No FK constraint — enforced at app layer only (two possible target tables).
    notificationid = Column(UUID(as_uuid=True), nullable=False)

    readat = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint(
            "traineeid", "notificationtype", "notificationid",
            name="uq_traineenotificationreads_trainee_type_notification"
        ),
        Index("ix_traineenotificationreads_trainee_type", "traineeid", "notificationtype"),
    )

    trainee = relationship("Trainee", foreign_keys=[traineeid])