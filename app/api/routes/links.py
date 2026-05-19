"""FastAPI router for link creation and processing."""

from fastapi import APIRouter, HTTPException

from app.api.schemas.links import LinkRequest, LinkResponse
from lib.llm import categorize_link, summarize_url

router = APIRouter(prefix="/links", tags=["links"])


@router.post("/", response_model=LinkResponse, status_code=201)
async def create_link(request: LinkRequest) -> LinkResponse:
    """Accept a URL, derive its summary and category, and return a fully-populated link.

    - If *summary* is not provided in the request it is generated via Claude.
    - Category is always assigned by Claude based on the summary.
    """
    try:
        summary = request.summary or await summarize_url(request.url)
        category = categorize_link(summary)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to process URL: {exc}") from exc

    return LinkResponse(
        url=request.url,
        title=request.title,
        summary=summary,
        category=category,
    )
