from atlas.graph.impact import build_graph
from atlas.scoring.heuristics import is_stateful, level_for, score_change, score_plan
from atlas.terraform.parser import ResourceChange, load_plan, read_plan_json

FIXTURES = "tests/fixtures"


def make_change(
    action: str = "update",
    resource_type: str = "null_resource",
    address: str = "null_resource.app",
) -> ResourceChange:
    return ResourceChange(
        address=address,
        type=resource_type,
        name=address.rsplit(".", 1)[-1],
        actions=(action,),
        action=action,
        before={},
        after={},
    )


def test_stateful_detects_data_resource_type():
    assert is_stateful("aws_db_instance")
    assert is_stateful("google_storage_bucket")
    assert not is_stateful("null_resource")


def test_level_thresholds():
    assert level_for(3) == "low"
    assert level_for(4) == "medium"
    assert level_for(7) == "high"


def test_score_change_includes_explainable_contributions():
    risk = score_change(make_change("delete", "aws_db_instance"), impacted_count=2)

    assert risk.score == 9
    assert risk.level == "high"
    assert risk.reasons == (
        "action is delete (+5)",
        "2 downstream resources impacted (+2)",
        "stateful resource type (+2)",
    )


def test_score_change_caps_blast_radius_and_total_score():
    risk = score_change(make_change("delete", "aws_rds_cluster"), impacted_count=9)

    assert risk.score == 10
    assert "3 downstream resources impacted (+3)" in risk.reasons


def test_score_plan_uses_per_resource_blast_radius_and_sorts_by_score():
    path = f"{FIXTURES}/plan_chain.json"
    changes = load_plan(path)
    graph = build_graph(read_plan_json(path))

    risks = score_plan(changes, graph)

    assert [risk.address for risk in risks] == ["random_pet.server"]
    assert risks[0].score == 5
    assert risks[0].reasons == (
        "action is replace (+4)",
        "1 downstream resources impacted (+1)",
    )
