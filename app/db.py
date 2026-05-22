"""Database engine and session management."""

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///links.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_tables() -> None:
    """Create all SQLModel tables. Called once at app startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
