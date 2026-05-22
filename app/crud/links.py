"""CRUD operations for LinkRecord."""

from typing import Optional

from sqlmodel import Session, func, select

from app.api.schemas.links import LinkCategory, LinkStatus
from app.models.link import LinkRecord


def create_link(
    session: Session,
    url: str,
    summary: str,
    category: LinkCategory,
    title: Optional[str] = None,
) -> LinkRecord:
    """Persist a new link. Raises ValueError if the URL already exists."""
    existing = get_link_by_url(session, url)
    if existing:
        raise ValueError(f"URL already saved: {url}")

    record = LinkRecord(url=url, title=title, summary=summary, category=category)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_link(session: Session, link_id: int) -> Optional[LinkRecord]:
    """Return the link with the given primary key, or None."""
    return session.get(LinkRecord, link_id)


def get_link_by_url(session: Session, url: str) -> Optional[LinkRecord]:
    """Return the link with the given URL, or None."""
    statement = select(LinkRecord).where(LinkRecord.url == url)
    return session.exec(statement).first()


def list_links(
    session: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[LinkCategory] = None,
    status: Optional[LinkStatus] = None,
) -> list[LinkRecord]:
    """Return a paginated list of saved links, optionally filtered by category/status."""
    statement = select(LinkRecord)
    if category is not None:
        statement = statement.where(LinkRecord.category == category)
    if status is not None:
        statement = statement.where(LinkRecord.status == status)
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_link_status(session: Session, link_id: int, status: LinkStatus) -> Optional[LinkRecord]:
    """Update the status of a link and record the time of change. Returns None if not found."""
    from datetime import datetime, timezone
    record = session.get(LinkRecord, link_id)
    if not record:
        return None
    record.status = status
    record.status_changed_at = datetime.now(timezone.utc)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def count_links_by_category(session: Session) -> dict[LinkCategory, int]:
    """Return a mapping of every LinkCategory to its saved link count (0 if none)."""
    statement = select(LinkRecord.category, func.count(LinkRecord.id)).group_by(LinkRecord.category)
    rows = session.exec(statement).all()
    counts: dict[LinkCategory, int] = {cat: 0 for cat in LinkCategory}
    for category, count in rows:
        counts[LinkCategory(category)] = count
    return counts


def delete_link(session: Session, link_id: int) -> bool:
    """Delete the link with the given primary key. Returns True if it existed."""
    record = session.get(LinkRecord, link_id)
    if not record:
        return False
    session.delete(record)
    session.commit()
    return True
