from pydantic import BaseModel
from typing import Optional
from enum import Enum

class Link(BaseModel):
    """Pydantic model for a stored link."""

    url: str
    title: str
    category: str
    summary: Optional[str] = None


class LinkCategory(str, Enum):
    """Enumeration of possible link categories."""

    CHRISTIANITY = "christianity"
    YOUTUBE = "youtube"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    TECH = "tech"
    WORKOUT = "workout"
    PF = "personal_finance"
    INVESTING = "investing"
    PARENTING = "parenting"
    SCIENCE = "science"
    TRAVEL = "travel"
    COOKING = "cooking"
    SHOPPING = "shopping"
    OTHER = "other"

