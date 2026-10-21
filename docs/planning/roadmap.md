# Roadmap and team workstream boundaries

**Source:** [Supplied implementation blueprint](../architecture/implementation-blueprint.md). This is a sequence, not a schedule or assignment of people. The current code is only the initial text intake/tracking slice; see [backend status](../../backend/README.md).

## Implementation phases

1. **Phase 0 — Foundation and decisions:** inspect current repository/docs; approve role grants/separation and real-world reviewer mapping, anonymous-token security operations, state names/transitions, taxonomy/reference-data owners, image/privacy controls, reminder delivery, technology versions, and acceptance criteria. Preserve the fixed 48-hour decision window, reminder with pending status after no response, and no closure by silence. The seven-calendar-day reviewer handoff and late-response behavior are documented project policy; confirm jurisdiction timezone source, daylight-saving ambiguity rule, reviewer authority/outcomes, and deployment recovery before implementing them.
2. **Phase 1 — Deterministic engine and routing core:** extend existing FastAPI/PostgreSQL slice; implement validated private image upload, location capture, atomic persistence and durable async-job intent; add Complaint Analyst and human-review fallback; implement approved policy retrieval and routing validation; build the deterministic recoverable SLA worker and idempotent event processing. Test critical core boundaries.
3. **Phase 2 — Multi-jurisdiction and escalation:** add parent-child tickets, independent child assignment/SLA/history, parent aggregation, rejection reasons and routing-loop controls; trigger Monitoring & Escalation from valid breach events; add escalation history and durable in-app notification records. Define optional WhatsApp/SMS integration interfaces when feasible; external delivery follows approval.
4. **Phase 3 — Verification and citizen audit:** add evidence requirements, citizen notification/proof card and fixed 48-hour confirmation/dispute workflow, reminder at 48 hours with the case remaining pending, assigned independent review, scoped audit, analytics, and critical recovery/security/end-to-end checks. Implement the intended seven-calendar-day `VERIFICATION_OVERDUE` handoff with the documented late-response behavior after confirming jurisdiction timezone/DST handling, recovery, reviewer authority/mapping, and permitted outcomes.
5. **Phase 4 — Frontend integration and demo hardening:** build citizen, officer, admin and independent-review interfaces after API contracts stabilize; seed clearly labelled demonstration policies/data; deploy within verified platform guarantees; prepare diagrams, test report, and demonstration script.
6. **Future scope:** duplicate detection, heatmaps, prediction, dynamic allocation, voice/multilingual, IoT and municipal integration only after separate need/policy approval.

Do not interpret phase names as feature-completion evidence. Model/provider, official policy and jurisdiction data, storage, scheduler, and deployment remain dependencies. AI is asynchronous and may fail without blocking persisted complaint handling. The SLA worker is deterministic; the escalation agent is event-triggered, never a deadline poller.

## Workstream boundaries

- **Product/policy:** user outcomes, taxonomy, official jurisdiction/department sources, lifecycle, SLA/escalation/verification rules and acceptance. Anonymous reporting is supported; token encoding, key management, expiry/renewal defaults, abuse thresholds and recovery channel remain security/implementation choices. Do not promise recovery for a lost token without independent identity proof.
- **Frontend:** accessible citizen, officer, admin and independent-review interfaces, location/image capture, client feedback and API integration; API enforces all security and validation.
- **Backend:** API, object references, identity/authorization, lifecycle, parent-child records, transactions/migrations, durable jobs/events, SLA worker, audit, notification interfaces, and operations behavior.
- **AI:** contracts/evaluation for exactly three agents; proposals only, with bounded tools and human review. Backend owns permissions and writes.
- **Integration/operations:** model, object storage, notification and municipal adapters; credentials, deployment, monitoring, backup, recovery and provider outage handling.
- **Quality:** cross-workstream tests for image validation, authorization, composite routing, SLA scale/recovery/idempotency, verification, and end-to-end acceptance.
