"""RLM Controller - Recursive goal-driven regulatory extraction."""

import uuid
import dspy
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models import (
    SFDRState,
    SustainableInvestmentDefinition,
    DNSHField,
    DNSHCoverage,
    PAIField,
    Citation,
)
from ..storage import DatabaseManager
from ..retrieval import BM25Retriever
from ..worker import LLMWorker
from .dspy_signatures import (
    ClassifyArticle,
    ExtractDefinition,
    ExtractDNSH,
    ExtractPAI,
)


class DSPyLLMWrapper(dspy.LM):
    """Wrapper to make our LLM workers compatible with DSPy."""

    def __init__(self, worker: LLMWorker):
        """Initialize wrapper."""
        self.worker = worker
        super().__init__(model="custom")

    def __call__(self, prompt: str = None, messages: List[Dict] = None, **kwargs) -> List[str]:
        """Generate response."""
        if messages:
            # Extract last user message
            user_messages = [m for m in messages if m.get("role") == "user"]
            prompt = user_messages[-1]["content"] if user_messages else ""
            
        if not prompt:
            return [""]

        response = self.worker.generate(prompt=prompt, temperature=0.1, max_tokens=1000)
        return [response]

    def inspect_history(self, n: int = 1):
        """Return history (not implemented for now)."""
        return []


