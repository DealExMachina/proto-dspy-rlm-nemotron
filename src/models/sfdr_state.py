"""SFDR state models following the PRD specification."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class Citation(BaseModel):
    """Citation pointing to source evidence."""

    document_id: str
    page_number: int
    span_id: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    text_snippet: str


class FieldValue(BaseModel):
    """A field value with confidence and citations."""

    value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)


class DNSHCoverage(str, Enum):
    """DNSH coverage levels."""

    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class SustainableInvestmentDefinition(BaseModel):
    """Sustainable investment definition extracted from documents."""

    present: bool
    text: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)


class DNSHField(BaseModel):
    """Do No Significant Harm field."""

    present: bool
    coverage: DNSHCoverage = DNSHCoverage.NONE
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)


class PAIField(BaseModel):
    """Principal Adverse Impact field."""

    mandatory_coverage_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)


class SFDRState(BaseModel):
    """
    Canonical SFDR state for a fund at a specific document version.
    
    This is the core output of Iteration 1.
    Each field stores value + confidence + citations.
    """

    model_config = ConfigDict(use_enum_values=True)

    state_id: str
    fund_isin: str
    doc_version: str
    claimed_article: Optional[str] = None  # Article 6, 8, or 9
    
    # Core SFDR fields
    sustainable_investment_definition: Optional[SustainableInvestmentDefinition] = None
    dnsh: Optional[DNSHField] = None
    pai: Optional[PAIField] = None
    
    # Metadata
    missing_fields: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[str] = Field(default_factory=list)  # list of document_ids
