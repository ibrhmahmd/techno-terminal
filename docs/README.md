# Techno Terminal — Documentation Index

> **Primary handoff reference for agents and engineers:** [`MEMORY_BANK.md`](./MEMORY_BANK.md)  
> **Last updated:** 2026-03-24 | **Schema:** v3.3 | **Branch:** `feature/api-layer`

---

## Folder Structure

| Folder / File | Purpose | Authoritative? |
|---|---|---|
| [`MEMORY_BANK.md`](./MEMORY_BANK.md) | Full architectural + code-level reference; single source of truth for AI agents | ✅ Yes |
| [`reviews/`](./reviews/README.md) | Active sprint planning, QA backlog, API roadmap | ✅ Yes (current) |
| [`plans/`](./plans/README.md) | Archived engineering plan summaries (completed work) | ✅ Historical |
| [`product/`](./product/) | Product-facing briefs (Arabic/English) | ✅ Yes |
| [`agent_sessions/`](./agent_sessions/) | AI agent conversation logs and context snapshots | 📷 Snapshots |
| [`memory_bank/`](./memory_bank/) | Background context: domain specs, architecture decisions, phase plans | ⚠️ May be stale — see `MEMORY_BANK.md §13` |

---

## Quick Reference

### Where to start (agents)
→ Read `MEMORY_BANK.md` first. If code and subdocs disagree, **trust the code + MEMORY_BANK**.

### Where to find sprint state
→ [`reviews/sprint_roadmap_post_qa_2026.md`](./reviews/sprint_roadmap_post_qa_2026.md) (v1.7, last sprint: 6b)

### Where to find the API plan
→ [`reviews/phase5_api_execution_roadmap_2026.md`](./reviews/phase5_api_execution_roadmap_2026.md)

### Where to find DB schema
→ `db/schema.sql` (canonical DDL) + `MEMORY_BANK.md §3` (summary)

---

## Staleness Policy

Subdocs under `memory_bank/` document **intent and design decisions** from earlier phases.  
They are preserved as background context but **may lag the codebase**.  
See [`MEMORY_BANK.md §13`](./MEMORY_BANK.md#13-documentation-drift-policy) for the drift policy.