class RLMController:
    """
    Recursive Language Model Controller.
    
    Goal-driven controller that fills SFDR state field by field using:
    1. Retrieval to find relevant sections
    2. LLM worker to extract structured information
    3. DSPy signatures for structured outputs
    """

    def __init__(
        self,
        db: DatabaseManager,
        retriever: BM25Retriever,
        worker: LLMWorker,
    ):
        """Initialize RLM controller."""
        self.db = db
        self.retriever = retriever
        self.worker = worker
        
        # Configure DSPy with our LLM
        dspy.settings.configure(lm=DSPyLLMWrapper(worker))

    def extract_article_classification(
        self, document_id: str
    ) -> tuple[Optional[str], float]:
        """
        Extract SFDR article classification (6, 8, or 9).
        
        Returns:
            Tuple of (article, confidence)
        """
        # Retrieve relevant sections
        query = "SFDR article 6 8 9 classification disclosure"
        results = self.retriever.retrieve(document_id, query, top_k=3)
        
        if not results:
            return None, 0.0
        
        # Build context
        context = "\n\n".join([section["text"][:500] for section, _ in results])
        
        # Use DSPy to extract
        try:
            predictor = dspy.Predict(ClassifyArticle)
            result = predictor(context=context)
            
            article = result.article
            confidence = float(result.confidence) if hasattr(result, "confidence") else 0.5
            
            return article, confidence
        except Exception as e:
            print(f"Error classifying article: {e}")
            return None, 0.0

    def extract_sustainable_investment_definition(
        self, document_id: str
    ) -> Optional[SustainableInvestmentDefinition]:
        """Extract sustainable investment definition."""
        # Retrieve relevant sections
        query = "sustainable investment definition environmentally socially"
        results = self.retriever.retrieve(document_id, query, top_k=5)
        
        if not results:
            return None
        
        # Build context
        context = "\n\n".join([
            f"[Page {section['page_start']}]\n{section['text'][:800]}"
            for section, _ in results[:3]
        ])
        
        # Use DSPy to extract
        try:
            predictor = dspy.Predict(ExtractDefinition)
            result = predictor(context=context)
            
            present = str(result.definition_present).lower() == "true"
            definition_text = result.definition_text if present else None
            confidence = float(result.confidence) if hasattr(result, "confidence") else 0.5
            page_number = int(result.page_number) if hasattr(result, "page_number") else results[0][0]["page_start"]
            
            # Create citations
            citations = []
            for section, _ in results[:1]:
                citations.append(Citation(
                    document_id=document_id,
                    page_number=section["page_start"],
                    text_snippet=section["text"][:200],
                ))
            
            return SustainableInvestmentDefinition(
                present=present,
                text=definition_text,
                confidence=confidence,
                citations=citations,
            )
        except Exception as e:
            print(f"Error extracting definition: {e}")
            return None

    def extract_dnsh(self, document_id: str) -> Optional[DNSHField]:
        """Extract DNSH information."""
        # Retrieve relevant sections
        query = "do no significant harm DNSH environmental objectives"
        results = self.retriever.retrieve(document_id, query, top_k=5)
        
        if not results:
            return DNSHField(present=False, coverage=DNSHCoverage.NONE, confidence=0.5)
        
        # Build context
        context = "\n\n".join([
            f"[Page {section['page_start']}]\n{section['text'][:800]}"
            for section, _ in results[:3]
        ])
        
        # Use DSPy to extract
        try:
            predictor = dspy.Predict(ExtractDNSH)
            result = predictor(context=context)
            
            present = str(result.dnsh_present).lower() == "true"
            coverage_str = str(result.coverage).lower()
            confidence = float(result.confidence) if hasattr(result, "confidence") else 0.5
            
            # Map coverage string to enum
            coverage_map = {
                "none": DNSHCoverage.NONE,
                "partial": DNSHCoverage.PARTIAL,
                "full": DNSHCoverage.FULL,
            }
            coverage = coverage_map.get(coverage_str, DNSHCoverage.NONE)
            
            # Create citations
            citations = []
            for section, _ in results[:1]:
                citations.append(Citation(
                    document_id=document_id,
                    page_number=section["page_start"],
                    text_snippet=section["text"][:200],
                ))
            
            return DNSHField(
                present=present,
                coverage=coverage,
                confidence=confidence,
                citations=citations,
            )
        except Exception as e:
            print(f"Error extracting DNSH: {e}")
            return DNSHField(present=False, coverage=DNSHCoverage.NONE, confidence=0.0)

    def extract_pai(self, document_id: str) -> Optional[PAIField]:
        """Extract PAI information."""
        # Retrieve relevant sections
        query = "principal adverse impacts PAI sustainability indicators"
        results = self.retriever.retrieve(document_id, query, top_k=5)
        
        if not results:
            return None
        
        # Build context
        context = "\n\n".join([
            f"[Page {section['page_start']}]\n{section['text'][:800]}"
            for section, _ in results[:3]
        ])
        
        # Use DSPy to extract
        try:
            predictor = dspy.Predict(ExtractPAI)
            result = predictor(context=context)
            
            ratio_str = str(result.mandatory_coverage_ratio)
            ratio = float(ratio_str) if ratio_str and ratio_str != "None" else None
            confidence = float(result.confidence) if hasattr(result, "confidence") else 0.5
            
            # Create citations
            citations = []
            for section, _ in results[:1]:
                citations.append(Citation(
                    document_id=document_id,
                    page_number=section["page_start"],
                    text_snippet=section["text"][:200],
                ))
            
            return PAIField(
                mandatory_coverage_ratio=ratio,
                confidence=confidence,
                citations=citations,
            )
        except Exception as e:
            print(f"Error extracting PAI: {e}")
            return None

    def build_sfdr_state(
        self, document_id: str, isin: str, doc_version: str = "1"
    ) -> SFDRState:
        """
        Build complete SFDR state for a document.
        
        This is the main entry point for Iteration 1.
        """
        # Extract each field
        article, article_conf = self.extract_article_classification(document_id)
        definition = self.extract_sustainable_investment_definition(document_id)
        dnsh = self.extract_dnsh(document_id)
        pai = self.extract_pai(document_id)
        
        # Track missing fields
        missing_fields = []
        if not article:
            missing_fields.append("claimed_article")
        if not definition or not definition.present:
            missing_fields.append("sustainable_investment_definition")
        if not dnsh or not dnsh.present:
            missing_fields.append("dnsh")
        if not pai or pai.mandatory_coverage_ratio is None:
            missing_fields.append("pai")
        
        # Compute overall confidence
        confidences = [article_conf]
        if definition:
            confidences.append(definition.confidence)
        if dnsh:
            confidences.append(dnsh.confidence)
        if pai:
            confidences.append(pai.confidence)
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Create state
        state = SFDRState(
            state_id=str(uuid.uuid4()),
            fund_isin=isin,
            doc_version=doc_version,
            claimed_article=article,
            sustainable_investment_definition=definition,
            dnsh=dnsh,
            pai=pai,
            missing_fields=missing_fields,
            confidence=overall_confidence,
            documents=[document_id],
        )
        
        return state
