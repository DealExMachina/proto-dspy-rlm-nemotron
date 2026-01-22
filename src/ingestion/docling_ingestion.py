"""Document ingestion using Docling MCP server."""

import hashlib
import uuid
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from ..models import Document, DocumentSection, DocumentSpan
from ..storage import DatabaseManager
from ..config import get_settings


class DoclingIngestion:
    """
    Ingests documents using Docling MCP server.
    
    Converts PDFs to structured documents with sections and spans.
    """

    def __init__(self, db: DatabaseManager):
        """Initialize ingestion."""
        self.db = db
        self.settings = get_settings()

    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _convert_document_with_docling(self, source: str) -> str:
        """
        Convert document using Docling MCP and return document key.
        
        Note: This is a placeholder. The actual implementation will use
        the MCP tools available at runtime.
        """
        # This will be called through MCP at runtime
        # For now, return a placeholder
        raise NotImplementedError(
            "This method should be called through MCP tools. "
            "Use mcp_docling_convert_document_into_docling_document."
        )

    def _export_docling_to_markdown(self, document_key: str) -> str:
        """
        Export Docling document to markdown.
        
        Note: This is a placeholder. The actual implementation will use
        the MCP tools available at runtime.
        """
        # This will be called through MCP at runtime
        raise NotImplementedError(
            "This method should be called through MCP tools. "
            "Use mcp_docling_export_docling_document_to_markdown."
        )

    def parse_markdown_to_sections(
        self, markdown_text: str, document_id: str
    ) -> List[DocumentSection]:
        """
        Parse markdown text into document sections.
        
        This is a simplified parser that extracts headings and their content.
        """
        sections = []
        lines = markdown_text.split("\n")
        
        current_section = None
        current_text = []
        current_page = 1
        section_counter = 0

        for line in lines:
            # Detect heading levels
            if line.startswith("#"):
                # Save previous section
                if current_section:
                    current_section.text = "\n".join(current_text)
                    sections.append(current_section)
                
                # Parse new heading
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                
                section_counter += 1
                section_id = f"{document_id}_section_{section_counter}"
                
                current_section = DocumentSection(
                    section_id=section_id,
                    document_id=document_id,
                    title=title,
                    level=level,
                    page_start=current_page,
                    text="",
                )
                current_text = []
            else:
                # Add to current section text
                if line.strip():
                    current_text.append(line)
                
                # Simple page break detection (could be improved)
                if "---" in line or "Page" in line:
                    current_page += 1

        # Save last section
        if current_section:
            current_section.text = "\n".join(current_text)
            sections.append(current_section)

        return sections

    def create_spans_from_sections(
        self, sections: List[DocumentSection]
    ) -> List[DocumentSpan]:
        """
        Create text spans from sections for citation purposes.
        
        Breaks sections into smaller chunks for granular citations.
        """
        spans = []
        span_counter = 0

        for section in sections:
            # Split section text into paragraphs
            paragraphs = [p.strip() for p in section.text.split("\n\n") if p.strip()]
            
            char_offset = 0
            for para in paragraphs:
                span_counter += 1
                span_id = f"{section.document_id}_span_{span_counter}"
                
                span = DocumentSpan(
                    span_id=span_id,
                    document_id=section.document_id,
                    section_id=section.section_id,
                    page_number=section.page_start,
                    start_char=char_offset,
                    end_char=char_offset + len(para),
                    text=para,
                )
                spans.append(span)
                char_offset += len(para) + 2  # Account for paragraph break

        return spans

    def ingest_document(
        self,
        file_path: Path,
        isin: str = None,
        document_type: str = "prospectus",
    ) -> Tuple[Document, List[DocumentSection], List[DocumentSpan]]:
        """
        Ingest a document from a file path.
        
        Returns:
            Tuple of (document, sections, spans)
        """
        # Compute checksum
        checksum = self._compute_checksum(file_path)
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Note: In actual usage, we would call Docling MCP tools here
        # For now, we'll create a simple placeholder
        # The user will need to integrate the MCP calls in the CLI
        
        # Create document record
        document = Document(
            document_id=document_id,
            isin=isin,
            document_type=document_type,
            version="1",
            checksum=checksum,
            source_path=str(file_path),
            total_pages=0,  # Will be updated after processing
            processed=False,
        )
        
        # Store in database
        self.db.insert_document(document)
        
        return document, [], []

    def process_docling_document(
        self, document_key: str, document_id: str, isin: str = None
    ) -> Tuple[Document, List[DocumentSection], List[DocumentSpan]]:
        """
        Process a document that has already been converted by Docling.
        
        This should be called after using MCP tools to convert the document.
        """
        # Export to markdown
        # In practice, this will be called via MCP
        # markdown_text = self._export_docling_to_markdown(document_key)
        
        # For now, return empty structures
        # The CLI will handle the actual MCP integration
        sections = []
        spans = []
        
        return None, sections, spans
