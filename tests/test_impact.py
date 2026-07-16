from atlas.graph.impact import build_graph, downstream, resolve_reference
from atlas.terraform.parser import load_plan, read_plan_json

FIXTURES = "tests/fixtures"

KNOWN = {"random_pet.server", "null_resource.app"}


def test_resolve_exact_match():
    assert resolve_reference("random_pet.server", KNOWN) == "random_pet.server"


def test_resolve_attribute_suffix():
    assert resolve_reference("random_pet.server.id", KNOWN) == "random_pet.server"


def test_resolve_unknown_returns_none():
    assert resolve_reference("var.region", KNOWN) is None


def test_build_graph_impact_direction():
    data = read_plan_json(f"{FIXTURES}/plan_chain.json")
    graph = build_graph(data)
    # impact direction: server -> app (NOT the other way around)
    assert graph == {"random_pet.server": {"null_resource.app"}}


def test_chain_fixture_finds_hidden_victim():
    path = f"{FIXTURES}/plan_chain.json"
    changes = load_plan(path)
    graph = build_graph(read_plan_json(path))
    changed = {c.address for c in changes}
    impacted = downstream(changed, graph)
    assert impacted == {"null_resource.app": ["random_pet.server", "null_resource.app"]}


def test_depth_limit_stops_bfs():
    graph = {"a": {"b"}, "b": {"c"}}
    result = downstream({"a"}, graph, max_depth=1)
    assert result == {"b": ["a", "b"]}          # c is 2 hops away — excluded


def test_changed_nodes_are_not_victims():
    graph = {"a": {"b"}, "b": {"a"}}            # cycle: a <-> b
    result = downstream({"a", "b"}, graph, max_depth=5)
    assert result == {}                           # both changed → no downstream victims
