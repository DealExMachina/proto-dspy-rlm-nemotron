#!/usr/bin/env python3
"""
Organize regulatory documents into ISIN-based structure.

This script:
1. Extracts documents from zip files
2. Classifies documents by type
3. Organizes into ISIN-based directory structure
4. Generates metadata files
"""

import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import hashlib


# Document type classification
DOCUMENT_TYPE_MAP = {
    "RA": ("annual_report", 3, "Rapport Annuel"),
    "PSC": ("prospectus", 3, "Prospectus"),
    "SfdrPeriodicAnnex": ("sfdr", 3, "SFDR Periodic Annex (Art 11)"),
    "WebsiteSfdrDisclosure": ("sfdr", 3, "SFDR Website Disclosure (Art 10)"),
    "PreContractualDocument": ("sfdr", 3, "SFDR Pre-contractual Annex"),
    "WebsiteSfdrDisclosureSummary": ("sfdr", 2, "SFDR Disclosure Summary"),
    "SRITransparencyCode": ("supplementary", 1, "SRI Transparency Code"),
    "ClimateReport": ("supplementary", 1, "Climate/TCFD Report"),
    "MonthlyFactsheet": ("supplementary", 1, "Monthly Factsheet"),
    "KIDPRIIPs": ("supplementary", 1, "KIID/PRIIPs KID"),
}


class DocumentOrganizer:
    """Organize documents into ISIN-based structure."""

    def __init__(self, base_path: Path = None):
        """Initialize organizer."""
        self.base_path = base_path or Path("data/documents")
        self.raw_path = self.base_path / "raw"
        self.by_isin_path = self.base_path / "by_isin"
        self.processed_path = self.base_path / "processed"

    def extract_zip(self, zip_path: Path, extract_to: Path) -> List[Path]:
        """Extract zip file and return list of extracted files."""
        print(f"📦 Extracting {zip_path.name}...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        return list(extract_to.glob("*.pdf"))

    def classify_document(self, filename: str) -> Tuple[str, str, int, str]:
        """
        Classify document by type.
        
        Returns: (category, doc_type, priority, description)
        """
        # Extract document type prefix
        prefix = filename.split('_')[0]
        
        if prefix in DOCUMENT_TYPE_MAP:
            category, priority, description = DOCUMENT_TYPE_MAP[prefix]
            return category, prefix, priority, description
        
        return "unknown", prefix, 0, "Unknown document type"

    def extract_date_from_filename(self, filename: str) -> str:
        """Extract date from filename (YYYYMMDD format)."""
        import re
        matches = re.findall(r'(20\d{6})', filename)
        return matches[-1] if matches else "unknown"

    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_isin_structure(self, isin: str) -> Dict[str, Path]:
        """Create directory structure for an ISIN."""
        isin_path = self.by_isin_path / isin
        
        dirs = {
            "root": isin_path,
            "prospectus": isin_path / "prospectus",
            "annual_report": isin_path / "annual_report",
            "sfdr": isin_path / "sfdr",
            "supplementary": isin_path / "supplementary",
        }
        
        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)
        
        return dirs

    def organize_documents(self, isin: str, zip_files: List[Path]) -> Dict:
        """
        Organize documents for an ISIN.
        
        Returns: Metadata dictionary
        """
        print(f"\n🏢 Organizing documents for ISIN: {isin}\n")
        
        # Create structure
        dirs = self.create_isin_structure(isin)
        
        # Extract temporary directory
        temp_extract = self.base_path / f"temp_extract_{isin}"
        temp_extract.mkdir(exist_ok=True)
        
        document_inventory = []
        
        try:
            # Extract all zips
            for zip_file in zip_files:
                extracted_files = self.extract_zip(zip_file, temp_extract)
                
                # Process each document
                for pdf_file in extracted_files:
                    category, doc_type, priority, description = self.classify_document(pdf_file.name)
                    date = self.extract_date_from_filename(pdf_file.name)
                    checksum = self.compute_checksum(pdf_file)
                    
                    # Determine destination
                    if category == "unknown":
                        dest_dir = dirs["supplementary"]
                    else:
                        dest_dir = dirs[category]
                    
                    # Create cleaner filename
                    dest_filename = self._create_clean_filename(pdf_file.name, doc_type, date)
                    
                    # Skip duplicates
                    if dest_filename is None:
                        print(f"  ⏭️  Skipping duplicate: {pdf_file.name}")
                        continue
                    
                    dest_path = dest_dir / dest_filename
                    
                    # Copy file
                    shutil.copy2(pdf_file, dest_path)
                    
                    print(f"  ✅ {pdf_file.name}")
                    print(f"     → {category}/{dest_filename}")
                    print(f"     Priority: {priority}, Checksum: {checksum[:12]}...")
                    
                    # Record in inventory
                    document_inventory.append({
                        "original_filename": pdf_file.name,
                        "organized_filename": dest_filename,
                        "document_type": doc_type,
                        "category": category,
                        "priority": priority,
                        "description": description,
                        "date": date,
                        "checksum": checksum,
                        "size_bytes": pdf_file.stat().st_size,
                        "source_zip": zip_file.name,
                    })
            
            # Generate metadata
            metadata = self._generate_metadata(isin, document_inventory)
            
            # Save metadata
            metadata_path = dirs["root"] / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n📋 Metadata saved to: {metadata_path}")
            
            return metadata
            
        finally:
            # Cleanup temp directory
            if temp_extract.exists():
                shutil.rmtree(temp_extract)

    def _create_clean_filename(self, original: str, doc_type: str, date: str) -> str:
        """Create clean, standardized filename."""
        # Remove version suffixes and duplicates
        if original.startswith("renamed_"):
            return None  # Skip duplicates
        
        # Standardize format: {type}_{date}.pdf
        return f"{doc_type}_{date}.pdf"

    def _generate_metadata(self, isin: str, inventory: List[Dict]) -> Dict:
        """Generate metadata.json content."""
        return {
            "isin": isin,
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
            "document_count": len(inventory),
            "documents": inventory,
            "organized_at": datetime.utcnow().isoformat() + "Z",
            "source_url": f"https://www.societegeneralegestion.fr/fra/fr/particuliers/products/{isin}"
        }

    def create_download_manifest(self, zip_files: List[Path]) -> Dict:
        """Create download manifest."""
        downloads = []
        
        for zip_file in zip_files:
            batch_id = zip_file.stem
            timestamp = datetime.fromtimestamp(zip_file.stat().st_mtime)
            
            with zipfile.ZipFile(zip_file, 'r') as zf:
                file_list = zf.namelist()
            
            downloads.append({
                "batch_id": batch_id,
                "timestamp": timestamp.isoformat() + "Z",
                "isin": "FR0050000829",
                "file_count": len(file_list),
                "total_size_mb": round(zip_file.stat().st_size / 1024 / 1024, 2),
                "source": "data_provider",
                "files": file_list
            })
        
        return {"downloads": downloads}


