"""BM25 retrieval over document sections and spans."""

from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi

from ..storage import DatabaseManager


class BM25Retriever:
    """BM25-based retrieval over document sections."""

    def __init__(self, db: DatabaseManager):
        """Initialize retriever."""
        self.db = db
        self.sections_by_doc: Dict[str, List[Dict[str, Any]]] = {}
        self.bm25_by_doc: Dict[str, BM25Okapi] = {}

    def index_document(self, document_id: str):
        """Index a document's sections for retrieval."""
        sections = self.db.get_sections_by_document(document_id)
        
        if not sections:
            return
        
        # Store sections
        self.sections_by_doc[document_id] = sections
        
        # Tokenize section texts (simple whitespace tokenization)
        tokenized_corpus = [
            section["text"].lower().split() for section in sections
        ]
        
        # Build BM25 index
        self.bm25_by_doc[document_id] = BM25Okapi(tokenized_corpus)

    def retrieve(
        self, document_id: str, query: str, top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve top-k most relevant sections for a query.
        
        Args:
            document_id: Document to search in
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (section, score) tuples
        """
        if document_id not in self.bm25_by_doc:
            self.index_document(document_id)
        
        if document_id not in self.bm25_by_doc:
            return []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_by_doc[document_id].get_scores(tokenized_query)
        
        # Get top-k results
        sections = self.sections_by_doc[document_id]
        scored_sections = list(zip(sections, scores))
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        
        return scored_sections[:top_k]

    def retrieve_by_keywords(
        self, document_id: str, keywords: List[str], top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve sections containing specific keywords.
        
        Args:
            document_id: Document to search in
            keywords: List of keywords to search for
            top_k: Number of results to return
            
        Returns:
            List of (section, score) tuples
        """
        query = " ".join(keywords)
        return self.retrieve(document_id, query, top_k)
