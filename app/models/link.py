"""SQLModel ORM model for a stored link."""

from typing import Optional

from sqlmodel import Field, SQLModel

from app.api.schemas.links import LinkCategory


class LinkRecord(SQLModel, table=True):
    """Persisted link row in the SQLite database."""

    __tablename__ = "links"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: Optional[str] = Field(default=None)
    category: LinkCategory
    summary: str
