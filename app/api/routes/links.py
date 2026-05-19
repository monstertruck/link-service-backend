"""FastAPI router for link creation and processing."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.schemas.links import LinkRequest, LinkResponse
from app.crud.links import create_link as db_create_link
from app.crud.links import delete_link as db_delete_link
from app.crud.links import get_link, list_links
from app.db import get_session
from lib.llm import categorize_link, summarize_url

router = APIRouter(prefix="/links", tags=["links"])


@router.post("/", response_model=LinkResponse, status_code=201)
async def create_link(
    request: LinkRequest, session: Session = Depends(get_session)
) -> LinkResponse:
    """Accept a URL, derive its summary and category, persist it, and return it.

    - If *summary* is not provided it is generated via Claude.
    - Category is always assigned by Claude based on the summary.
    - Returns 409 if the URL has already been saved.
    """
    try:
        summary = request.summary or await summarize_url(request.url)
        category = categorize_link(summary)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to process URL: {exc}") from exc

    try:
        record = db_create_link(
            session, url=request.url, summary=summary, category=category, title=request.title
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return LinkResponse(
        id=record.id,
        url=record.url,
        title=record.title,
        summary=record.summary,
        category=record.category,
    )


@router.get("/", response_model=list[LinkResponse])
def list_all_links(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
) -> list[LinkResponse]:
    """Return a paginated list of all saved links."""
    records = list_links(session, skip=skip, limit=limit)
    return [
        LinkResponse(
            id=r.id, url=r.url, title=r.title, summary=r.summary, category=r.category
        )
        for r in records
    ]


@router.get("/{link_id}", response_model=LinkResponse)
def get_one_link(link_id: int, session: Session = Depends(get_session)) -> LinkResponse:
    """Fetch a single saved link by ID."""
    record = get_link(session, link_id)
    if not record:
        raise HTTPException(status_code=404, detail="Link not found")
    return LinkResponse(
        id=record.id, url=record.url, title=record.title, summary=record.summary, category=record.category
    )


@router.delete("/{link_id}", status_code=204)
def delete_one_link(link_id: int, session: Session = Depends(get_session)) -> None:
    """Delete a saved link by ID."""
    deleted = db_delete_link(session, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
