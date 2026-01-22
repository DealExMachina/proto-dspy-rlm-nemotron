# Sample Fund Documents for Testing

For testing the Continuous Regulatory Intelligence system, you need SFDR-compliant fund prospectuses.

## Recommended Sources

### 1. Major Asset Managers with SFDR Funds

**Amundi**
- Search: "Amundi MSCI World ESG Leaders Select prospectus"
- ISIN: LU1602144229 (Article 8)
- URL: https://www.amundi.lu

**BlackRock iShares**
- Search: "iShares MSCI World SRI UCITS ETF prospectus"
- ISIN: IE00BYX2JD69 (Article 8)
- URL: https://www.ishares.com

**DWS**
- Search: "DWS ESG Equity Income prospectus"
- Multiple Article 8 and 9 funds
- URL: https://www.dws.com

**BNP Paribas**
- Search: "BNP Paribas Green Tigers prospectus"
- ISIN: LU0823414635 (Article 9)
- URL: https://www.bnpparibas-am.com

### 2. How to Download

1. Go to fund provider website
2. Navigate to fund page using ISIN
3. Look for "Documents" or "Literature" section
4. Download:
   - Prospectus (long document, 100-300 pages)
   - SFDR Annex (if separate)
   - Annual Report (optional for Iteration 2)

### 3. Example ISINs to Test

**Article 8 Funds:**
- LU1602144229 - Amundi MSCI World ESG Leaders
- IE00BYX2JD69 - iShares MSCI World SRI
- LU2145460353 - DWS Invest ESG Equity Income

**Article 9 Funds:**
- LU0823414635 - BNP Paribas Green Tigers
- LU1291108642 - Nordea Global Climate & Environment Fund

## Storage

Place downloaded PDFs in:
```
data/documents/
├── LU1602144229_prospectus.pdf
├── IE00BYX2JD69_prospectus.pdf
└── ...
```

## Legal Notes

- Use these documents for research and testing purposes only
- These are public documents but subject to copyright
- Do not redistribute without permission
- Always check the fund provider's terms of use
