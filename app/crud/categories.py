"""CRUD operations for CategoryRecord."""

from sqlmodel import Session, select

from app.models.category import CategoryRecord


def list_categories(session: Session) -> list[CategoryRecord]:
    """Return all categories ordered by name."""
    return list(session.exec(select(CategoryRecord).order_by(CategoryRecord.name)).all())


def get_category_by_name(session: Session, name: str) -> CategoryRecord | None:
    """Return the category with the given name, or None."""
    return session.exec(select(CategoryRecord).where(CategoryRecord.name == name)).first()


def create_category(session: Session, name: str) -> CategoryRecord:
    """Persist a new category. Raises ValueError if name already exists."""
    existing = get_category_by_name(session, name)
    if existing:
        raise ValueError(f"Category already exists: {name}")
    record = CategoryRecord(name=name)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def seed_categories(session: Session, names: list[str]) -> None:
    """Insert categories that do not already exist (idempotent)."""
    for name in names:
        if not get_category_by_name(session, name):
            session.add(CategoryRecord(name=name))
    session.commit()
