import uuid

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class TraineeNotificationRead(Base):
    __tablename__ = "traineenotificationreads"

    read_id = Column("readid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    trainee_id = Column(
        "traineeid",
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )

    # 'announcement' or 'node_event'
    notification_type = Column("notificationtype", String(20), nullable=False)

    # Polymorphic UUID — references either spaceannouncements.announcementid or
    # nodeeventnotifications.notificationid depending on notificationtype.
    # No FK constraint — enforced at app layer only (two possible target tables).
    notification_id = Column("notificationid", UUID(as_uuid=True), nullable=False)

    read_at = Column("readat", TIMESTAMP(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint(
            "traineeid", "notificationtype", "notificationid",
            name="uq_traineenotificationreads_trainee_type_notification"
        ),
        Index("ix_traineenotificationreads_trainee_type", "traineeid", "notificationtype"),
    )

    trainee = relationship("Trainee", foreign_keys=[trainee_id])