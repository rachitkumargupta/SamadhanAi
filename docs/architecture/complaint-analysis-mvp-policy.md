# Complaint Analyst MVP analysis framework

**Status:** The framework below is implemented as a configurable, provisional engineering baseline. It is **not an officially approved municipal taxonomy, priority policy, emergency protocol, or service-level policy**. No model or rule result authorizes assignment, dispatch, closure, or an emergency response.

**Configuration:** [`analysis_policy.json`](../../backend/app/agents/analysis_policy.json), loaded by [`analysis_policy.py`](../../backend/app/agents/analysis_policy.py). Set `COMPLAINT_ANALYST_POLICY_FILE` to use a deployment-specific JSON file. `COMPLAINT_ANALYST_CATEGORIES` may restrict the configured taxonomy; any override must include the configured uncertain fallback. Edit/version the JSON to change IDs, definitions, criteria, weights, or thresholds.

## What the project already defines

- FR-ANL-02 requires a versioned structured proposal based on the required image and optional description/location, with evidence, generated description as needed, category, severity/priority recommendations, uncertainty, missing information, possible multi-department involvement, and review recommendation.
- FR-ANL-03 requires visible facts to remain distinguishable from inferences. Confidence semantics are explicitly TBD in the requirements.
- FR-ANL-04 forbids the agent from rejecting, assigning, merging, closing, or performing actions.
- FR-ANL-05 requires persistence on failure and a manual-handling path.
- FR-ANL-06 gives candidate categories and requires configurable taxonomy plus deterministic priority/safety rules, while saying taxonomy and policy values need approval.
- UC-01 makes the image required and says missing location is preserved for location review. The integration contract already sets accepted image formats, size/dimension bounds, normalization, and metadata stripping.

The project does **not** define official category boundaries, numeric priority thresholds, confidence calibration, emergency criteria, or an approved review owner. The defaults below make development behavior deterministic while marking these decisions as provisional.

## Provisional taxonomy

The IDs are the candidate categories from FR-ANL-06. The JSON file includes short operational descriptions for consistent model prompts and fallback behavior:

| ID | Provisional scope |
|---|---|
| `roads_potholes` | Visible damage or defect affecting a public road, footpath, curb, or surface. |
| `garbage_sanitation` | Visible litter, unmanaged waste, overflowing public bins, or sanitation concern. |
| `drainage_sewage` | Visible blocked drains, standing water, sewage overflow, or drainage infrastructure concern. |
| `water_leakage` | Visible leakage, water wastage, or public water infrastructure damage. |
| `streetlights_electrical` | Visible streetlight outage or public electrical infrastructure damage. |
| `damaged_public_infrastructure` | Other visible damage to public infrastructure. |
| `other_uncertain` | Outside configured categories or insufficient evidence to classify reliably; always required as the fallback. |

These definitions are engineering aids, not authority/jurisdiction determinations. The model must not infer cause, responsible department, jurisdiction, or official eligibility from an image.

## Provisional priority rubric

Priority is an explainable **recommendation** based on evidence-backed factors. The model may propose a priority, but application code computes the returned `priority_recommendation`; the model's suggestion is retained separately as `model_priority_recommendation`. Factors must cite text present in their declared source (`image_evidence` or `citizen_description`). Unsupported or unknown factors do not score and require review. Duplicate factor IDs count once.

| Criterion | Points | Provisional interpretation |
|---|---:|---|
| `routine_localized_issue` | 0 | Localized maintenance issue with no supported service, access, or potential-safety impact. |
| `service_disruption` | 1 | Evidence supports disruption to a public service or normal infrastructure use. |
| `public_access_obstructed` | 2 | Evidence supports obstruction or material restriction of public access. |
| `potential_safety_hazard` | 3 | Evidence suggests a possible hazard; always requires human triage. |

The configurable score bands are **0 = low**, **1 = medium**, and **2 or more = high**. The automated MVP never emits `critical`; a model `critical` suggestion is retained, the computed score remains visible, and human review is required. These values are provisional and must not trigger operational action. A safety signal is explicitly **not** an emergency determination or official emergency-service instruction.

The application-side mapping is deterministic: the same validated model proposal, input context, and policy version produce the same category fallback, priority score, and review flags. The vision model itself can vary between calls; repeatability of model judgments must be measured against an approved evaluation set and is not claimed by the deterministic rules.

The JSON includes an editable potential-hazard phrase list. A phrase match in the citizen description or visible evidence only raises the review flag and provisional high-priority factor; it is intentionally conservative and incomplete. Model-detected hazards also require review. False positives should be reviewed, not suppressed by treating the rule as an emergency classifier.

Policy loading rejects configurations that omit the potential-safety-hazard criterion, place its score below the configured high band, or remove its mandatory human-review trigger. Policy ID, version, and approval-status metadata must also be present so outputs cannot silently lose provenance.

## Confidence, evidence, and missing information

`confidence_level` is `high`, `medium`, or `low`, with the following provisional meaning:

- `high`: one category is clearly supported by visible evidence, with no material uncertainty or conflict.
- `medium`: a plausible category exists, but evidence/context is incomplete or ambiguous.
- `low`: evidence is unclear, conflicting, or insufficient.

These are provider self-assessments, **not calibrated probabilities**. Medium and low always require human review. No visible evidence yields `insufficient_context`, `other_uncertain`, no priority recommendation, and a `clearer_image` missing-information code. If citizen text is absent, a grounded generated description is required; if the provider cannot supply it, the outcome is reviewable `insufficient_context` rather than a fabricated description. A missing location is flagged with code `location` and requires location verification, but does not by itself prevent image classification. Conflicting context is flagged and requires review. Invalid/oversized/unsupported images are rejected at intake before analysis.

## Structured result

Schema version `1.1` returns:

- outcome and grounded generated description (when citizen text is absent);
- visible evidence, facts, and inferences as separate lists;
- category, severity recommendation, model priority suggestion, and deterministic provisional priority;
- evidence-linked priority factors, score, criteria IDs, and plain-language score explanation;
- confidence level, uncertainty, missing-information text and stable codes, and contradictions;
- possible multi-department flag, human-review flag and reasons;
- policy ID, version, and approval status so provisional outputs remain identifiable.

The model proposal schema excludes application-derived score/explanation fields. The application validates the proposal, applies the policy, and persists the enriched result. All returned classifications remain proposals.

## Decisions still requiring project/policy approval

Before production use, the responsible project and municipal stakeholders must approve or replace the candidate taxonomy, category definitions, severity/priority meaning and thresholds, hazard indicators, reviewer identity/scope and dispositions, provider and data-handling terms, media scanning/storage/retention controls, and an evaluation dataset/rubric/acceptance thresholds. Until then, outputs carry `provisional_engineering_default_not_municipal_policy` and remain human-review recommendations only.
