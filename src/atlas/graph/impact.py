"""Dependency graph + blast radius from terraform plan JSON.

Direction rule (memorize):
  app REFERENCES server  (dependency: app -> server)
  so impact flows        server -> app
  and we store IMPACT direction: graph[server] = {app}
"""
from collections import deque

def parse_references(data: dict) -> list[tuple[str, str]]:
    """
    Return (referencing_address, raw_reference) pairs from the configuration
    section.
    """
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



def resolve_reference(ref: str, known: set[str]) -> str | None:
    """Map a raw reference like 'random_pet.server.id' to a known address, or None."""
    if ref in known:
        return ref
    for addr in known:
        if ref.startswith(addr+"."):
            return addr
    return None



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

