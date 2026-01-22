# Document Storage Structure

## Overview

Based on the analysis of the two document zips for **SG AMUNDI OBLIGATIONS VERTES** (ISIN: FR0050000829), this document defines the storage structure for regulatory documents.

## Fund Information

**Fund:** SG AMUNDI OBLIGATIONS VERTES  
**ISIN:** FR0050000829  
**SFDR Classification:** Article 8  
**Manager:** Société Générale Gestion (delegated to Amundi)  
**Source:** https://www.societegeneralegestion.fr/fra/fr/particuliers/products/FR0050000829

## Document Inventory

### ZIP 1: documents_20260122204056.zip (11 MB, 8 files)

| Document Type | File | Size | Pages | Category |
|---------------|------|------|-------|----------|
| Annual Report | RA_SG-AMUNDI-OBLIGATIONS-VERTES_202505_FRANCAIS_EUR_7705_xxx_1_xxx_117481.pdf | 3.9 MB | 200 | Primary |
| Prospectus | PSC_1_UM85896_fra_FRA_20250526_20250526.pdf | 981 KB | 52 | Primary |
| Prospectus (v2) | PSC_1_UM85896_fra_FRA_20250526_20250525.pdf | 895 KB | 52 | Primary |
| SRI Transparency Code | SRITransparencyCode_CL85898_FRA_FRA_20250515.pdf | 7.4 MB | ? | Supplementary |
| Monthly Factsheet | MonthlyFactsheet_4142329_CL85898_FRA_FRA_AMUNDI_RETAIL_20251231.pdf | 544 KB | 7 | Supplementary |
| Climate Report | ClimateReport_4167820_PF85897_FRA_FRA_AMUNDI_20251231.pdf | 144 KB | 2 | Supplementary |
| KIID/PRIIPs | KIDPRIIPs_803405_74269_FRA_FRA_20250526.pdf | 160 KB | 3 | Supplementary |
| Duplicate RA | renamed_1_RA_SG-AMUNDI-OBLIGATIONS-VERTES_202505_FRANCAIS_EUR_7705_xxx_1_xxx_117481.pdf | 3.2 MB | 200 | Duplicate |

### ZIP 2: documents_20260122204101.zip (1 MB, 4 files)

| Document Type | File | Size | Pages | Category |
|---------------|------|------|-------|----------|
| SFDR Periodic Annex | SfdrPeriodicAnnex_3712001_17842_FRA_FRA_20250531.pdf | 622 KB | 9 | SFDR |
| SFDR Website Disclosure | WebsiteSfdrDisclosure_PF85897_FRA_FRA_20250526.pdf | 133 KB | 8 | SFDR |
| SFDR Pre-contractual | PreContractualDocument_PF85897_FRA_FRA_20250526.pdf | 341 KB | 10 | SFDR |
| SFDR Disclosure Summary | WebsiteSfdrDisclosureSummary_PF85897_FRA_FRA_20241220.pdf | 52 KB | ? | SFDR |

## Recommended Storage Structure

```
data/
  documents/
    by_isin/
      FR0050000829/                                    # SG AMUNDI OBLIGATIONS VERTES
        metadata.json                                  # Fund metadata
        
        prospectus/
          v1_20250526_PSC_UM85896.pdf                 # Main prospectus
          v2_20250526_PSC_UM85896_revised.pdf         # Revised version
        
        annual_report/
          2025_RA_FRANCAIS_EUR.pdf                    # Annual report May 2025
        
        sfdr/
          periodic_annex_20250531.pdf                 # Article 11 periodic disclosure
          website_disclosure_20250526.pdf             # Article 10 website disclosure
          precontractual_20250526.pdf                 # Pre-contractual SFDR annex
          disclosure_summary_20241220.pdf             # Summary disclosure
        
        supplementary/
          sri_transparency_20250515.pdf               # SRI Transparency Code
          climate_report_20251231.pdf                 # Climate/TCFD report
          monthly_factsheet_20251231.pdf              # Investor factsheet
          kiid_20250526.pdf                           # KIID/PRIIPs document
    
    raw/                                               # Original downloads (audit trail)
      documents_20260122204056.zip                    # Batch 1 download
      documents_20260122204101.zip                    # Batch 2 download
      download_manifest.json                          # Download metadata
    
    processed/                                         # Docling processed output
      FR0050000829/
        prospectus_20250526/
          document.json                               # Docling JSON structure
          document.md                                 # Markdown export
          metadata.json                               # Processing metadata
        annual_report_2025/
          document.json
          document.md
          metadata.json
        sfdr_periodic_annex_20250531/
          document.json
          document.md
          metadata.json
```

## Metadata Schema

### metadata.json (per ISIN)

