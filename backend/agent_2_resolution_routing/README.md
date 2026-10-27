# Agent 2 — Resolution & Routing

## Overview

Agent 2 is responsible for recommending how a municipal complaint should be routed after the Complaint Analyst has analyzed the complaint and produced a structured analysis.

It evaluates the available complaint information, recommends the responsible department, identifies jurisdiction-related uncertainty, determines a proposed severity level, retrieves applicable configured SLA targets, and identifies when a complaint may require multiple department-level work items.

Agent 2 produces **recommendations for backend validation**, not authoritative municipal decisions. Its outputs must not independently trigger ticket creation, officer assignment, SLA clocks, or escalation.

> **Implementation status:** This module is a partial implementation. Its routing, review, severity, SLA, and ticket-splitting logic must be integrated and validated against the main Samadhan AI backend before being treated as an operational workflow.

## Responsibilities

- Recommend the responsible department using configured reference data.
- Identify missing or uncertain classification and jurisdiction information.
- Recommend complaint severity using the available evidence and configured rules.
- Retrieve configured SLA targets when the complaint category and applicable policy are sufficiently established.
- Identify complaints that may need multiple department-level work items.
- Produce proposed child-ticket information without persisting tickets.
- Flag decisions that require human review.
- Preserve the distinction between verified reference data and provisional recommendations.

## Architecture

The module separates routing responsibilities into focused Python components.

| Component | Responsibility |
|---|---|
| `routing.py` | Coordinates routing recommendations and combines the results of the routing components. |
| `schemas.py` | Defines structured data models, enums, and the module's data contracts. |
| `review.py` | Identifies conditions that require human review. |
| `severity.py` | Recommends severity based on the available complaint information and configured logic. |
| `sla.py` | Looks up configured SLA targets. |
| `policy_retriever.py` | Supports retrieval of relevant policy information. |
| `ticket_splitter.py` | Proposes parent/child or department-level work items without persisting them. |
| `routing_reference_data.example.json` | Provides example reference data for local development. |

`__init__.py` supports Python package organization.

## Processing Workflow

1. **Receive analysis data:** Obtain the structured complaint analysis and relevant evidence from the upstream Complaint Analyst or its integration layer.
2. **Check classification confidence:** Identify missing evidence, unknown categories, low confidence, or explicit human-review requirements.
3. **Recommend department:** Use configured department and jurisdiction reference data when sufficient information is available.
4. **Assess severity:** Produce a severity recommendation using the available evidence and configured rules.
5. **Resolve SLA applicability:** Look up configured SLA targets only when the category and applicable policy are sufficiently established.
6. **Evaluate multi-department work:** Identify whether multiple department-level work items may be required.
7. **Flag review requirements:** Combine applicable review reasons and preserve unresolved uncertainty.
8. **Return proposals:** Provide structured recommendations for validation by the backend workflow.

## Human Review and Safety

Human review is required when the available information is insufficient to support a reliable recommendation.

Examples include:

- An unknown complaint category.
- Classification confidence below the configured threshold.
- Missing or insufficient evidence.
- A department that cannot be verified against configured reference data.
- Missing jurisdiction information.
- An unavailable or inapplicable policy.
- Potential safety hazards that require clarification.

When classification is uncertain, Agent 2 should not use an unverified category to select a department or apply a category-specific SLA. Missing policy information must not be replaced with invented policy values.

The review conditions and thresholds in this module are engineering defaults. They require validation against approved municipal policy before production use.

## SLA Handling

SLA recommendations depend on configured reference data and applicable policy rules.

- SLA values in example configuration are illustrative, not official municipal commitments.
- Agent 2 does not start or monitor SLA clocks.
- Agent 2 does not independently declare an SLA breach or initiate escalation.
- An uncertain category or unavailable applicable policy must not result in a fabricated SLA target.
- The backend workflow is responsible for validating and applying approved SLA rules.

## Parent/Child Work Proposals

A complaint may involve multiple problems or departments. Agent 2 can propose department-level child work items based on its routing decisions.

The module does not persist parent or child tickets, determine final ticket status, assign officers, or manage cross-department execution. These operations belong to the integrated backend workflow and require their own validation and authorization rules.

## Integration Boundaries

### Upstream dependency

The Complaint Analyst produces structured analysis, including relevant evidence, classification recommendations, uncertainty, severity/priority recommendations, and possible multi-department involvement.

Agent 2 should consume this structured result through an agreed integration contract. The exact production interface must be confirmed during integration.

### Downstream dependency

The main backend must validate Agent 2's proposals before accepting workflow actions. Depending on the approved architecture, downstream responsibilities include:

- Persisting accepted routing decisions and tickets.
- Enforcing department and jurisdiction rules.
- Managing officer assignment and authorization.
- Applying approved SLA policies and starting SLA clocks.
- Monitoring SLA deadlines and handling escalation.
- Recording audit events and coordinating parent/child work.

Agent 2 is not a replacement for these workflow services.

## Configuration

The module includes `routing_reference_data.example.json` as example reference data.

Before operational use:

1. Replace illustrative mappings with approved and versioned municipal reference data.
2. Validate department identifiers and jurisdiction rules.
3. Configure only approved SLA policies.
4. Define the expected input and output contract with the Complaint Analyst and backend integration layer.
5. Establish how policy retrieval, evidence provenance, review reasons, and errors are represented.
6. Confirm authorization, audit, and persistence responsibilities with the backend team.

Do not treat example configuration as authoritative policy.

## Local Development

The module contains Python source files and example reference data. Its dependencies, runtime requirements, and invocation method must be confirmed against the root backend configuration.

From the repository root, inspect the module and the root dependency configuration before running it. If the module is integrated into the main backend, follow the project's established environment and execution instructions.

No standalone HTTP endpoint, ticket persistence workflow, or complete production deployment contract is claimed by this README.

## Current Limitations

The following remain outside this module's current scope or require integration and validation:

- Official municipal taxonomy, department mappings, jurisdiction rules, and SLA policies.
- Production policy retrieval and verified policy provenance.
- Integration with the Complaint Analyst's final API contract.
- Backend validation and persistence of accepted routing proposals.
- Ticket creation, parent/child persistence, and officer assignment.
- SLA clock management, monitoring, and escalation.
- Human-review assignment, dispositions, and operator workflows.
- Notifications and broader staff-facing workflows.
- Production security, audit, and deployment validation.

## Design Principles

- **Evidence-based:** Recommendations should be grounded in available complaint information.
- **Configuration-driven:** Department mappings and SLA targets must come from approved reference data.
- **Human oversight:** Uncertain or potentially unsafe decisions should be flagged for review.
- **No fabricated policy:** Missing mappings or SLA rules must remain unresolved rather than being invented.
- **Separation of responsibilities:** Agent 2 recommends; the backend validates and executes.
- **Auditable integration:** Accepted decisions should be traceable through the backend's audit and correlation mechanisms.

## Status

Agent 2 provides the initial resolution and routing logic for Samadhan AI. It is intended to integrate with the Complaint Analyst and the main backend workflow after the data contracts, approved municipal policies, and downstream responsibilities have been finalized and validated.
