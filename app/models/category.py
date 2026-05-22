"""SQLModel ORM model for a stored category."""

from sqlmodel import Field, SQLModel


class CategoryRecord(SQLModel, table=True):
    """Persisted category row in the SQLite database."""

    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
