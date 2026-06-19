# C:\CapStone\Identity_service\src\api\utils\invite_code.py
import secrets
import string

_INVITE_CODE_ALPHABET = string.ascii_uppercase + string.digits
_INVITE_CODE_LENGTH = 20
_INVITE_CODE_MAX_ATTEMPTS = 10


def _generate_invite_code() -> str:
    return "".join(
        secrets.choice(_INVITE_CODE_ALPHABET) for _ in range(_INVITE_CODE_LENGTH)
    )