def main():
    """Main organization script."""
    organizer = DocumentOrganizer()
    
    # Ensure raw directory exists
    organizer.raw_path.mkdir(parents=True, exist_ok=True)
    
    # Find zip files
    zip_files = list(organizer.base_path.glob("*.zip"))
    
    if not zip_files:
        print("❌ No zip files found in data/documents/")
        return
    
    print(f"Found {len(zip_files)} zip file(s)")
    
    # Organize documents for FR0050000829
    isin = "FR0050000829"
    metadata = organizer.organize_documents(isin, zip_files)
    
    # Create download manifest
    manifest = organizer.create_download_manifest(zip_files)
    manifest_path = organizer.raw_path / "download_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📋 Download manifest saved to: {manifest_path}")
    
    # Move zips to raw/
    for zip_file in zip_files:
        dest = organizer.raw_path / zip_file.name
        if not dest.exists():
            shutil.move(zip_file, dest)
            print(f"📦 Moved {zip_file.name} to raw/")
    
    print(f"\n✅ Organization complete!")
    print(f"\n📂 Structure created:")
    print(f"   by_isin/{isin}/")
    print(f"   ├── metadata.json")
    print(f"   ├── prospectus/ ({len([d for d in metadata['documents'] if d['category'] == 'prospectus'])} files)")
    print(f"   ├── annual_report/ ({len([d for d in metadata['documents'] if d['category'] == 'annual_report'])} files)")
    print(f"   ├── sfdr/ ({len([d for d in metadata['documents'] if d['category'] == 'sfdr'])} files)")
    print(f"   └── supplementary/ ({len([d for d in metadata['documents'] if d['category'] == 'supplementary'])} files)")


if __name__ == "__main__":
    main()
