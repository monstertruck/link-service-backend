from pydantic import BaseModel

class Link(BaseModel):
    """Pydantic model for a stored link."""

    url: str
    title: str
    category: str
