# Schema inventory and status

## Reported 25-table inventory

1. `departments`
2. `wards`
3. `users`
4. `roles`
5. `user_roles`
6. `officers`
7. `complaints`
8. `assignments`
9. `complaint_media`
10. `complaint_events`
11. `complaint_analysis`
12. `background_jobs`
13. `agent_runs`
14. `resolution_submissions`
15. `citizen_verification`
16. `independent_reviews`
17. `notifications`
18. `notification_attempts`
19. `sla_policies`
20. `complaint_sla`
21. `audit_logs`
22. `knowledge_documents`
23. `knowledge_chunks`
24. `escalation_records`
25. `resolution_evidence`

This is the inventory reported during local setup. It must be checked against the current database export before being treated as authoritative.

## Confirmed during local setup

- Database: `samadhan_ai_target`
- PostgreSQL version reported: 18.6, Windows 64-bit
- `pgcrypto` and `vector` extensions enabled successfully
- `knowledge_chunks.embedding` verified as `vector`
- SQLAlchemy connection test returned `samadhan_ai_target`
- Indexes reviewed for `complaints`, `complaint_media`, `background_jobs`, `agent_runs`, `complaint_analysis`, and `complaint_events`
- Six foreign keys were adjusted to specify `ON DELETE RESTRICT`

## Backend model scope reviewed

The provided SQLAlchemy models cover:
- `complaints`
- `complaint_media`
- `background_jobs`
- `agent_runs`
- `complaint_analysis`
- `complaint_events`

The actual database contains additional columns and relationships beyond these models. Preserve them until the team confirms whether they are required.

## Work required before finalizing

- Export the complete current schema (tables, constraints, indexes, defaults, extensions).
- Compare it with the final ER diagram and all current backend models.
- Reconcile with Alembic migration history.
- Choose the canonical schema initialization approach with the team.
- Test it on a fresh disposable database.
