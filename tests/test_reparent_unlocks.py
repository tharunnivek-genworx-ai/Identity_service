from uuid import uuid4

from src.api.core.services.space_node_service.node_service import (
    should_clear_unlocks_for_reparent,
)


def test_parent_change_clears_moved_node_unlocks() -> None:
    assert should_clear_unlocks_for_reparent(uuid4(), uuid4())
    assert should_clear_unlocks_for_reparent(uuid4(), None)
    assert should_clear_unlocks_for_reparent(None, uuid4())


def test_same_parent_reorder_keeps_unlocks() -> None:
    parent_id = uuid4()
    assert not should_clear_unlocks_for_reparent(parent_id, parent_id)
    assert not should_clear_unlocks_for_reparent(None, None)
