# Central model registry — importing every model module here registers
# each SQLAlchemy model onto Base.metadata automatically.
#
# env.py only needs:  import src.api.data.models.postgres  (one line)
#
# IMPORTANT: When you add a new model file anywhere under this package,
# add its import here so Alembic autogenerate never silently skips it.

# ── Identity models ───────────────────────────────────────────────────────────
# ── Spaces & topic tree ───────────────────────────────────────────────────────
from src.api.data.models.postgres.e_spaces_trees import (  # noqa: F401
    espaces,
    space_trainees,
    topic_nodes,
)
from src.api.data.models.postgres.Identity_models import (  # noqa: F401
    departments,
    it_admin,
    mentors,
    revoked_token,
    trainees,
)

# ── Progress & notifications ──────────────────────────────────────────────────
from src.api.data.models.postgres.progress_notification_models import (  # noqa: F401
    node_event_notifications,
    space_announcements,
    trainee_node_progress,
    trainee_notification_reads,
    trainee_space_progress,
)

# ── Quizzes ───────────────────────────────────────────────────────────────────
from src.api.data.models.postgres.quiz_models import (  # noqa: F401
    quiz_attempts,
    quiz_question_responses,
    quiz_questions,
    quizzes,
)

# ── Student chat ──────────────────────────────────────────────────────────────
from src.api.data.models.postgres.student_chat_models import (  # noqa: F401
    chat_messages,
    chat_sessions,
)

# ── Study material ────────────────────────────────────────────────────────────
from src.api.data.models.postgres.study_material_models import (  # noqa: F401
    node_media,
    pdf_parse_job_nodes,
    pdf_parse_jobs,
    reference_materials,
    study_material_versions,
)
