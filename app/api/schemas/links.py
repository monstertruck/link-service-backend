from pydantic import BaseModel
from typing import Optional
from enum import Enum


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


class Link(BaseModel):
    """Pydantic model for a stored link."""

    url: str
    title: Optional[str] = None
    category: LinkCategory
    summary: Optional[str] = None


class LinkRequest(BaseModel):
    """Request body for creating a link."""

    url: str
    title: Optional[str] = None
    summary: Optional[str] = None


class LinkResponse(BaseModel):
    """Response body returned after processing a link."""

    id: Optional[int] = None
    url: str
    title: Optional[str] = None
    category: LinkCategory
    summary: str

