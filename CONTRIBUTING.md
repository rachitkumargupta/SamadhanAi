# Contributing

Samadhan AI is a team project. Coordinate changes through small, reviewable pull requests and keep the documentation aligned with the implementation.

## Workflow

1. Agree on the issue and acceptance criteria with the relevant workstream.
2. Create a short-lived branch from the team's agreed integration branch. Suggested format: `feat/short-topic`, `fix/short-topic`, `docs/short-topic`.
3. Keep each pull request focused; describe behavior, design choices, risks, and verification performed.
4. Request review from an affected workstream. Resolve or explicitly discuss feedback before merging.
5. Do not commit secrets, real citizen data, generated credentials, local databases, virtual environments, or build output.

The team GitHub repository currently uses `main`; its initial commit contains a project README. This workspace is now based on that history on a local `feature/backend-foundation` branch. Confirm the team's branch naming, merge strategy, protection rules, and required review count before merging.

## Commits

Use a concise imperative subject, optionally following Conventional Commits (for example, `docs: define complaint lifecycle`). The team has not yet selected a mandatory commit convention.

## Engineering expectations

- Follow the language and formatting standards documented for the affected component.
- Validate inputs at system boundaries and enforce permissions server-side.
- Include focused tests for changed behavior when implementation starts; document commands and results.
- Update requirements, API contracts, data model, and ADRs when behavior or decisions change.
- Never claim an integration or test works unless it has been run and verified.

## Definition of Done (proposed)

- Acceptance criteria are met and reviewed.
- Relevant automated checks pass; limitations or skipped checks are stated.
- Authorization, validation, error handling, and audit implications are considered.
- Documentation and examples match the change.
- No secrets or unrelated generated files are included.
