# Agent 2 — Complaint Resolution Workflow

## 1. Input

Agent 2 receives structured problem analysis from Agent 1, including the complaint ID, detected problems, categories, descriptions, evidence, confidence scores, and uncertainty indicators.

## 2. Classification Safety Check

Each detected problem is evaluated independently.

- Unknown category → human review.
- Confidence below the configured threshold → human review.
- Missing evidence → human review.
- Agent 1 explicitly requests review → human review.

Uncertain classifications must not result in guessed departments or category-specific SLA deadlines.

## 3. Department Routing

Agent 2 looks up department mappings using configured reference data.

If no mapping exists, or the mapping is unverified, the recommendation must not be presented as authoritative. Jurisdiction and asset ownership must also be validated.

## 4. Severity Assessment

Agent 2 recommends severity using the available problem details and its configured severity logic. The recommendation should retain its rationale and must not be represented as an official municipal decision without an approved policy.

## 5. SLA Lookup

Agent 2 retrieves response and resolution targets from configured SLA rules using the problem category and severity.

If classification is uncertain or no matching policy exists, the SLA targets remain unavailable. Demo values must not be treated as official deadlines.

## 6. Child-Ticket Proposals

Agent 2 can propose a separate child ticket for each independently actionable problem and link it to the parent complaint.

Each proposal retains the relevant category, department recommendation, severity, SLA values when available, and human-review status.

## 7. Backend Validation

The backend validates the proposed department, jurisdiction, policy references, permissions, and required approvals before persisting accepted tickets.

Agent 2 does not persist tickets or start SLA clocks.

## 8. Agent 3 Monitoring

After a ticket is accepted and its SLA deadline is established, Agent 3 handles the assigned SLA monitoring and escalation workflow.

## 9. Expected Outcome

Agent 2 returns structured recommendations. If any problem requires human review, the overall result must reflect that requirement. Supported problems should not be discarded merely because another problem is uncertain.
