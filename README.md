# Atlas 🗺️

**Blast-radius analyzer for Terraform plans — see what your PR really touches.**

Atlas parses `terraform show -json` output, builds a dependency graph of your resources, and tells you which resources will be impacted downstream when a change rolls out. It also scores each change by risk level so you can prioritize reviews.

> 🚧 Under active development. v0.1 coming soon.

---

## Features

- **`atlas analyze`** — Quick summary of all resource changes (create / update / delete / replace)
- **`atlas impact`** — Full blast-radius analysis with dependency graph traversal + risk scoring
- **Heuristic scoring** — Each change gets a risk score (0-10) based on action type, number of downstream impacts, and whether the resource is stateful (databases, storage, etc.)
- **Explainable output** — Every risk score comes with human-readable reasons so you know *why* something is risky

---

## Installation

```bash
pip install atlas-iac
```

### From source

```bash
git clone https://github.com/yourusername/atlas.git
cd atlas
pip install -e ".[dev]"
```

Requires **Python 3.10+**.

---

## Usage

First, export a Terraform plan as JSON:

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
```

Then run Atlas:

```bash
# Quick summary of changes
atlas analyze plan.json

# Full blast-radius + risk scoring
atlas impact plan.json

# Control how many dependency hops to follow (default: 3)
atlas impact plan.json --max-depth 5
```

### Example output

```
$ atlas impact plan.json
Atlas impact — 1 changed, 1 impacted downstream — risk: HIGH (5/10)
  null_resource.app  why: random_pet.server -> null_resource.app
  random_pet.server — medium (5/10)  action is replace (+4); 1 downstream resources impacted (+1)
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

---

## Architecture

```
terraform plan JSON
      |
      v
+-------------+    +--------------+    +--------------+
|   Parser     |--->|   Graph      |--->|   Scorer     |
| (parser.py)  |    | (impact.py)  |    |(heuristics.py)|
+-------------+    +--------------+    +--------------+
      |                    |                   |
      v                    v                   v
 ResourceChange      downstream()        ResourceRisk
  dataclass          BFS traversal        score + reasons
```

Key design decisions:
- **Library-first** — all analysis logic lives in the library; the CLI is a thin wrapper
- **Terraform plan JSON only** — consumes `terraform show -json` output, no raw HCL parsing
- **Impact direction** — if `app` references `server`, impact flows *from* `server` *to* `app`

---

## License

MIT