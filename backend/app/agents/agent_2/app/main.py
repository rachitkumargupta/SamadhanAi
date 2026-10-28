
import logging
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from .schemas import ComplaintInput, RoutingProposal
from .workflows.workflow import ResolutionWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Samadhan AI - Agent 2",
    description="Resolution and Routing Agent API for municipal complaints.",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "agent": "Agent 2 - Resolution and Routing",
    }

@app.post("/api/v1/routing/propose", response_model=RoutingProposal)
def propose_routing(complaint: ComplaintInput) -> RoutingProposal:
    try:
        logger.info(
            "Received routing request for complaint_id=%s",
            complaint.complaint_id,
        )
        workflow = ResolutionWorkflow()
        proposal = workflow.run(complaint)
        logger.info(
            "Routing proposal generated for complaint_id=%s",
            complaint.complaint_id,
        )
        return proposal
    except ValidationError as exc:
        logger.exception(
            "Schema validation failed for complaint_id=%s",
            complaint.complaint_id,
        )
        raise HTTPException(
            status_code=422,
            detail="The routing proposal failed schema validation.",
        ) from exc
    except ValueError as exc:
        logger.exception(
            "Invalid routing proposal for complaint_id=%s: %s",
            complaint.complaint_id,
            str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail="The routing model returned an invalid proposal.",
        ) from exc
    except Exception as exc:
        logger.exception(
            "Routing workflow failed for complaint_id=%s (%s)",
            complaint.complaint_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="Routing workflow processing failed.",
        ) from exc

