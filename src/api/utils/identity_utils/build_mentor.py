# C:\CapStone\Identity_service\src\api\utils\identity_utils\build_mentor.py
"""Build MentorOut without triggering async-incompatible lazy loads."""

from sqlalchemy.orm import attributes as orm_attributes

from src.api.data.models.postgres.Identity_models.mentors import Mentor
from src.api.schemas.identity_schemas.mentors_schema import MentorOut


def build_mentor_out(mentor: Mentor) -> MentorOut:
    """Serialize a mentor row. Department must be eager-loaded via selectinload."""
    dept_name: str | None = None
    dept_code: str | None = None
    state = orm_attributes.instance_state(mentor)
    if "department" not in state.unloaded:
        dept = mentor.department
        if dept is not None:
            dept_name = dept.department_name
            dept_code = dept.department_code

    out = MentorOut.model_validate(mentor)
    if dept_name is not None or dept_code is not None:
        return out.model_copy(
            update={"department_name": dept_name, "department_code": dept_code}
        )
    return out
