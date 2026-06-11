from fastapi import HTTPException, status

# ─────────────────────────────────────────────
# MENTOR EXCEPTIONS
# ─────────────────────────────────────────────


class MentorNotFoundException(HTTPException):
    """Raised when a mentor_id lookup returns no rows."""

    def __init__(self, mentor_id: str = ""):
        detail = (
            f"Mentor '{mentor_id}' not found." if mentor_id else "Mentor not found."
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class MentorEmailAlreadyExistsException(HTTPException):
    """Raised on INSERT when a mentor's email violates the UNIQUE constraint."""

    def __init__(self, email: str = ""):
        detail = (
            f"A mentor account with email '{email}' already exists."
            if email
            else "Mentor email already in use."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class MentorEmployeeIdAlreadyExistsException(HTTPException):
    """Raised when employeeid is provided and already assigned to another mentor."""

    def __init__(self, employee_id: str = ""):
        detail = (
            f"Employee ID '{employee_id}' is already assigned to another mentor."
            if employee_id
            else "Employee ID already in use."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class MentorAlreadyDeactivatedException(HTTPException):
    """Raised when PATCH /deactivate is called on a mentor who is already inactive."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This mentor account is already deactivated.",
        )


class MentorAlreadyActiveException(HTTPException):
    """Raised when PATCH /reactivate is called on a mentor who is already active."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This mentor account is already active.",
        )


class TransferTargetNotFoundException(HTTPException):
    """Raised when the transferred_to_mentor_id provided during mentor deactivation
    does not match any active mentor. Per EC-27 — transfer target must be active."""

    def __init__(self, mentor_id: str = ""):
        detail = (
            f"Transfer target mentor '{mentor_id}' not found or is not active."
            if mentor_id
            else "Transfer target mentor not found or is not active."
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
