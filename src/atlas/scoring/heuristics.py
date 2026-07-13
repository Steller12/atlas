from dataclasses import dataclass

from atlas.graph.impact import downstream
from atlas.terraform.parser import ResourceChange

# How dangerous is the action itself? (given — argue with me if you disagree)
_ACTION_SEVERITY = {
    "delete": 5,
    "replace": 4,
    "unknown": 3,   # can't classify it → treat with suspicion
    "update": 2,
    "create": 1,
}

# Substrings that suggest a resource HOLDS DATA (losing it = unrecoverable).
_STATEFUL_HINTS = (
    "database", "db_", "rds", "sql", "dynamodb", "elasticache",
    "storage", "bucket", "volume", "disk", "efs", "kafka", "queue",
)


@dataclass(frozen=True)
class ResourceRisk:
    address: str
    score: int                 # 0–10
    level: str                 # "low" | "medium" | "high"
    reasons: tuple[str, ...]   # why — one sentence per contribution


def is_stateful(resource_type: str) -> bool:
    """True if the type string smells like it holds data."""
    resource_type_lower = resource_type.lower()
    return any(hint in resource_type_lower for hint in _STATEFUL_HINTS)


def level_for(score: int) -> str:
    """0–3 low, 4–6 medium, 7–10 high."""
    if score <= 3:
        return "low"
    if score <= 6:
        return "medium"
    return "high"


def score_change(change: ResourceChange, impacted_count: int) -> ResourceRisk:
    base = _ACTION_SEVERITY[change.action]
    blast = min(impacted_count, 3)
    state = 2 if is_stateful(change.type) else 0
    score = min(base + blast + state, 10)

    reasons = [f"action is {change.action} (+{base})"]
    if blast:
        reasons.append(f"{impacted_count} downstream resources impacted (+{blast})")
    if state:
        reasons.append("stateful resource type (+2)")

    return ResourceRisk(change.address, score, level_for(score), tuple(reasons))


def score_plan(
    changes: list[ResourceChange], graph: dict[str, set[str]]
) -> list[ResourceRisk]:
    risks = []
    for change in changes:
        impacted = downstream({change.address}, graph)
        risks.append(score_change(change, len(impacted)))
    return sorted(risks, key=lambda risk: risk.score, reverse=True)
