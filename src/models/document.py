"""Document models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentSpan(BaseModel):
    """A span of text within a document with location information."""

    span_id: str
    document_id: str
    section_id: Optional[str] = None
    page_number: int
    start_char: int
    end_char: int
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentSection(BaseModel):
    """A logical section within a document."""

    section_id: str
    document_id: str
    title: str
    level: int  # heading level
    page_start: int
    page_end: Optional[int] = None
    text: str
    parent_section_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """A regulatory document (prospectus, annual report, SFDR annex)."""

    document_id: str
    isin: Optional[str] = None
    document_type: str  # "prospectus", "annual_report", "sfdr_annex"
    version: str = "1"
    checksum: str
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    total_pages: int
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
