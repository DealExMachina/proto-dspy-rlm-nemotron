#!/usr/bin/env python3
"""
Test full RLM pipeline with Amundi Obligations Vertes SFDR document.

This tests:
1. Document ingestion (markdown parsing)
2. Database storage
3. BM25 retrieval
4. RLM controller with real Ollama
5. SFDR state extraction
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.storage import DatabaseManager
from src.ingestion import DoclingIngestion
from src.retrieval import BM25Retriever
from src.controller import RLMController
from src.worker import get_worker

console = Console()


# Docling markdown output (from MCP conversion)
DOCLING_MARKDOWN = """Publication sur le site internet d'informations relatives au produit conformément à l'article 10(1) du Règlement SFDR pour les fonds classés article 9 au sens dudit Règlement

Product Nom: SG AMUNDI OBLIGATIONS VERTES

Legal entity identifier: 969500TKG1TYT8BKXA62

## Absence de préjudice important pour l'objectif d'investissement durable

Pour s'assurer que les investissements durables ne causent pas de préjudice important (principe du « DNSH » ou Do Not Significantly Harm »), Amundi utilise deux filtres :

- le premier filtre « DNSH » repose sur le suivi d'indicateurs obligatoires des Principales Incidences Négatives de l'Annexe 1, Tableau 1 des RTS
- Amundi prend déjà en compte des Principales Incidences Négatives spécifiques dans sa politique d'exclusions

Les investissements durables sont alignés sur les principes directeurs de l'OCDE à l'intention des entreprises multinationales et sur les principes directeurs des Nations unies relatifs aux droits de l'Homme.

## Objectif d'investissement durable du produit financier

L'objectif d'investissement durable du compartiment maître consiste à investir dans des obligations vertes dites "green bonds" de qualité investment grade répondant aux critères et aux lignes directrices des Green Bond Principles tels que publiés par l'International Capital Market Association.

L'impact environnemental est apprécié en fonction des estimations des émissions de gaz à effet de serre évitées avec comme indicateur les tonnes d'émissions d'équivalent CO2 (tC02e) évitées.

## Stratégie d'Investissement

La stratégie consiste à offrir une performance liée à l'évolution du marché des obligations vertes dites « Green bonds ». L'univers d'investissement du compartiment maître est constitué des obligations vertes respectant les Green Bonds Principles.

Le compartiment maître investit 100% de l'actif net hors liquidités dans tous types d'obligations vertes négociés sur un marché réglementé, émis par des Etats, des organismes supra-nationaux, des entreprises privées ou publiques.

