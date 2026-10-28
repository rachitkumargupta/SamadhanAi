# Samadhan AI database design and maintenance

## Purpose

The database supports complaint intake and processing, media metadata, complaint event history, background processing jobs, AI-agent runs, and analysis results.

## Core backend tables

- `complaints`: public reference, owner subject, description, location text, status, creation time.
- `complaint_media`: media object metadata, type, size, checksum, uploader, and creation time.
- `complaint_events`: complaint event type, actor, previous/resulting state, reason, correlation ID, visibility, and timestamp.
- `background_jobs`: work type, status, retry information, lease fields, and timestamps.
- `agent_runs`: agent name, provider/model, schema version, attempt number, status, and timestamps.
- `complaint_analysis`: structured JSON analysis output linked to a complaint, media record, and agent run.

These descriptions summarize the six supplied SQLAlchemy models; confirm details against the current source before changing the schema.

## Relationships in supplied models

- A complaint can have many media records and events.
- A background job references a complaint and a media record.
- An agent run references a complaint and a background job.
- A complaint analysis record references a complaint, media record, and agent run.

The database also contains additional fields and relationships not represented in these six models. Do not remove them without team review.

## Development workflow

1. Create a local development database.
2. Configure `DATABASE_URL` privately in `.env`.
3. Install compatible PostgreSQL and pgvector components.
4. Enable extensions using `database/extensions.sql`.
5. Initialize schema using the team's agreed migrations or schema script after reconciliation.
6. Verify with `database/verify_schema.sql`.
7. Test against a fresh disposable database before merging database changes.

## Security and change control

Never commit credentials, real citizen/complaint data, or local virtual environments. Coordinate schema changes with backend developers. Prefer repeatable reviewed migrations over undocumented manual edits.
