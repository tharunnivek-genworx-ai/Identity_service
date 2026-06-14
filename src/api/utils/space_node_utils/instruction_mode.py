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
        return text, None, branch
    if instruction_mode == "extend":
        return None, text, branch
    return None, None, branch


def detect_instruction_mode(
    *,
    node_specific_instruction: str | None,
    node_additive_instruction: str | None,
) -> InstructionMode:
    """Infer the mentor UI mode from stored node instruction columns."""
    if (node_specific_instruction or "").strip():
        return "replace"
    if (node_additive_instruction or "").strip():
        return "extend"
    return "inherit"
