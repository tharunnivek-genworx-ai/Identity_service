# C:\CapStone\Identity_service\src\api\data\models\postgres\progress_notification_models\trainee_node_unlocks.py
import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class TraineeNodeUnlock(Base):
    """Durable unlock grant so parent progress resets do not re-lock children."""

    __tablename__ = "traineenodeunlocks"

    unlock_id = Column(
        "unlockid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    trainee_id = Column(
        "traineeid",
        UUID(as_uuid=True),
        ForeignKey("trainees.traineeid", ondelete="RESTRICT"),
        nullable=False,
    )
    node_id = Column(
        "nodeid",
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=False,
    )
    space_id = Column(
        "spaceid",
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )

    unlocked_at = Column(
        "unlockedat", TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    # e.g. parent_completed | backfill
    source = Column(String(40), nullable=False)
    # Parent learning unit that was completed when the grant was written (audit)
    gate_node_id = Column(
        "gatenodeid",
        UUID(as_uuid=True),
        ForeignKey("topicnodes.nodeid", ondelete="RESTRICT"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "traineeid", "nodeid", name="uq_traineenodeunlocks_trainee_node"
        ),
    )

    trainee = relationship("Trainee", foreign_keys=[trainee_id])
    node = relationship("TopicNode", foreign_keys=[node_id])
    space = relationship("ESpace", foreign_keys=[space_id])
    gate_node = relationship("TopicNode", foreign_keys=[gate_node_id])
