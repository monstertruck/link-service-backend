"""FastAPI router for link creation and processing."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

logger = logging.getLogger(__name__)

from app.api.schemas.links import CategoryCreate, CategoryResponse, LinkCategory, LinkRequest, LinkResponse, LinkStatus, LinkUpdate
from app.crud.categories import create_category, delete_category, get_category_by_name, list_categories, rename_category
from app.crud.links import count_links_by_category
from app.crud.links import create_link as db_create_link
from app.crud.links import delete_link as db_delete_link
from app.crud.links import get_link, get_link_by_url, list_links, update_link, update_link_status
from app.models.link import LinkRecord
from app.db import get_session
from lib.llm import categorize_link, summarize_url_with_title
from lib.utils import is_youtube_url, title_from_url

router = APIRouter(prefix="/links", tags=["links"], redirect_slashes=False)

categories_router = APIRouter(prefix="/categories", tags=["categories"], redirect_slashes=False)


@categories_router.get("")
def get_categories(
    include_all: bool = False, session: Session = Depends(get_session)
) -> list[dict]:
    """Return categories with their link counts.

    By default only categories with at least one link are returned.
    Pass `include_all=true` to include all categories regardless of count.
    """
    counts = count_links_by_category(session)
    all_categories = list_categories(session)
    return [
        {"category": cat.name, "count": counts.get(cat.name, 0)}
        for cat in all_categories
        if include_all or counts.get(cat.name, 0) > 0
    ]


@categories_router.patch("/{name}", response_model=CategoryResponse)
def update_category(name: str, body: CategoryCreate, session: Session = Depends(get_session)) -> CategoryResponse:
    """Rename a category."""
    new_name = body.name.strip().lower()
    if not new_name:
        raise HTTPException(status_code=422, detail="Category name must not be empty")
    if get_category_by_name(session, new_name):
        raise HTTPException(status_code=409, detail=f"Category already exists: {new_name}")
    record = rename_category(session, name.strip().lower(), new_name)
    if not record:
        raise HTTPException(status_code=404, detail=f"Category not found: {name}")
    return CategoryResponse(name=record.name)


@categories_router.delete("/{name}", status_code=204)
def remove_category(name: str, session: Session = Depends(get_session)) -> None:
    """Delete a category by name."""
    deleted = delete_category(session, name.strip().lower())
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Category not found: {name}")


@categories_router.post("", response_model=CategoryResponse, status_code=201)
def add_category(
    body: CategoryCreate, session: Session = Depends(get_session)
) -> CategoryResponse:
    """Create a new category."""
    name = body.name.strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="Category name must not be empty")
    existing = get_category_by_name(session, name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Category already exists: {name}")
    record = create_category(session, name)
    return CategoryResponse(name=record.name)


@router.post("", response_model=LinkResponse, status_code=201)
async def create_link(
    request: LinkRequest, response: Response, session: Session = Depends(get_session)
) -> LinkResponse:
    """Accept a URL, derive its summary and category, persist it, and return it.

    - If *summary* is not provided it is generated via Claude.
    - Category is always assigned by Claude based on the summary.
    - Returns 409 if the URL has already been saved.
    """
    logger.info("Creating link url=%s", request.url)
    try:
        if is_youtube_url(request.url) and not request.summary:
            html_title, _ = await summarize_url_with_title(request.url)
            # Use the page title as the summary; skip Claude entirely.
            summary = request.title or html_title or title_from_url(request.url)
            category = LinkCategory.YOUTUBE
        elif request.summary:
            summary = request.summary
            html_title = None
            category = categorize_link(summary)
        else:
            html_title, summary = await summarize_url_with_title(request.url)
            category = categorize_link(summary)
    except RuntimeError as exc:
        logger.error("Service error for url=%s: %s", request.url, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error processing url=%s", request.url)
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
    category: str | None = None,
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


@router.patch("/{link_id}", response_model=LinkResponse)
def patch_link(
    link_id: int, body: LinkUpdate, session: Session = Depends(get_session)
) -> LinkResponse:
    """Update a link's category and/or status."""
    if body.category is not None:
        category_name = body.category.strip().lower()
        if not get_category_by_name(session, category_name):
            raise HTTPException(status_code=422, detail=f"Unknown category: {category_name}")
        body = LinkUpdate(category=category_name, status=body.status)
    record = update_link(session, link_id, body.category, body.status)
    if not record:
        raise HTTPException(status_code=404, detail="Link not found")
    return _to_response(record)


@router.delete("/{link_id}", status_code=204)
def delete_one_link(link_id: int, session: Session = Depends(get_session)) -> None:
    """Delete a saved link by ID."""
    deleted = db_delete_link(session, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
