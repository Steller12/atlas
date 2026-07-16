import pytest

from atlas import __version__
from atlas.errors import AtlasError
from atlas.terraform.parser import (
    load_plan,
    normalize_actions,
    read_plan_json,
)

FIXTURES = "tests/fixtures"


def test_version():
    assert __version__ == "0.1.0"


# ── normalize_actions ──────────────────────────────────────────────────────


class TestNormalizeActions:
    def test_create(self):
        assert normalize_actions(["create"]) == "create"

    def test_update(self):
        assert normalize_actions(["update"]) == "update"

    def test_delete(self):
        assert normalize_actions(["delete"]) == "delete"

    def test_replace_delete_create(self):
        assert normalize_actions(["delete", "create"]) == "replace"

    def test_replace_create_delete(self):
        assert normalize_actions(["create", "delete"]) == "replace"

    def test_noop_returns_unknown(self):
        assert normalize_actions(["no-op"]) == "unknown"

    def test_read_returns_unknown(self):
        assert normalize_actions(["read"]) == "unknown"

    def test_empty_list_returns_unknown(self):
        assert normalize_actions([]) == "unknown"


# ── read_plan_json ─────────────────────────────────────────────────────────


class TestReadPlanJson:
    def test_reads_valid_plan(self):
        data = read_plan_json(f"{FIXTURES}/plan_small.json")
        assert "resource_changes" in data
        assert len(data["resource_changes"]) == 2

    def test_missing_file_raises_error(self):
        with pytest.raises(AtlasError, match="plan file not found"):
            read_plan_json(f"{FIXTURES}/nonexistent.json")

    def test_invalid_json_raises_error(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json}", encoding="utf-8")
        with pytest.raises(AtlasError, match="invalid JSON"):
            read_plan_json(str(bad_file))

    def test_missing_resource_changes_raises_error(self, tmp_path):
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}", encoding="utf-8")
        with pytest.raises(AtlasError, match="missing resource_changes"):
            read_plan_json(str(empty_file))


# ── load_plan ──────────────────────────────────────────────────────────────


class TestLoadPlan:
    def test_small_fixture_two_creates(self):
        changes = load_plan(f"{FIXTURES}/plan_small.json")
        assert len(changes) == 2
        assert all(c.action == "create" for c in changes)
        assert [c.address for c in changes] == [
            "null_resource.app",
            "random_pet.server",
        ]

    def test_update_fixture_two_replaces(self):
        changes = load_plan(f"{FIXTURES}/plan_update.json")
        assert len(changes) == 2
        assert all(c.action == "replace" for c in changes)
        assert [c.address for c in changes] == [
            "null_resource.app",
            "random_pet.server",
        ]

    def test_chain_fixture_filters_noop(self):
        """null_resource.app has actions=['no-op'] and should be skipped."""
        changes = load_plan(f"{FIXTURES}/plan_chain.json")
        assert len(changes) == 1
        assert changes[0].address == "random_pet.server"
        assert changes[0].action == "replace"

    def test_resource_change_fields_are_populated(self):
        changes = load_plan(f"{FIXTURES}/plan_small.json")
        change = changes[0]

        assert change.address == "null_resource.app"
        assert change.type == "null_resource"
        assert change.name == "app"
        assert change.actions == ("create",)
        assert change.action == "create"
        assert change.before is None
        assert change.after == {"triggers": {}}

    def test_before_and_after_on_replace_change(self):
        changes = load_plan(f"{FIXTURES}/plan_update.json")
        change = changes[0]  # null_resource.app — replaced

        assert change.action == "replace"
        assert change.before is not None
        assert change.after is not None
        assert change.before.get("id") == "5969991425366537142"
