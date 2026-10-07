# Data Model: Review Competition Routers

**Created**: 2026-05-13  
**Input**: spec.md, research.md

## Overview

This audit produces documentation artifacts — not runtime data. The entities defined here are conceptual models for tracking audit findings.

---

## Entity: EndpointRecord

Represents a single API endpoint in the audit inventory.

| Field | Type | Description |
|-------|------|-------------|
| file | string | Path to router file |
| line | integer | Starting line number |
| method | string | HTTP method (GET, POST, PUT, PATCH, DELETE) |
| path | string | URL path template |
| auth_guard | string | Auth decorator used |
| service_class | string | Service class injected |
| service_method | string | Method called on service |
| input_dto | string | Input Pydantic model name |
| output_dto | string | Output Pydantic model name |
| is_inline_dto | boolean | Whether the DTO is defined in the router file |
| status | enum(verified, issue_found, needs_review) | Audit status |

## Entity: AuditFinding

Represents a single issue discovered during the audit.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier (F-001, F-002, ...) |
| severity | enum(HIGH, MEDIUM, LOW, INFO) | Impact severity |
| category | string | Finding type (dead_code, schema_mismatch, auth_issue, arch_violation, etc.) |
| location | string | File path and line number |
| description | string | What was found |
| evidence | string | Code excerpt or reference |
| recommendation | string | Suggested remediation |
| status | enum(open, resolved, won_t_fix) | Resolution status |

## Entity: RemediationItem

Represents a single action item to fix an audit finding.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier (R-001, R-002, ...) |
| finding_id | string | Links to AuditFinding.id |
| priority | enum(P1, P2, P3) | Implementation priority |
| effort | enum(small, medium, large) | Estimated effort |
| description | string | Action to take |
| files_affected | list[string] | Files that need changes |
| depends_on | list[string] | IDs of RemediationItems that must be done first |
| verification | string | How to verify the fix |

## Relationships

- EndpointRecord → AuditFinding: An endpoint can have 0..N findings
- AuditFinding → RemediationItem: A finding can have 1..N remediation items
- RemediationItem ⊸ RemediationItem: Dependency ordering via depends_on
