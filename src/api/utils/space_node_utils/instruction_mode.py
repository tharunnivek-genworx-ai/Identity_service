# C:\CapStone\Identity_service\src\api\utils\space_node_utils\instruction_mode.py
"""Map mentor-facing instruction modes to the three DB instruction columns."""

from typing import Literal

InstructionMode = Literal["inherit", "extend", "replace"]


def resolve_instruction_fields_from_mode(
    *,
    instruction_mode: InstructionMode,
    instruction_text: str | None,
    branch_default_instruction: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Return (node_specific, node_additive, tree_default) for persistence."""
    text = (instruction_text or "").strip() or None
    branch = (branch_default_instruction or "").strip() or None

    if instruction_mode == "replace":
        stripped = (instruction_text or "").strip()
        # Persist "" so empty replace overrides are distinguishable from inherit (null).
        return stripped if stripped else "", None, branch
    if instruction_mode == "extend":
        return None, text, branch
    return None, None, branch
