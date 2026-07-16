import json
from dataclasses import dataclass
from pathlib import Path

from atlas.errors import AtlasError


@dataclass(frozen=True)
class ResourceChange:
    address: str
    type: str
    name: str
    actions: tuple[str, ...]   # raw actions, as a tuple (hashable + immutable)
    action: str                # normalized: create/update/delete/replace/unknown
    before: dict | None
    after: dict | None


_ACTION_MAP = {
    ("create",): "create",
    ("update",): "update",
    ("delete",): "delete",
    ("delete", "create"): "replace",
    ("create", "delete"): "replace",
}


def normalize_actions(actions: list[str]) -> str:
    return _ACTION_MAP.get(tuple(actions), "unknown")

def read_plan_json(path: str) -> dict:
    """Read and validate a terraform plan JSON file, return the parsed dict."""
    p = Path(path)
    if not p.exists():
        raise AtlasError(f"plan file not found: {path}")
    text = p.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise AtlasError(f"invalid JSON in {path}: {e}") from e
    if "resource_changes" not in data:
        raise AtlasError("not a terraform plan JSON: missing resource_changes")
    return data

def load_plan(path: str, data: dict | None = None) -> list[ResourceChange]:
    """Read a terraform plan JSON file and return the list of resource changes.

    If ``data`` is provided (pre-parsed JSON), it is used directly instead
    of reading + parsing the file a second time.
    """
    if data is None:
        data = read_plan_json(path)
    changes=[]
    for rc in data["resource_changes"]:
        change_block = rc.get("change")
        if not isinstance(change_block, dict) or "actions" not in change_block:
            raise AtlasError(
                f"malformed resource change at {rc.get('address', '?')}: "
                "missing 'change.actions' field"
            )
        actions = change_block["actions"]
        if actions==["no-op"]:
            continue
        change = ResourceChange(
            address=rc.get("address", ""),
            type=rc.get("type", ""),
            name=rc.get("name", ""),
            actions=tuple(actions),
            action=normalize_actions(actions),
            before=change_block.get("before"),
            after=change_block.get("after"),
        )
        changes.append(change) 
    return changes