from fastapi import HTTPException, status

# ─────────────────────────────────────────────
# TRAINEE EXCEPTIONS
# ─────────────────────────────────────────────

class TraineeNotFoundException(HTTPException):
    """Raised when a trainee_id lookup returns no rows."""
    def __init__(self, trainee_id: str = ""):
        detail = (
            f"Trainee '{trainee_id}' not found."
            if trainee_id
            else "Trainee not found."
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class TraineeEmailAlreadyExistsException(HTTPException):
    """Raised on INSERT when a trainee's email violates the UNIQUE constraint."""
    def __init__(self, email: str = ""):
        detail = (
            f"A trainee account with email '{email}' already exists."
            if email
            else "Trainee email already in use."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class TraineeEmployeeIdAlreadyExistsException(HTTPException):
    """Raised when employeeid is provided and already assigned to another trainee."""
    def __init__(self, employee_id: str = ""):
        detail = (
            f"Employee ID '{employee_id}' is already assigned to another trainee."
            if employee_id
            else "Employee ID already in use."
        )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class TraineeAlreadyDeactivatedException(HTTPException):
    """Raised when PATCH /deactivate is called on a trainee who is already inactive."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This trainee account is already deactivated.",
        )


class TraineeAlreadyActiveException(HTTPException):
    """Raised when PATCH /reactivate is called on a trainee who is already active."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This trainee account is already active.",
        )