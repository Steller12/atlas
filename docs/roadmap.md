# Atlas Roadmap

> Living document - features organized by effort level and priority.

---

## Tier 1 - Quick Wins (Low Effort, High Impact)

### 1. atlas map - Visual dependency graph
**Command:** atlas map plan.json
**Output:** atlas-map.html - self-contained HTML with interactive force-directed graph.

Uses vis-network (embedded via CDN) to render nodes/edges with:
- Size by action (delete = large, create = small)
- Color by risk level
- Arrows for dependency direction
- Hover tooltips

**Effort:** Moderate - new CLI command + HTML template renderer

### 2. Multi-provider severity scoring
Extend _STATEFUL_HINTS in heuristics.py to cover AWS, GCP, and Azure data services.

**Effort:** Trivial - extend a tuple

### 3. --min-risk filter
atlas impact plan.json --min-risk high - only show changes above threshold.

**Effort:** Small - CLI option + output filter

### 4. JSON / Markdown output
atlas impact plan.json --format json|markdown - pipe results into CI/CD.

**Effort:** Small - swap print logic

---

## Tier 2 - Core Enhancements (Moderate Effort)

### 5. CI-friendly exit codes
atlas impact plan.json --fail-on high - exit non-zero on high-risk changes.

**Effort:** Moderate - CLI option + post-scoring check

### 6. Child module support
Recursively walk child_modules in configuration. Currently only root_module.

**Effort:** Moderate - recursive tree walk

### 7. Auto-run terraform show
atlas plan / atlas impact - run terraform show -json internally.

**Effort:** Moderate - subprocess call

### 8. HTML impact report
Self-contained HTML combining dependency graph, change table, diffs, risk summary.

**Effort:** Moderate-High

---

## Tier 3 - Long-term (High Value)

### 9. Diff view
Field-level before/after comparisons per resource.

**Effort:** Moderate - structured dict diff

### 10. PR comment integration
GitHub Action / GitLab CI template posting risk report on PRs.

**Effort:** High - action template + CI wiring

### 11. Policy-as-code
Custom rules in .atlas-rules.yaml to block/warn on specific changes.

**Effort:** High - YAML parser + rule engine

---

## Data Flow for atlas map

plan.json -> read_plan_json() -> build_graph() -> {nodes, edges} -> HTML template -> atlas-map.html

**Visualization:** vis-network standalone UMD from CDN. Zero Python deps added.
