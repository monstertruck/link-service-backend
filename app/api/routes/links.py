"""FastAPI router for link creation and processing."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

from app.api.schemas.links import LinkCategory, LinkRequest, LinkResponse, LinkStatus
from app.crud.links import count_links_by_category
from app.crud.links import create_link as db_create_link
from app.crud.links import delete_link as db_delete_link
from app.crud.links import get_link, get_link_by_url, list_links, update_link_status
from app.models.link import LinkRecord
from app.db import get_session
from lib.llm import categorize_link, summarize_url_with_title
from lib.utils import title_from_url

router = APIRouter(prefix="/links", tags=["links"], redirect_slashes=False)

categories_router = APIRouter(prefix="/categories", tags=["categories"], redirect_slashes=False)


@categories_router.get("")
def list_categories(
    include_all: bool = False, session: Session = Depends(get_session)
) -> list[dict]:
    """Return categories with their link counts.

    By default only categories with at least one link are returned.
    Pass `include_all=true` to include all categories regardless of count.
    """
    counts = count_links_by_category(session)
    return [
        {"category": cat.value, "count": counts[cat]}
        for cat in LinkCategory
        if include_all or counts[cat] > 0
    ]


@router.post("", response_model=LinkResponse, status_code=201)
async def create_link(
    request: LinkRequest, response: Response, session: Session = Depends(get_session)
) -> LinkResponse:
    """Accept a URL, derive its summary and category, persist it, and return it.

    - If *summary* is not provided it is generated via Claude.
    - Category is always assigned by Claude based on the summary.
    - Returns 409 if the URL has already been saved.
    """
    try:
        if request.summary:
            summary = request.summary
            html_title = None
        else:
            html_title, summary = await summarize_url_with_title(request.url)
        category = categorize_link(summary)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to process URL: {exc}") from exc

    existing = get_link_by_url(session, request.url)
    if existing:
        response.status_code = 409
        return _to_response(existing)

    title = request.title or html_title or title_from_url(request.url)
    record = db_create_link(
        session, url=request.url, summary=summary, category=category, title=title
    )
    return _to_response(record)


def _to_response(record: LinkRecord, status_code: int = 201) -> LinkResponse:
    return LinkResponse(
        id=record.id,
        url=record.url,
        title=record.title,
        summary=record.summary,
        category=record.category,
        status=record.status,
        status_changed_at=record.status_changed_at.isoformat() if record.status_changed_at else None,
    )


@router.get("", response_model=list[LinkResponse])
def list_all_links(
    skip: int = 0,
    limit: int = 100,
    category: LinkCategory | None = None,
    status: LinkStatus | None = None,
    session: Session = Depends(get_session),
) -> list[LinkResponse]:
    """Return a paginated list of saved links, optionally filtered by category/status."""
    records = list_links(session, skip=skip, limit=limit, category=category, status=status)
    return [_to_response(r) for r in records]


@router.get("/{link_id}", response_model=LinkResponse)
def get_one_link(link_id: int, session: Session = Depends(get_session)) -> LinkResponse:
    """Fetch a single saved link by ID."""
    record = get_link(session, link_id)
    if not record:
        raise HTTPException(status_code=404, detail="Link not found")
    return _to_response(record)


@router.patch("/{link_id}/status", response_model=LinkResponse)
def set_link_status(
    link_id: int, status: LinkStatus, session: Session = Depends(get_session)
) -> LinkResponse:
    """Update the read status of a link (unread / read)."""
    record = update_link_status(session, link_id, status)
    if not record:
        raise HTTPException(status_code=404, detail="Link not found")
    return _to_response(record)


@router.delete("/{link_id}", status_code=204)
def delete_one_link(link_id: int, session: Session = Depends(get_session)) -> None:
    """Delete a saved link by ID."""
    deleted = db_delete_link(session, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