Le processus d'investissement identifie les meilleures opportunités en termes de perspectives financières et de caractéristiques ESG, en particulier environnementales.
"""


def main():
    """Test full pipeline."""
    console.print("\n[bold blue]🧪 Testing Full RLM Pipeline with Real Document[/bold blue]")
    console.print("[dim]Fund: Amundi Obligations Vertes (FR0050000829)[/dim]")
    console.print("[dim]Document: SFDR Website Disclosure (8 pages)[/dim]\n")
    
    # Step 1: Initialize components
    console.print("[yellow]Step 1:[/yellow] Initializing components...")
    
    db = DatabaseManager(db_path=Path("data/test_pipeline.duckdb"))
    db.init_schema()
    console.print("  ✅ Database initialized")
    
    ingestion = DoclingIngestion(db)
    console.print("  ✅ Ingestion ready")
    
    retriever = BM25Retriever(db)
    console.print("  ✅ Retriever ready")
    
    worker = get_worker(use_ollama=True, use_openai_api=True)
    console.print(f"  ✅ Worker ready: {type(worker).__name__}")
    
    # Test worker
    test_resp = worker.generate("What is SFDR Article 9?", max_tokens=50)
    console.print(f"  ✅ Worker test: {test_resp[:60]}...\n")
    
    # Step 2: Ingest markdown
    console.print("[yellow]Step 2:[/yellow] Parsing Docling markdown...")
    
    isin = "FR0050000829"
    document_id = "amundi_sfdr_web_disclosure"
    
    # Create document record
    from src.models import Document
    import hashlib
    
    doc = Document(
        document_id=document_id,
        isin=isin,
        document_type="sfdr_website_disclosure",
        version="1",
        checksum=hashlib.md5(DOCLING_MARKDOWN.encode()).hexdigest(),
        source_path="data/documents/by_isin/FR0050000829/sfdr/WebsiteSfdrDisclosure_20250526.pdf",
        total_pages=8,
        processed=True,
    )
    db.insert_document(doc)
    console.print(f"  ✅ Document created: {document_id}")
    
    # Parse sections
    sections = ingestion.parse_markdown_to_sections(DOCLING_MARKDOWN, document_id)
    console.print(f"  ✅ Parsed {len(sections)} sections")
    
    for section in sections:
        db.insert_section(section)
    console.print(f"  ✅ Sections stored in database")
    
    # Create spans
    spans = ingestion.create_spans_from_sections(sections)
    console.print(f"  ✅ Created {len(spans)} spans")
    
    for span in spans:
        db.insert_span(span)
    console.print(f"  ✅ Spans stored in database\n")
    
    # Step 3: Index for retrieval
    console.print("[yellow]Step 3:[/yellow] Building BM25 index...")
    retriever.index_document(document_id)
    console.print(f"  ✅ Document indexed\n")
    
    # Test retrieval
    console.print("[yellow]Step 3a:[/yellow] Testing retrieval...")
    test_results = retriever.retrieve(document_id, "investissement durable obligations vertes", top_k=3)
    console.print(f"  ✅ Retrieved {len(test_results)} relevant sections")
    if test_results:
        top_section = test_results[0][0]
        console.print(f"  📄 Top result: {top_section['title'][:50]}...")
        console.print(f"     Score: {test_results[0][1]:.2f}\n")
    
    # Step 4: Extract SFDR state with RLM controller
    console.print("[yellow]Step 4:[/yellow] Extracting SFDR state with RLM controller...")
    console.print("[dim]Using native DSPy with Ollama[/dim]\n")
    
    controller = RLMController(db, retriever, use_native_dspy=True)
    
    state = controller.build_sfdr_state(
        document_id=document_id,
        isin=isin,
        doc_version="1",
    )
    
    console.print(f"  ✅ SFDR state extracted!")
    console.print(f"     State ID: {state.state_id}")
    console.print(f"     Overall confidence: {state.confidence:.2f}\n")
    
    # Step 5: Display results
    console.print("[yellow]Step 5:[/yellow] Extraction Results\n")
    
    table = Table(show_header=True, header_style="bold magenta", title="SFDR State Extraction")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Confidence", justify="right")
    
    # Article
    table.add_row(
        "SFDR Article",
        state.claimed_article or "Not found",
        f"{state.confidence:.2f}" if state.claimed_article else "0.00"
    )
    
    # Definition
    if state.sustainable_investment_definition:
        def_text = state.sustainable_investment_definition.text or "Not found"
        def_conf = state.sustainable_investment_definition.confidence
        table.add_row(
            "Sustainable Investment Definition",
            f"{'✅' if state.sustainable_investment_definition.present else '❌'} {def_text[:60]}...",
            f"{def_conf:.2f}"
        )
    
    # DNSH
    if state.dnsh:
        table.add_row(
            "DNSH (Do No Significant Harm)",
            f"{'✅' if state.dnsh.present else '❌'} Coverage: {state.dnsh.coverage.value}",
            f"{state.dnsh.confidence:.2f}"
        )
    
    # PAI
    if state.pai and state.pai.mandatory_coverage_ratio is not None:
        table.add_row(
            "PAI Coverage",
            f"✅ {state.pai.mandatory_coverage_ratio:.1%}",
            f"{state.pai.confidence:.2f}"
        )
    
    console.print(table)
    console.print()
    
    # Missing fields
    if state.missing_fields:
        console.print("[yellow]Missing fields:[/yellow]")
        for field in state.missing_fields:
            console.print(f"  ⚠️  {field}")
        console.print()
    
    # Citations
    console.print("[yellow]Citations:[/yellow]")
    citation_count = 0
    if state.sustainable_investment_definition:
        citation_count += len(state.sustainable_investment_definition.citations)
    if state.dnsh:
        citation_count += len(state.dnsh.citations)
    if state.pai:
        citation_count += len(state.pai.citations)
    console.print(f"  📎 Total citations: {citation_count}\n")
    
    # Step 6: Save results
    console.print("[yellow]Step 6:[/yellow] Saving results...")
    
    db.insert_sfdr_state(state)
    console.print(f"  ✅ State saved to database")
    
    output_file = Path("test_output_amundi.json")
    output_data = {
        "fund": {
            "isin": isin,
            "name": "SG AMUNDI OBLIGATIONS VERTES",
        },
        "document": {
            "id": document_id,
            "type": "sfdr_website_disclosure",
            "pages": 8,
        },
        "state": state.model_dump(),
        "test_metadata": {
            "llm": "ollama",
            "model": "qwen2.5:3b-instruct",
            "api": "openai_compatible",
            "dspy_version": "2.4.9",
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    
    console.print(f"  ✅ Results exported to {output_file}\n")
    
    # Summary
    console.print("[bold green]✅ Test Complete![/bold green]\n")
    console.print("[bold]Pipeline Summary:[/bold]")
    console.print(f"  📄 Document: {document_id}")
    console.print(f"  📝 Sections: {len(sections)}")
    console.print(f"  🔍 Spans: {len(spans)}")
    console.print(f"  📊 SFDR State ID: {state.state_id}")
    console.print(f"  🎯 Confidence: {state.confidence:.2%}")
    console.print(f"  📎 Citations: {citation_count}")
    console.print(f"  ⚠️  Missing: {len(state.missing_fields)} fields")
    
    console.print("\n[dim]Database: data/test_pipeline.duckdb[/dim]")
    console.print(f"[dim]Output: {output_file}[/dim]\n")
    
    db.close()


if __name__ == "__main__":
    main()
