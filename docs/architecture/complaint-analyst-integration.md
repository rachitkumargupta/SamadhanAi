# Complaint Analyst integration contract

**Status:** Agent core implemented; application/API/job integration is pending because image-first intake, private media persistence, and durable job tables do not yet exist.

## Purpose and boundaries

The Complaint Analyst reads one complaint image and the minimum optional citizen description/location context. It returns a versioned, typed proposal. It has no database session, complaint mutation, routing, assignment, notification, SLA, or lifecycle authority. The application must validate the result and own persistence and any subsequent action.

## Python interface

```python
from backend.app.agents.complaint_analyst import AnalystInput, build_complaint_analyst
from backend.app.config import get_settings

agent = build_complaint_analyst(get_settings())
proposal = agent.analyze(AnalystInput(
    image=image_bytes,
    description="Water is leaking near the sidewalk",
    location_text="Citizen-provided location, if permitted",
))
```

`image` is required. Accepted decoded formats are JPEG, PNG, and WebP. The module caps uploads at 10 MiB and 20 megapixels, applies EXIF orientation, converts to JPEG, and drops source metadata before the provider call. It does not persist uploaded bytes; callers must use private storage and access control.

The `ComplaintAnalysis` schema version is `1.0`. It contains:

- `outcome`: `completed`, `needs_review`, or `insufficient_context`;
- `generated_description`: grounded short description when citizen text is absent;
- `visible_evidence`, `facts`, and `inferences` as separately identified lists;
- nullable `category`, `severity_recommendation`, and `priority_recommendation`;
- `uncertainty` and `missing_information` lists;
- `possible_multi_department`, `human_review_recommended`, and review reasons.

Recommendation levels are `low`, `medium`, `high`, and `critical`. Their policy meaning is not approved; they must not directly trigger workflow decisions. Categories default to roads/potholes, garbage/sanitation, drainage/sewage, water/leakage, streetlights/electrical, damaged public infrastructure, and other/uncertain. Override the comma-separated `COMPLAINT_ANALYST_CATEGORIES` setting only with approved taxonomy identifiers. Unknown categories are rejected.

The model is instructed to report visible observations separately from inferences, avoid inferring cause/jurisdiction/responsible department, and recommend review for uncertainty or safety concerns. These are model instructions, not deterministic safety or priority policy. Application policy checks and human review remain necessary.

## Provider configuration and errors

The current adapter uses the OpenAI Responses API with Structured Outputs. Configure:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | API credential; absent/blank means `AnalystUnavailable` |
| `COMPLAINT_ANALYST_MODEL` | Vision-capable model ID; default `gpt-6-luna` |
| `COMPLAINT_ANALYST_TIMEOUT_SECONDS` | Bounded provider timeout; default 30 seconds |
| `COMPLAINT_ANALYST_CATEGORIES` | Comma-separated allowed taxonomy IDs |

The request sets `store=false` and disables SDK retries. Provider/network/parse failures raise `AnalystProviderError`; invalid or oversized uploads raise `AnalystInputError`. No fallback response is synthesized. A caller should persist the complaint/media/job before invocation as required by the architecture, and record an explicit failure/review outcome if analysis fails.

## Workflow/API integration status

There is no public analysis endpoint yet. The current complaint endpoint accepts text JSON and has no media row, private object store, agent-run/analysis record, or durable analysis job. The agent remains a callable service boundary rather than making a model call outside the documented atomic intake/job workflow. The next integration step is to add the minimum private media reference and durable job persistence, then have a worker load authorized media and call this interface. Do not expose local file paths or raw provider errors to citizens.

## Tests

Run `python -m unittest discover -s tests -v`. Tests use deterministic provider stubs and do not require credentials or make network calls. Live provider behavior requires a configured API key and is not verified by the local unit suite.
