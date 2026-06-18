# C:\CapStone\Identity_service\src\api\data\models\postgres\progress_notification_models\trainee_node_progress.py
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from src.api.data.clients.postgres.database import Base
from src.api.utils.time import utc_now


class TraineeNodeProgress(Base):
    __tablename__ = "traineenodeprogress"

    progress_id = Column(
        "progressid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
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
    # Denormalized
    space_id = Column(
        "spaceid",
        UUID(as_uuid=True),
        ForeignKey("espaces.spaceid", ondelete="RESTRICT"),
        nullable=False,
    )

    # TRUE as soon as trainee opens the study material page
    study_material_viewed = Column(
        "studymaterialviewed", Boolean, nullable=False, default=False
    )
    first_viewed_at = Column("firstviewedat", TIMESTAMP(timezone=True), nullable=True)
    last_viewed_at = Column("lastviewedat", TIMESTAMP(timezone=True), nullable=True)

    # 0-100; updated by frontend scroll events
    study_material_read_percent = Column(
        "studymaterialreadpercent", Integer, nullable=False, default=0
    )
    # TRUE when readpercent = 100 (scroll-to-bottom confirmed) — earns 50% of node progress
    study_material_completed = Column(
        "studymaterialcompleted", Boolean, nullable=False, default=False
    )

    # MAX() across all submitted attempts (EC-9, EC-22)
    quiz_best_score = Column("quizbestscore", Float, nullable=True)
    quiz_attempt_count = Column("quizattemptcount", Integer, nullable=False, default=0)
    # Stays TRUE once achieved — never reverted by a later failed attempt (EC-22)
    # Reset to FALSE only when mentor adds a new quiz to a completed node (EC-20)
    quiz_passed = Column("quizpassed", Boolean, nullable=False, default=False)

    # Phase 2B: incremented when trainee starts a chat session on this node
    chat_session_count = Column("chatsessioncount", Integer, nullable=False, default=0)

    # 'not_started', 'in_progress', 'completed'
    # completed = studymaterialcompleted AND quizpassed both TRUE
    completion_status = Column(
        "completionstatus", String(20), nullable=False, default="not_started"
    )

    updated_at = Column(
        "updatedat",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "traineeid", "nodeid", name="uq_traineenodeprogress_trainee_node"
        ),
    )

    trainee = relationship("Trainee", foreign_keys=[trainee_id])
    node = relationship("TopicNode", foreign_keys=[node_id])
    space = relationship("ESpace", foreign_keys=[space_id])
