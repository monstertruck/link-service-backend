"""SQLModel ORM model for a stored link."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel

from app.api.schemas.links import LinkStatus


class LinkRecord(SQLModel, table=True):
    """Persisted link row in the SQLite database."""

    __tablename__ = "links"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: Optional[str] = Field(default=None)
    category: str
    summary: str
    status: LinkStatus = Field(default=LinkStatus.UNREAD)
    status_changed_at: Optional[datetime] = Field(default=None)
