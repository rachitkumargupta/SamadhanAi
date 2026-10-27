# Agent 2 — Integration Contract

## 1. Purpose

This document defines the expected inputs, outputs, and responsibilities for integrating Agent 2 (Resolution and Routing Agent) into Samadhan AI.

Agent 2 generates structured recommendations. The application backend validates and approves these recommendations before persistence.

## 2. Input from Agent 1

Agent 2 expects structured problem analysis containing, where available:

- Parent complaint ID
- Unique problem ID for each detected problem
- Problem category and description
- Supporting evidence
- Classification confidence
- Explicit uncertainty or human-review indicators
- Severity hints
- Jurisdiction and asset-owner context

The actual input contract must be aligned with Agent 1's implemented schema before integration.

## 3. Output from Agent 2

Agent 2 produces a structured response containing:

- Complaint ID and overall status
- A decision for each detected problem
- Category and severity recommendations
- Department recommendation and verification status
- Rationale and policy references when available
- SLA response and resolution targets when configured
- Human-review flags and explanations
- Proposed child tickets linked to the parent complaint
- Notes describing limitations and demo configuration

## 4. Department and Policy Validation

The backend must validate department IDs, jurisdiction, asset ownership, and policy references against approved records.

A department mapping from demo configuration must not be treated as an official assignment.

Missing or unverified mappings require appropriate review rather than fabricated routing decisions.

## 5. SLA Handling

Agent 2 looks up configured response and resolution targets.

If classification is uncertain or a matching SLA rule is unavailable, the corresponding SLA values must remain unavailable rather than being invented.

The backend establishes SLA deadlines according to the approved policy and defined clock-start event. Agent 2 does not start or monitor SLA clocks.

## 6. Human Review

Human review is required for uncertain classifications, insufficient evidence, unknown categories, unverified department mappings, unclear jurisdiction, or unresolved policy questions.

The backend must prevent proposals requiring approval from being automatically assigned or persisted as approved tickets.

## 7. Child-Ticket Proposals

Agent 2 can propose one child ticket per independently actionable problem.

The backend should validate the parent complaint, problem IDs, proposal status, and duplicate-submission conditions before persisting approved child tickets.

Proposed IDs are not database-generated ticket IDs.

## 8. Agent 3 Responsibilities

After the backend accepts a ticket and establishes its SLA deadline, Agent 3 handles the assigned monitoring and escalation workflow.

Agent 2 does not monitor SLA breaches or initiate escalation actions.

## 9. Error and Uncertainty Behavior

- Unknown category: require human review.
- Insufficient evidence: require human review.
- Missing department mapping: do not invent a department.
- Unverified mapping or unclear jurisdiction: require review.
- Missing SLA rule: return unavailable targets.
- Demo configuration: clearly identify it as unverified.
- Multiple problems: preserve each problem independently, even if another problem requires review.

## 10. Integration Readiness

Before integration is considered complete:

- [ ] Align Agent 2 input models with Agent 1's actual output.
- [ ] Confirm the output models match the backend's expectations.
- [ ] Validate routing and SLA references against approved data.
- [ ] Confirm review-required proposals cannot bypass approval.
- [ ] Confirm Agent 3 receives only accepted tickets with established SLA deadlines.
