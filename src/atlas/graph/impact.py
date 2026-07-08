"""Dependency graph + blast radius from terraform plan JSON.

Direction rule (memorize):
  app REFERENCES server  (dependency: app -> server)
  so impact flows        server -> app
  and we store IMPACT direction: graph[server] = {app}
"""
from collections import deque

def parse_references(data: dict) -> list[tuple[str, str]]:
    """Return (referencing_address, raw_reference) pairs from the configuration section."""
    resources = data.get("configuration",{}).get("root_module", {}).get("resources", [])
    pairs=[]
    for res in resources:
        addr=res.get("address")
        if not addr:
            continue
        for expr in res.get("expressions",{}).values():
            if isinstance(expr, dict):
                for ref in expr.get("references", []):
                    pairs.append((addr, ref))
    return pairs
    # 1. resources = data.get("configuration", {}).get("root_module", {}).get("resources", [])
    #    (chained .get() with defaults — configuration section may be absent; empty list = no edges, not a crash)
    # 2. pairs = []   ← accumulator pattern again
    # 3. for res in resources:
    #        addr = res.get("address")
    #        if not addr: skip (continue)
    #        for expr in res.get("expressions", {}).values():
    #            if isinstance(expr, dict):              ← tolerate non-dict expression values
    #                for ref in expr.get("references", []):
    #                    append (addr, ref) to pairs
    # 4. return pairs
    ...


def collect_addresses(data: dict) -> set[str]:
    """All known resource addresses: from resource_changes + configuration resources."""

    known =set()
    for rc in data.get("resource_changes",[]):
        addr=rc.get("address")
        if addr:
            known.add(addr)
    resources= data.get("configuration", {}).get("root_module",{}).get("resources",[])
    for res in resources:
        addr = res.get("address")
        if addr:
            known.add(addr)
    return known
    # set comprehension over data.get("resource_changes", []) → rc.get("address")
    # then add addresses from configuration resources (same walk as parse_references step 1)
    # return the set (drop None/empty)
    ...


def resolve_reference(ref: str, known: set[str]) -> str | None:
    """Map a raw reference like 'random_pet.server.id' to a known address, or None."""
    if ref in known:
        return ref
    for addr in known:
        if ref.startswith(addr+"."):
            return addr  
    return None
    # exact match: ref in known → return ref
    # attribute form: for addr in known: if ref.startswith(addr + ".") → return addr
    # anything else (var.x, local.y, module inputs...) → return None
    ...


def build_graph(data: dict) -> dict[str, set[str]]:
    """Adjacency map in IMPACT direction: graph[changed_thing] = {things it impacts}."""
    known = collect_addresses(data)
    graph={}
    for (referencing_addr, raw_ref) in parse_references(data):
        target= resolve_reference(raw_ref, known)
        if target is None or target==referencing_addr:
            continue 
        graph.setdefault(target, set()).add(referencing_addr)
    return graph
    # known = collect_addresses(data)
    # graph: dict[str, set[str]] = {}
    # for (referencing_addr, raw_ref) in parse_references(data):
    #     target = resolve_reference(raw_ref, known)
    #     if target is None or target == referencing_addr: skip
    #     ⚠ DIRECTION: referencing_addr depends on target
    #        → graph.setdefault(target, set()).add(referencing_addr)
    #     (setdefault = "get the set, creating an empty one first if missing")
    # return graph
    ...


def downstream(
    changed: set[str], graph: dict[str, set[str]], max_depth: int = 3
) -> dict[str, list[str]]:
    """BFS from changed nodes. Returns impacted_address -> why-path (list of addresses).

    Example: {"null_resource.app": ["random_pet.server", "null_resource.app"]}
    Changed nodes themselves are NOT in the result — only downstream victims.
    """
    queue=deque((c,[c],0) for c in changed)
    visited=set(changed)
    result={}
    while queue:
        addr, path, depth = queue.popleft()
        if depth==max_depth:
            continue
        for neighbour in graph.get(addr, set()):
            if neighbour in visited:
                continue
            visited.add(neighbour)
            result[neighbour]=path+[neighbour]
            queue.append((neighbour, path+[neighbour],depth+1))
    return result

    # classic BFS — same as your Week 3 LeetCode problems:
    # queue = deque of (address, path_so_far, depth) seeded with (c, [c], 0) for each changed
    # visited = set(changed)   ← seed visited with changed so you don't re-visit sources
    # result = {}
    # while queue:
    #     addr, path, depth = queue.popleft()
    #     if depth == max_depth: continue
    #     for neighbor in graph.get(addr, set()):
    #         if neighbor in visited: continue
    #         visited.add(neighbor)
    #         result[neighbor] = path + [neighbor]
    #         queue.append((neighbor, path + [neighbor], depth + 1))
    # return result
    ...