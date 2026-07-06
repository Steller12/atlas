# Decision Log

## 001 — Input is Terraform plan JSON, not raw HCL
**Date:** 2026-07-06
**Decision:** Atlas consumes `terraform show -json` output only.
**Why:**
**Tradeoff accepted:**

## 002 — Terraform-only MVP, heuristic scoring, no ML
**Date:** 2026-07-06
**Decision:**
**Why:**
**Tradeoff accepted:**

## 003 — Library-first, CLI as thin wrapper
**Date:** 2026-07-06
**Decision:** All analysis lives in the library; the CLI only handles I/O and formatting.
**Why:**
**Tradeoff accepted:**