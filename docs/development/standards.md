# Development standards

These standards apply to ongoing development against the [master implementation blueprint](../architecture/implementation-blueprint.md). The repository already contains a partial backend starter; distinguish planned target work from implemented and verified behavior. Tool versions and CI choices remain pending; see [ADR-001](../decisions/ADR-001-technology-stack.md).

## Branches and reviews

Use short-lived topic branches and focused pull requests. Include issue/context, behavior, acceptance criteria, risks, and actual checks. Require review from an affected workstream; choose branch protection and merge policy with the team. Never commit directly to a protected integration branch once established.

## Commits

Use imperative, concise subjects. Conventional Commit prefixes are recommended but not mandatory until agreed. Keep commits coherent and avoid mixing generated files or unrelated formatting changes.

## Formatting and code quality

Python: choose one formatter and linter (for example Ruff) and enable type checking proportionate to code maturity. JavaScript/React: choose a formatter/linter and keep JavaScript unless the team explicitly approves a change. Pin supported tool/runtime versions in project configuration after selection. Use `.editorconfig` defaults in this repository.

## Testing

Prioritize domain rules, state transitions, permissions, SLA calculation, database constraints/migrations, API contracts, integration failure behavior, and AI schema/fallback behavior. Keep deterministic unit tests separate from provider-dependent evaluations. Document commands and report only checks actually run. Test framework and CI provider are TBD.

## Documentation

Update the PRD when scope/acceptance changes; architecture and ADRs when boundaries/decisions change; API and data docs with contracts/schema; setup/troubleshooting with actual developer experience. Mark proposals and unknowns clearly.

## Environment and secrets

Commit only placeholder examples after real configuration variables are known. Keep `.env`, credentials, private keys, dumps, citizen data, and local databases out of version control. Use environment-based config and a deployment secret store. Never paste secrets into logs or AI prompts.

## Definition of Done

- Agreed acceptance criteria are met.
- Relevant tests and checks were run and results are reported accurately.
- Input validation, authorization, transaction/audit behavior, and failure cases are addressed.
- API/data/docs and migration implications are reviewed.
- Changes receive appropriate review and contain no secrets or unrelated artifacts.
