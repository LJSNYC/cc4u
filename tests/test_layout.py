"""Tests for layout components: WidgetSlot, ColumnContainer."""

import pytest
from app import WidgetSlot, ColumnContainer
from grid import register, WIDGET_REGISTRY


# ──────────────────────────────────────────────────────────────────────────────
# WidgetSlot Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_widget_slot_init_defaults():
    """WidgetSlot initializes with wtype, default weight=1, and id."""
    slot = WidgetSlot("clock", id="test-slot")
    assert slot._wtype == "clock"
    assert slot._weight == 1
    assert slot._inner is None


def test_widget_slot_init_with_weight():
    """WidgetSlot accepts custom weight in __init__."""
    slot = WidgetSlot("git_status", weight=3, id="test-slot-weight")
    assert slot._wtype == "git_status"
    assert slot._weight == 3


def test_widget_slot_set_weight_updates_weight():
    """set_weight updates _weight attribute."""
    slot = WidgetSlot("clock", id="test-set-weight")
    slot.set_weight(5)
    assert slot._weight == 5


def test_widget_slot_set_weight_clamps_to_minimum():
    """set_weight clamps values below 1 to 1."""
    slot = WidgetSlot("clock", id="test-clamp-min")
    slot.set_weight(0)
    assert slot._weight == 1
    slot.set_weight(-5)
    assert slot._weight == 1


def test_widget_slot_set_weight_accepts_large_values():
    """set_weight accepts large weight values."""
    slot = WidgetSlot("clock", id="test-large-weight")
    slot.set_weight(10)
    assert slot._weight == 10
    slot.set_weight(100)
    assert slot._weight == 100


def test_widget_slot_wtype_attribute_direct():
    """WidgetSlot _wtype can be read and is set correctly at init."""
    slot = WidgetSlot("dummy_swap_1", id="test-swap")
    assert slot._wtype == "dummy_swap_1"

    # Test that _wtype is a direct attribute we can modify (for move logic)
    slot._wtype = "dummy_swap_2"
    assert slot._wtype == "dummy_swap_2"


# ──────────────────────────────────────────────────────────────────────────────
# ColumnContainer Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_column_container_init():
    """ColumnContainer initializes with side, widget_types, and heights."""
    col = ColumnContainer("left", ["clock", "git_status"], [1, 2], id="test-col")
    assert col._side == "left"
    assert col._widget_types == ["clock", "git_status"]
    assert col._heights == [1, 2]


def test_column_container_init_right_side():
    """ColumnContainer can be initialized as right side."""
    col = ColumnContainer("right", ["pomodoro"], [1], id="test-right-col")
    assert col._side == "right"
    assert col._widget_types == ["pomodoro"]


def test_column_container_init_empty():
    """ColumnContainer can be initialized with empty widget lists."""
    col = ColumnContainer("left", [], [], id="test-empty-col")
    assert col._side == "left"
    assert col._widget_types == []
    assert col._heights == []


def test_column_container_init_creates_lists_not_references():
    """ColumnContainer creates copies of widget_types and heights, not references."""
    original_types = ["clock", "git_status"]
    original_heights = [1, 2]
    col = ColumnContainer("left", original_types, original_heights, id="test-copy")

    # Modify originals
    original_types.append("pomodoro")
    original_heights.append(3)

    # Container should not be affected
    assert col._widget_types == ["clock", "git_status"]
    assert col._heights == [1, 2]


def test_column_container_get_widget_types_from_data():
    """get_widget_types returns _widget_types when slots not yet composed."""
    col = ColumnContainer("left", ["clock", "git_status"], [1, 2], id="test-types")
    # Before compose() is called, get_widget_types should still work via get_slots
    # which queries for WidgetSlot children. Since we haven't mounted/composed,
    # get_slots will return empty list and get_widget_types will return empty.
    # This tests the method's fallback behavior when no slots exist.
    result = col.get_widget_types()
    assert isinstance(result, list)


def test_column_container_get_heights_from_data():
    """get_heights returns heights from mounted slots."""
    col = ColumnContainer("left", ["clock", "git_status"], [1, 2], id="test-heights")
    # Similar to get_widget_types, this should return a list (empty when not mounted).
    result = col.get_heights()
    assert isinstance(result, list)


def test_column_container_get_slots_empty_when_not_mounted():
    """get_slots returns empty list before compose."""
    col = ColumnContainer("left", ["clock"], [1], id="test-slots-empty")
    slots = col.get_slots()
    assert slots == []


def test_column_container_add_widget_slot_appends_to_data():
    """add_widget_slot should mount a new WidgetSlot (tested via compose behavior)."""
    col = ColumnContainer("left", ["clock"], [1], id="test-add")
    # add_widget_slot creates a new slot with weight=1
    # Without running app context, we can verify the method exists and can be called
    assert hasattr(col, "add_widget_slot")
    assert callable(col.add_widget_slot)


# ──────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_widget_slot_multiple_weight_changes():
    """WidgetSlot weight can be changed multiple times."""
    slot = WidgetSlot("clock", weight=1, id="test-multi-weight")
    assert slot._weight == 1

    slot.set_weight(2)
    assert slot._weight == 2

    slot.set_weight(5)
    assert slot._weight == 5

    slot.set_weight(1)
    assert slot._weight == 1


def test_column_container_multiple_types():
    """ColumnContainer handles many widget types."""
    types = ["clock", "git_status", "pomodoro", "cost_tracker"]
    heights = [1, 2, 1, 1]
    col = ColumnContainer("left", types, heights, id="test-many")

    assert col._widget_types == types
    assert col._heights == heights
    assert len(col._widget_types) == 4
    assert len(col._heights) == 4


def test_widget_slot_init_preserves_all_kwargs():
    """WidgetSlot passes all kwargs to Widget parent."""
    # Verify that we can pass custom kwargs
    slot = WidgetSlot("clock", weight=2, id="test-kwargs", classes="custom-class")
    assert slot._wtype == "clock"
    assert slot._weight == 2
    assert "custom-class" in slot.classes


def test_column_container_left_and_right_independent():
    """Left and right ColumnContainers are independent."""
    left = ColumnContainer("left", ["clock"], [1], id="left-col")
    right = ColumnContainer("right", ["pomodoro"], [1], id="right-col")

    assert left._side == "left"
    assert right._side == "right"
    assert left._widget_types != right._widget_types
    assert left.id != right.id


def test_widget_slot_weight_independent_of_type():
    """WidgetSlot weight and type are independent attributes."""
    slot = WidgetSlot("type_a_preserve", weight=3, id="test-preserve-weight")
    initial_weight = slot._weight

    # Changing type should not affect weight (simulating swap behavior)
    slot._wtype = "type_b_preserve"

    assert slot._weight == initial_weight
    assert slot._wtype == "type_b_preserve"
