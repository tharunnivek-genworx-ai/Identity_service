from types import SimpleNamespace
from uuid import uuid4

from src.api.utils.space_node_utils.build_node import _build_tree_for_trainee


def _node(*, node_id, parent_id, title, level, order_index):
    return SimpleNamespace(
        node_id=node_id,
        parent_id=parent_id,
        title=title,
        level=level,
        order_index=order_index,
        node_specific_instruction=None,
        tree_default_instruction=None,
        node_additive_instruction=None,
        is_active=True,
        auto_generated=False,
    )


def test_trainee_tree_exposes_prerequisite_metadata() -> None:
    parent_id = uuid4()
    child_id = uuid4()
    nodes = [
        _node(
            node_id=parent_id,
            parent_id=None,
            title="Basics",
            level=1,
            order_index=0,
        ),
        _node(
            node_id=child_id,
            parent_id=parent_id,
            title="Advanced",
            level=2,
            order_index=0,
        ),
    ]

    roots = _build_tree_for_trainee(
        nodes,
        nodes_with_published_material={parent_id, child_id},
        access_by_node={
            parent_id: "available",
            child_id: "prerequisite_locked",
        },
        blocked_by_node={child_id: parent_id},
    )

    child = roots[0].children[0]
    assert child.hasPublishedMaterial is True
    assert child.access_status == "prerequisite_locked"
    assert child.blocked_by_node_id == parent_id
    assert child.blocked_by_title == "Basics"
    assert child.unlock_message == "Finish Basics first"
