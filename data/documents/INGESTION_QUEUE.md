# Document Ingestion Queue

## Overview

This file tracks the ingestion status of regulatory documents for the continuous monitoring system.

## Active Funds

### 1. Amundi Obligations Vertes (FR0050000829)

**Fund Details:**
- **ISIN:** FR0050000829
- **Name:** SG AMUNDI OBLIGATIONS VERTES
- **SFDR:** Article 8
- **Manager:** Société Générale Gestion (delegated to Amundi)
- **LEI:** 969500TKG1TYT8BKXA62

**Official Sources:**
- 🔗 Fund Profile: https://www.societegeneralegestion.fr/fra/fr/particuliers/products/FR0050000829
- 🔗 Regulatory Documents API: https://epr.amfinesoft.com/api/v1/download/SOGECAP/underlying/pcd/FR0050000829/lang/fr?key=7pPlB7HoeaCTjsHOsYGA87RfJcmpSQ

**Document Inventory:**

| Category | Document | Date | Pages | Status | Priority |
|----------|----------|------|-------|--------|----------|
| SFDR | SfdrPeriodicAnnex | 2025-05-31 | 9 | ⏳ Queued | 🔴 P1 |
| SFDR | WebsiteSfdrDisclosure | 2025-05-26 | 8 | ⏳ Queued | 🔴 P1 |
| SFDR | PreContractualDocument | 2025-05-26 | 10 | ⏳ Queued | 🔴 P1 |
| Prospectus | PSC | 2025-05-26 | 52 | ⏳ Queued | 🟡 P2 |
| Annual Report | RA | 2025-05 | 200 | ⏳ Queued | 🟡 P3 |
| SFDR | DisclosureSummary | 2024-12-20 | ? | ⏳ Queued | 🟢 P4 |
| Supplementary | SRI Transparency | 2025-05-15 | ? | ⏳ Low | 🟢 P5 |
| Supplementary | Climate Report | 2025-12-31 | 2 | ⏳ Low | 🟢 P5 |
| Supplementary | Monthly Factsheet | 2025-12-31 | 7 | ⏳ Low | 🟢 P5 |
| Supplementary | KIID/PRIIPs | 2025-05-26 | 3 | ⏳ Low | 🟢 P5 |

**Storage Location:** `data/documents/by_isin/FR0050000829/`

**Next Actions:**
1. ✅ Documents organized into ISIN-based structure
2. ⏳ Ingest with Docling (convert PDF → markdown + JSON)
3. ⏳ Extract SFDR state using RLM controller
4. ⏳ Store in DuckDB
5. ⏳ Generate evidence pack

## Ingestion Priority Strategy

### Priority 1 (Critical - SFDR Core Documents)
Process these first - they contain the most structured SFDR data:
- `sfdr/SfdrPeriodicAnnex_20250531.pdf` - Article 11 periodic disclosure
- `sfdr/WebsiteSfdrDisclosure_20250526.pdf` - Article 10 website disclosure
- `sfdr/PreContractualDocument_20250526.pdf` - Pre-contractual annex

**Expected Data:**
- Sustainable investment definition
- DNSH methodology
- PAI consideration
- Proportion of sustainable investments
- Environmental/social characteristics promoted

### Priority 2 (High - Prospectus)
- `prospectus/PSC_20250526.pdf` - 52 pages

**Expected Data:**
- Investment objective
- Investment policy details
- Risk disclosures
- Sustainability strategy details

### Priority 3 (Medium - Annual Report)
- `annual_report/RA_unknown.pdf` - 200 pages

**Expected Data:**
- Actual sustainability performance
- PAI indicators (realized)
- Portfolio composition
- Performance attribution

### Priority 4-5 (Low - Supplementary)
Process if needed for additional context or validation

## Usage

### For RLM Controller

```python
from pathlib import Path
import json

# Load metadata
isin = "FR0050000829"
metadata_path = Path(f"data/documents/by_isin/{isin}/metadata.json")
with open(metadata_path) as f:
    metadata = json.load(f)

# Get priority documents
priority_docs = sorted(
    metadata["documents"],
    key=lambda d: d["priority"],
    reverse=True
)

# Process in order
for doc in priority_docs:
    if doc["priority"] >= 2:  # Process P1, P2, P3
        doc_path = Path(f"data/documents/by_isin/{isin}/{doc['category']}/{doc['organized_filename']}")
        print(f"Processing: {doc_path}")
        # ... ingest with Docling ...
```

### For Iteration 1 Testing

Start with the smallest, most structured document:

```bash
# Use SFDR Website Disclosure (8 pages, highly structured)
python run_one_doc.py \
  data/documents/by_isin/FR0050000829/sfdr/WebsiteSfdrDisclosure_20250526.pdf \
  --isin FR0050000829 \
  --doc-type sfdr_website_disclosure \
  --use-ollama
```

## Document Download Tracking

Stored in: `data/documents/raw/download_manifest.json`

Tracks:
- Download batch ID
- Timestamp
- Source
- File inventory
- Checksums

## Future ISINs

When adding new funds, follow this pattern:

1. Create directory: `data/documents/by_isin/{NEW_ISIN}/`
2. Download documents from official sources
3. Run: `python scripts/organize_documents.py --isin {NEW_ISIN}`
4. Update this ingestion queue
5. Process with RLM controller

## Storage on S3/Bucket (Future)

For production deployment, migrate to:

```
s3://regulatory-docs-bucket/
  by_isin/
    FR0050000829/
      [same structure as local]
```

Use same directory structure for consistency.
