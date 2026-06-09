from fastapi import HTTPException, status

# ─────────────────────────────────────────────
# DEPARTMENT EXCEPTIONS
# ─────────────────────────────────────────────

class DepartmentNotFoundException(HTTPException):
    """Raised when a department_id lookup returns no rows."""
    def __init__(self, department_id: str = ""):
        detail = (
            f"Department '{department_id}' not found."
            if department_id
            else "Department not found."
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DepartmentCodeAlreadyExistsException(HTTPException):
    """Raised on INSERT when departmentcode violates the UNIQUE constraint.
    departmentcode is a business key (e.g. 'FE', 'DEVOPS') — must be unique."""
    def __init__(self, code: str = ""):
        detail = (
            f"Department code '{code}' is already in use."
            if code
            else "Department code already exists."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class DepartmentNameAlreadyExistsException(HTTPException):
    """Raised when a duplicate department name is detected (app-layer check)."""
    def __init__(self, name: str = ""):
        detail = (
            f"A department named '{name}' already exists."
            if name
            else "Department name already exists."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class DepartmentHasActiveMembersException(HTTPException):
    """Raised when trying to deactivate a department that still has
    active mentors or trainees assigned to it. Per design doc, FK is RESTRICT."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot deactivate a department with active mentors or trainees.",
        )


