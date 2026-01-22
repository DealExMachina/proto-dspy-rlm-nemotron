# Document Storage

## Structure

This directory contains regulatory documents organized by ISIN for the continuous monitoring system.

```
documents/
├── by_isin/
│   └── FR0050000829/              # Amundi Obligations Vertes
│       ├── metadata.json          # Fund metadata & document inventory
│       ├── sources.json           # Official source URLs
│       ├── prospectus/            # Prospectus documents
│       ├── annual_report/         # Annual reports
│       ├── sfdr/                  # SFDR-specific documents (Art 10, 11)
│       └── supplementary/         # Other documents (climate, factsheets)
│
├── raw/                           # Original download zips (audit trail)
│   ├── documents_*.zip
│   └── download_manifest.json
│
├── processed/                     # Docling processed output
│   └── FR0050000829/
│       └── {document_id}/
│           ├── document.json      # Docling structured output
│           ├── document.md        # Markdown export
│           └── metadata.json      # Processing metadata
│
├── INGESTION_QUEUE.md            # Document processing queue & status
└── README.md                      # This file
```

## Current Holdings

### FR0050000829 - Amundi Obligations Vertes

**SFDR Article 8 Fund**

- **Prospectus:** 2 versions (May 2025)
- **Annual Report:** 1 report (FY 2024/2025, 200 pages)
- **SFDR Documents:** 4 documents (Art 10, Art 11 disclosures)
- **Supplementary:** 4 documents (climate, factsheet, KIID, SRI)

**Total:** 11 documents, ~18 MB

## Usage

### Get Documents for a Fund

```python
from pathlib import Path
import json

isin = "FR0050000829"
base_path = Path(f"data/documents/by_isin/{isin}")

# Load metadata
with open(base_path / "metadata.json") as f:
    metadata = json.load(f)

# Get SFDR documents
sfdr_docs = list(base_path.glob("sfdr/*.pdf"))

# Get high-priority documents
priority_docs = [
    doc for doc in metadata["documents"]
    if doc["priority"] >= 3
]
```

### Process Documents with RLM

```bash
# Start with smallest SFDR document (8 pages)
python run_one_doc.py \
  data/documents/by_isin/FR0050000829/sfdr/WebsiteSfdrDisclosure_20250526.pdf \
  --isin FR0050000829 \
  --doc-type sfdr_website_disclosure \
  --use-ollama
```

## Document Categories

### Primary Documents (Priority 3)

**SFDR Documents:**
- Contain structured SFDR disclosures (Art 10, 11)
- Pre-contractual annexes
- Most relevant for SFDR state extraction

**Prospectus:**
- Investment objectives and policies
- Sustainability strategy
- Risk disclosures

**Annual Report:**
- Realized performance
- Actual PAI metrics
- Portfolio holdings

### Supplementary Documents (Priority 1-2)

**Supporting Information:**
- Climate/TCFD reports
- Monthly factsheets
- KIID/PRIIPs documents
- SRI transparency codes

Use for validation and additional context.

## Ingestion Workflow

1. **Load metadata:** Read `metadata.json` for document inventory
2. **Select documents:** Choose by priority and category
3. **Convert with Docling:** PDF → markdown + JSON
4. **Extract with RLM:** Use RLM controller to extract SFDR state
5. **Store in DB:** Save to DuckDB with citations
6. **Track progress:** Update ingestion queue

## Storage Strategy

### Current (Local Storage)

Documents stored in repository under `data/documents/`:
- ✅ Good for development and testing
- ✅ Version controlled structure (metadata, not PDFs)
- ⚠️ PDFs ignored via .gitignore (too large)

### Future (Cloud Storage)

Migrate to S3/bucket:
```
s3://regulatory-docs-bucket/
  by_isin/
    FR0050000829/
      [same structure]
```

**Benefits:**
- Scalable to many funds
- Automatic backups
- Shared access
- Cost-effective storage

## Adding New Funds

1. **Create structure:**
   ```bash
   mkdir -p data/documents/by_isin/{ISIN}/{prospectus,annual_report,sfdr,supplementary}
   ```

2. **Download documents:**
   - From official fund page
   - From regulatory database API
   - Save as zips in `data/documents/`

3. **Organize:**
   ```bash
   python scripts/organize_documents.py --isin {ISIN}
   ```

4. **Document sources:**
   - Update `sources.json` with official URLs
   - Track in `INGESTION_QUEUE.md`

5. **Process:**
   ```bash
   python run_one_doc.py data/documents/by_isin/{ISIN}/sfdr/*.pdf --isin {ISIN}
   ```

## File Naming Convention

Format: `{DocumentType}_{YYYYMMDD}.pdf`

Examples:
- `SfdrPeriodicAnnex_20250531.pdf`
- `PSC_20250526.pdf`
- `RA_unknown.pdf` (when date not extractable)

## Metadata Files

### metadata.json
Complete fund and document inventory with:
- ISIN, LEI, fund identifiers
- Manager information
- Document list with checksums
- Priority classification

### sources.json
Official source URLs for:
- Fund profile pages
- Document download APIs
- Regulatory databases

### download_manifest.json
Download audit trail:
- Batch IDs
- Timestamps
- File inventories
- Source tracking

## Notes

- All metadata JSON files are tracked in git
- PDFs are excluded (too large, tracked via checksums)
- Structure enables easy bucket migration
- ISIN-based organization is standard across EU regulatory systems
