"""DuckDB database manager."""

import duckdb
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..models import Document, DocumentSection, DocumentSpan, SFDRState
from ..config import get_settings


class DatabaseManager:
    """Manages DuckDB connection and operations."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager."""
        self.settings = get_settings()
        self.db_path = db_path or self.settings.duckdb_path_obj
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Connect to DuckDB database."""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_schema(self):
        """Initialize database schema."""
        conn = self.connect()

        # Documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id VARCHAR PRIMARY KEY,
                isin VARCHAR,
                document_type VARCHAR NOT NULL,
                version VARCHAR NOT NULL,
                checksum VARCHAR NOT NULL,
                source_url VARCHAR,
                source_path VARCHAR,
                total_pages INTEGER NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                metadata JSON
            )
        """)

        # Sections table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                section_id VARCHAR PRIMARY KEY,
                document_id VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                level INTEGER NOT NULL,
                page_start INTEGER NOT NULL,
                page_end INTEGER,
                text TEXT NOT NULL,
                parent_section_id VARCHAR,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(document_id)
            )
        """)

        # Spans table (for citations)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                span_id VARCHAR PRIMARY KEY,
                document_id VARCHAR NOT NULL,
                section_id VARCHAR,
                page_number INTEGER NOT NULL,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(document_id),
                FOREIGN KEY (section_id) REFERENCES sections(section_id)
            )
        """)

        # SFDR States table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sfdr_states (
                state_id VARCHAR PRIMARY KEY,
                fund_isin VARCHAR NOT NULL,
                doc_version VARCHAR NOT NULL,
                claimed_article VARCHAR,
                sustainable_investment_definition JSON,
                dnsh JSON,
                pai JSON,
                missing_fields JSON,
                confidence DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL,
                documents JSON
            )
        """)

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_isin ON documents(isin)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sections_document ON sections(document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_document ON spans(document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sfdr_states_isin ON sfdr_states(fund_isin)")

        conn.commit()

    def insert_document(self, document: Document):
        """Insert a document into the database."""
        conn = self.connect()
        conn.execute("""
            INSERT INTO documents 
            (document_id, isin, document_type, version, checksum, source_url, source_path, 
             total_pages, processed, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            document.document_id,
            document.isin,
            document.document_type,
            document.version,
            document.checksum,
            document.source_url,
            document.source_path,
            document.total_pages,
            document.processed,
            document.created_at,
            json.dumps(document.metadata),
        ])
        conn.commit()

    def insert_section(self, section: DocumentSection):
        """Insert a section into the database."""
        conn = self.connect()
        conn.execute("""
            INSERT INTO sections 
            (section_id, document_id, title, level, page_start, page_end, text, 
             parent_section_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            section.section_id,
            section.document_id,
            section.title,
            section.level,
            section.page_start,
            section.page_end,
            section.text,
            section.parent_section_id,
            section.created_at,
        ])
        conn.commit()

    def insert_span(self, span: DocumentSpan):
        """Insert a span into the database."""
        conn = self.connect()
        conn.execute("""
            INSERT INTO spans 
            (span_id, document_id, section_id, page_number, start_char, end_char, 
             text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            span.span_id,
            span.document_id,
            span.section_id,
            span.page_number,
            span.start_char,
            span.end_char,
            span.text,
            span.created_at,
        ])
        conn.commit()

    def insert_sfdr_state(self, state: SFDRState):
        """Insert an SFDR state into the database."""
        conn = self.connect()
        conn.execute("""
            INSERT INTO sfdr_states 
            (state_id, fund_isin, doc_version, claimed_article, 
             sustainable_investment_definition, dnsh, pai, missing_fields, 
             confidence, created_at, documents)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            state.state_id,
            state.fund_isin,
            state.doc_version,
            state.claimed_article,
            json.dumps(state.sustainable_investment_definition.model_dump() if state.sustainable_investment_definition else None),
            json.dumps(state.dnsh.model_dump() if state.dnsh else None),
            json.dumps(state.pai.model_dump() if state.pai else None),
            json.dumps(state.missing_fields),
            state.confidence,
            state.created_at,
            json.dumps(state.documents),
        ])
        conn.commit()

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        conn = self.connect()
        result = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?", [document_id]
        ).fetchone()
        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None

    def get_sections_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all sections for a document."""
        conn = self.connect()
        results = conn.execute(
            "SELECT * FROM sections WHERE document_id = ? ORDER BY page_start, level",
            [document_id]
        ).fetchall()
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]

    def get_sfdr_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Get an SFDR state by ID."""
        conn = self.connect()
        result = conn.execute(
            "SELECT * FROM sfdr_states WHERE state_id = ?", [state_id]
        ).fetchone()
        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None
