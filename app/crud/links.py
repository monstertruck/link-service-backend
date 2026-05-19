"""CRUD operations for LinkRecord."""

from typing import Optional

from sqlmodel import Session, select

from app.api.schemas.links import LinkCategory
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


def list_links(session: Session, skip: int = 0, limit: int = 100) -> list[LinkRecord]:
    """Return a paginated list of all saved links."""
    statement = select(LinkRecord).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def delete_link(session: Session, link_id: int) -> bool:
    """Delete the link with the given primary key. Returns True if it existed."""
    record = session.get(LinkRecord, link_id)
    if not record:
        return False
    session.delete(record)
    session.commit()
    return True
