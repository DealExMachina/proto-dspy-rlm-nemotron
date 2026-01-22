#!/usr/bin/env python3
"""
Download and organize Pictet Water fund documents.

ISIN: LU0104884860
"""

import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime


ISIN = "LU0104884860"
FUND_NAME = "Pictet - Water - P EUR"

# Document sources
SOURCES = {
    "kid": {
        "url": "https://epr.amfinesoft.com/api/v1/download/SOGECAP/underlying/kid/LU0104884860/lang/fr?key=7pPlB7HoeaCTjsHOsYGA87RfJcmpSQ",
        "filename": "kid_20250122.pdf",
        "category": "supplementary",
        "type": "KIDPRIIPs",
        "priority": 1,
    },
    # Note: Factsheet URL blocked by CloudFront, would need alternative access
}


def download_file(url: str, output_path: Path) -> bool:
    """Download file using curl."""
    try:
        result = subprocess.run(
            ["curl", "-L", "-o", str(output_path), url],
            capture_output=True,
            timeout=60
        )
        return result.returncode == 0 and output_path.exists()
    except Exception as e:
        print(f"Download error: {e}")
        return False


def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_pictet_structure():
    """Create document structure for Pictet Water fund."""
    base_path = Path("data/documents/by_isin") / ISIN
    
    # Create directories
    dirs = {
        "prospectus": base_path / "prospectus",
        "annual_report": base_path / "annual_report",
        "sfdr": base_path / "sfdr",
        "supplementary": base_path / "supplementary",
    }
    
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created structure for {ISIN}\n")
    return base_path, dirs


def main():
    """Main download and organization."""
    print(f"🏢 PICTET WATER FUND")
    print(f"   ISIN: {ISIN}")
    print(f"   Name: {FUND_NAME}\n")
    
    # Create structure
    base_path, dirs = create_pictet_structure()
    
    # Download documents
    download_dir = Path("data/documents/downloads_pictet")
    download_dir.mkdir(exist_ok=True)
    
    documents = []
    
    for doc_key, doc_info in SOURCES.items():
        print(f"⬇️  Downloading {doc_key}...")
        output_file = download_dir / f"{doc_key}_{ISIN}.pdf"
        
        if download_file(doc_info["url"], output_file):
            # Verify it's a PDF
            if output_file.stat().st_size > 1000:  # More than 1KB
                print(f"   ✅ Downloaded: {output_file.stat().st_size / 1024:.1f} KB")
                
                # Move to organized structure
                dest_dir = dirs[doc_info["category"]]
                dest_file = dest_dir / doc_info["filename"]
                
                import shutil
                shutil.copy2(output_file, dest_file)
                
                checksum = compute_checksum(dest_file)
                
                documents.append({
                    "original_filename": output_file.name,
                    "organized_filename": doc_info["filename"],
                    "document_type": doc_info["type"],
                    "category": doc_info["category"],
                    "priority": doc_info["priority"],
                    "source_url": doc_info["url"],
                    "download_date": datetime.utcnow().isoformat() + "Z",
                    "checksum": checksum,
                    "size_bytes": dest_file.stat().st_size,
                })
                
                print(f"   📁 Organized: {doc_info['category']}/{doc_info['filename']}")
            else:
                print(f"   ⚠️  File too small (likely error page)")
        else:
            print(f"   ❌ Download failed")
        print()
    
    # Generate metadata
    metadata = {
        "isin": ISIN,
        "fund_name": FUND_NAME,
        "manager": "Pictet Asset Management",
        "domicile": "Luxembourg",
        "currency": "EUR",
        "share_class": "P EUR",
        "fund_identifiers": {
            "isin": ISIN,
        },
        "document_count": len(documents),
        "documents": documents,
        "organized_at": datetime.utcnow().isoformat() + "Z",
    }
    
    # Save metadata
    metadata_path = base_path / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"📋 Metadata saved: {metadata_path}")
    
    # Save sources
    sources = {
        "isin": ISIN,
        "fund_name": FUND_NAME,
        "official_sources": {
            "fund_profile_fr": {
                "url": "https://am.pictet.com/fr/fr/individuals/funds/pictet-water/LU0104884860",
                "description": "Official fund page (French site)",
                "type": "web_page",
            },
            "fund_profile_en": {
                "url": "https://am.pictet.com/lu/en/individuals/funds/pictet-water/LU0104884860",
                "description": "Official fund page (Luxembourg/English site)",
                "type": "web_page",
            },
            "kid_download": {
                "url": "https://epr.amfinesoft.com/api/v1/download/SOGECAP/underlying/kid/LU0104884860/lang/fr?key=7pPlB7HoeaCTjsHOsYGA87RfJcmpSQ",
                "description": "KID/PRIIPs document download API",
                "type": "download_api",
                "status": "working",
            },
            "factsheet_download": {
                "url": "https://documents.am.pictet/?audience=INSTITUTIONAL&cat=marketing-permalink&dcty=FR&dla=fr&dtyp=FCL_RME&isin=LU0104884860",
                "description": "Marketing factsheet download",
                "type": "download_api",
                "status": "blocked_by_cloudfront",
            },
        },
        "notes": [
            "Pictet uses different document structure than Amundi",
            "Documents accessible via amfinesoft API",
            "Marketing materials behind CloudFront (may need authentication)",
            "SFDR documents likely available on official site",
        ]
    }
    
    sources_path = base_path / "sources.json"
    with open(sources_path, 'w') as f:
        json.dump(sources, f, indent=2)
    
    print(f"📋 Sources saved: {sources_path}")
    
    print(f"\n✅ Organization complete!")
    print(f"\n📂 Structure:")
    print(f"   by_isin/{ISIN}/")
    print(f"   ├── metadata.json")
    print(f"   ├── sources.json")
    print(f"   └── supplementary/ ({len(documents)} file)")


if __name__ == "__main__":
    main()
