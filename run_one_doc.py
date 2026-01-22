#!/usr/bin/env python3
"""
CLI for processing a single document (Iteration 1).

Usage:
    python run_one_doc.py path/to/document.pdf --isin LU1234567890
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.config import get_settings
from src.storage import DatabaseManager
from src.ingestion import DoclingIngestion
from src.retrieval import BM25Retriever
from src.controller import RLMController
from src.worker import get_worker

console = Console()


@click.command()
@click.argument("document_path", type=click.Path(exists=True))
@click.option("--isin", required=True, help="Fund ISIN")
@click.option("--doc-type", default="prospectus", help="Document type")
@click.option("--use-ollama", is_flag=True, help="Use Ollama instead of Nemotron")
@click.option("--output", default="sfdr_state.json", help="Output file path")
def main(document_path: str, isin: str, doc_type: str, use_ollama: bool, output: str):
    """
    Process a single regulatory document and extract SFDR state.
    
    This is the main CLI for Iteration 1 of the project.
    """
    console.print("\n[bold blue]Continuous Regulatory Intelligence - Iteration 1[/bold blue]")
    console.print(f"[dim]Processing: {document_path}[/dim]\n")

    # Initialize components
    settings = get_settings()
    db = DatabaseManager()
    db.init_schema()
    
    retriever = BM25Retriever(db)
    worker = get_worker(use_ollama=use_ollama)
    controller = RLMController(db, retriever, worker)
    ingestion = DoclingIngestion(db)

    # Step 1: Convert document with Docling
    console.print("[yellow]Step 1:[/yellow] Converting document with Docling...")
    console.print("[dim]Note: You need to manually call MCP tools for now:[/dim]")
    console.print("[dim]  mcp_docling_convert_document_into_docling_document[/dim]")
    console.print("[dim]  mcp_docling_export_docling_document_to_markdown[/dim]\n")
    
    # For now, we'll simulate by creating a simple document entry
    # In production, this would integrate with Docling MCP
    doc_path = Path(document_path)
    
    # This is a placeholder - real implementation would use Docling MCP
    console.print("[red]⚠ Docling integration required - see README[/red]")
    console.print("[dim]For now, creating placeholder document entry...[/dim]\n")
    
    document, sections, spans = ingestion.ingest_document(
        file_path=doc_path,
        isin=isin,
        document_type=doc_type,
    )

    # Step 2: Index document for retrieval
    console.print("[yellow]Step 2:[/yellow] Indexing document for retrieval...")
    if sections:
        for section in sections:
            db.insert_section(section)
        for span in spans:
            db.insert_span(span)
        retriever.index_document(document.document_id)
        console.print("[green]✓[/green] Document indexed\n")
    else:
        console.print("[red]✗[/red] No sections found - Docling integration needed\n")
        console.print("[yellow]To proceed, you need to:[/yellow]")
        console.print("1. Use Docling MCP to convert the PDF")
        console.print("2. Export to markdown")
        console.print("3. Parse sections and spans")
        console.print("4. Then re-run this script\n")
        return

    # Step 3: Extract SFDR state using RLM controller
    console.print("[yellow]Step 3:[/yellow] Extracting SFDR state with RLM controller...")
    console.print(f"[dim]Using: {'Ollama (Qwen3:8b)' if use_ollama else 'Nemotron (Koyeb H100)'}[/dim]\n")
    
    state = controller.build_sfdr_state(
        document_id=document.document_id,
        isin=isin,
        doc_version="1",
    )

    # Step 4: Save to database
    console.print("[yellow]Step 4:[/yellow] Saving SFDR state to database...")
    db.insert_sfdr_state(state)
    console.print("[green]✓[/green] State saved\n")

    # Step 5: Export to JSON
    console.print("[yellow]Step 5:[/yellow] Exporting results...")
    output_data = {
        "state": state.model_dump(),
        "metadata": {
            "document_id": document.document_id,
            "isin": isin,
            "document_type": doc_type,
            "llm": "ollama" if use_ollama else "nemotron",
        }
    }
    
    with open(output, "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    
    console.print(f"[green]✓[/green] Results exported to {output}\n")

    # Display summary
    display_summary(state)

    db.close()


def display_summary(state):
    """Display a summary of the extracted SFDR state."""
    console.print("[bold]Extraction Summary[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Confidence", justify="right")
    
    # Article
    article_status = "✓" if state.claimed_article else "✗"
    table.add_row(
        "SFDR Article",
        f"{article_status} {state.claimed_article or 'Not found'}",
        f"{state.confidence:.2f}"
    )
    
    # Definition
    if state.sustainable_investment_definition:
        def_status = "✓" if state.sustainable_investment_definition.present else "✗"
        def_text = state.sustainable_investment_definition.text or "Not found"
        def_conf = state.sustainable_investment_definition.confidence
        table.add_row(
            "Sustainable Investment Definition",
            f"{def_status} {def_text[:50]}...",
            f"{def_conf:.2f}"
        )
    
    # DNSH
    if state.dnsh:
        dnsh_status = "✓" if state.dnsh.present else "✗"
        table.add_row(
            "DNSH",
            f"{dnsh_status} Coverage: {state.dnsh.coverage.value}",
            f"{state.dnsh.confidence:.2f}"
        )
    
    # PAI
    if state.pai and state.pai.mandatory_coverage_ratio is not None:
        table.add_row(
            "PAI Coverage",
            f"✓ {state.pai.mandatory_coverage_ratio:.1%}",
            f"{state.pai.confidence:.2f}"
        )
    
    console.print(table)
    console.print()
    
    if state.missing_fields:
        console.print("[yellow]Missing fields:[/yellow]")
        for field in state.missing_fields:
            console.print(f"  - {field}")
        console.print()


if __name__ == "__main__":
    main()