```json
{
  "isin": "FR0050000829",
  "fund_name": "SG AMUNDI OBLIGATIONS VERTES",
  "lei": "969500TKG1TYT8BKXA62",
  "manager": "Société Générale Gestion",
  "sub_delegate": "Amundi",
  "domicile": "France",
  "currency": "EUR",
  "sfdr_article": "8",
  "fund_identifiers": {
    "pf_code": "PF85897",
    "cl_code": "CL85898",
    "um_code": "UM85896"
  },
  "language": "FRA",
  "created_at": "2026-01-22T20:40:56Z",
  "source_url": "https://www.societegeneralegestion.fr/fra/fr/particuliers/products/FR0050000829"
}
```

### download_manifest.json

```json
{
  "downloads": [
    {
      "batch_id": "documents_20260122204056",
      "timestamp": "2026-01-22T20:40:56Z",
      "isin": "FR0050000829",
      "file_count": 8,
      "total_size_mb": 17.2,
      "source": "data_provider",
      "files": [...]
    },
    {
      "batch_id": "documents_20260122204101",
      "timestamp": "2026-01-22T20:41:01Z",
      "isin": "FR0050000829",
      "file_count": 4,
      "total_size_mb": 1.1,
      "source": "data_provider",
      "files": [...]
    }
  ]
}
```

## Document Type Mapping

| Prefix | Full Name | Document Type | Priority for SFDR |
|--------|-----------|---------------|-------------------|
| **RA** | Rapport Annuel | annual_report | ⭐⭐⭐ High |
| **PSC** | Prospectus | prospectus | ⭐⭐⭐ High |
| **SfdrPeriodicAnnex** | SFDR Periodic Annex | sfdr_periodic_annex | ⭐⭐⭐ Critical |
| **WebsiteSfdrDisclosure** | Website SFDR Disclosure | sfdr_website_disclosure | ⭐⭐⭐ Critical |
| **PreContractualDocument** | Pre-contractual Disclosure | sfdr_precontractual | ⭐⭐⭐ Critical |
| **WebsiteSfdrDisclosureSummary** | Disclosure Summary | sfdr_disclosure_summary | ⭐⭐ Medium |
| **SRITransparencyCode** | SRI Transparency Code | sri_transparency | ⭐ Low |
| **ClimateReport** | Climate/TCFD Report | climate_report | ⭐ Low |
| **MonthlyFactsheet** | Monthly Factsheet | monthly_factsheet | ⭐ Low |
| **KIDPRIIPs** | KIID/PRIIPs KID | kiid | ⭐ Low |

## Implementation Strategy

### Phase 1: Organize Existing Documents

1. **Create ISIN directory structure**
   ```bash
   mkdir -p data/documents/by_isin/FR0050000829/{prospectus,annual_report,sfdr,supplementary}
   mkdir -p data/documents/raw
   mkdir -p data/documents/processed/FR0050000829
   ```

2. **Move raw zips**
   ```bash
   mv data/documents/*.zip data/documents/raw/
   ```

3. **Organize PDFs by type**
   - Extract from zips
   - Classify by document type
   - Rename with consistent pattern
   - Place in appropriate subdirectories

4. **Generate metadata.json**
   - Extract fund information
   - Record document inventory
   - Track versions

### Phase 2: Database Schema Updates

Update `src/models/document.py` to support:

```python
class DocumentMetadata:
    """Extended metadata for document organization."""
    fund_id_codes: Dict[str, str]  # {"pf": "PF85897", "cl": "CL85898"}
    document_category: str  # "primary", "sfdr", "supplementary"
    priority: int  # 1-3 for extraction priority
    language: str  # "FRA", "ENG"
```

### Phase 3: Ingestion Updates

Update `src/ingestion/docling_ingestion.py` to:
- Read from organized structure
- Track document relationships
- Handle versioning
- Process by priority

## Usage in Code

```python
from pathlib import Path

# Get documents for an ISIN
isin = "FR0050000829"
docs_path = Path(f"data/documents/by_isin/{isin}")

# Primary SFDR documents
sfdr_docs = list(docs_path.glob("sfdr/*.pdf"))

# Prospectus
prospectus = list(docs_path.glob("prospectus/*.pdf"))

# Annual report
annual_report = list(docs_path.glob("annual_report/*.pdf"))

# Process in priority order
priority_docs = sfdr_docs + prospectus + annual_report
```

## Benefits of This Structure

1. **ISIN-centric**: Standard identifier across all regulatory systems
2. **Version tracking**: Date-based filenames enable drift detection
3. **Type categorization**: Easy to prioritize SFDR documents
4. **Audit trail**: Raw zips preserved with download metadata
5. **Scalability**: Easy to add more ISINs
6. **Processing separation**: Raw vs processed clearly separated
7. **Provenance**: Full chain from download → processing → extraction

## Migration Script Needed

Create `scripts/organize_documents.py` to:
1. Extract zips
2. Parse filenames
3. Classify document types
4. Create directory structure
5. Move files to correct locations
6. Generate metadata.json
7. Create download_manifest.json

## Next Steps

1. Create the directory structure
2. Move and organize existing documents
3. Generate metadata files
4. Update ingestion code to read from structure
5. Add to `.gitignore` (PDFs are large, track structure not files)
6. Document for future downloads
