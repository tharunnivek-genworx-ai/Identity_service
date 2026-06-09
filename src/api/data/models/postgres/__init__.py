# Central model registry — importing every model module here registers
# each SQLAlchemy model onto Base.metadata automatically.
#
# env.py only needs:  import src.api.data.models.postgres  (one line)
#
# IMPORTANT: When you add a new model file anywhere under this package,
# add its import here so Alembic autogenerate never silently skips it.

# ── Identity models ───────────────────────────────────────────────────────────
from src.api.data.models.postgres.Identity_models import (  # noqa: F401
    it_admin,
    mentors,
    revoked_token,
    trainees,
    departments,
)

# ── Spaces & topic tree ───────────────────────────────────────────────────────
from src.api.data.models.postgres.e_spaces_trees import (  # noqa: F401
    espaces,
    space_trainees,
    topic_nodes,
)

# ── Study material ────────────────────────────────────────────────────────────
from src.api.data.models.postgres.study_material_tables import (  # noqa: F401
    study_material_versions,
    reference_materials,
    node_media,
    pdf_parse_jobs,
    pdf_parse_job_nodes,
)

# ── Quizzes ───────────────────────────────────────────────────────────────────
from src.api.data.models.postgres.quiz_tables import (  # noqa: F401
    quizzes,
    quiz_questions,
    quiz_attempts,
    quiz_question_responses,
)

# ── Progress & notifications ──────────────────────────────────────────────────
from src.api.data.models.postgres.progress_notification_models import (  # noqa: F401
    trainee_space_progress,
    trainee_node_progress,
    node_event_notifications,
    trainee_notification_reads,
    space_announcements,
)

# ── Student chat ──────────────────────────────────────────────────────────────
from src.api.data.models.postgres.student_chat import (  # noqa: F401
    chat_sessions,
    chat_messages,
)
