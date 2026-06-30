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

# ── Generation checkpoints ────────────────────────────────────────────────────
from src.api.data.models.postgres.generation import (  # noqa: F401
    generation_runs,
)
from src.api.data.models.postgres.Identity_models import (  # noqa: F401
    departments,
    it_admin,
    mentors,
    revoked_token,
    trainees,
)

# ── Progress ──────────────────────────────────────────────────────────────────
from src.api.data.models.postgres.progress_notification_models import (  # noqa: F401
    trainee_node_progress,
    trainee_space_progress,
)

# ── Quizzes ───────────────────────────────────────────────────────────────────
from src.api.data.models.postgres.quiz_models import (  # noqa: F401
    quiz_attempts,
    quiz_question_responses,
    quiz_questions,
    quizzes,
)

# ── Study material ────────────────────────────────────────────────────────────
from src.api.data.models.postgres.study_material_models import (  # noqa: F401
    node_media,
    reference_llamaparse_images,
    reference_llamaparse_pdf,
    reference_materials,
    study_material_versions,
)
