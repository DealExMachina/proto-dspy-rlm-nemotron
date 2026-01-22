# Test Fixtures

This directory contains test data for the regulatory intelligence system.

## Structure

- `sample_documents/`: Sample markdown documents representing different fund types
- `expected_outputs/`: Expected SFDR state JSON outputs for validation

## Sample Documents

### test_article_8.md
Article 8 SFDR fund that promotes environmental and social characteristics.

Key features:
- Partial sustainable investment
- Partial DNSH coverage (70%)
- 71% PAI coverage
- ISIN: LU0123456789

### test_article_9.md
Article 9 SFDR fund with sustainable investment as its objective.

Key features:
- 100% sustainable investment
- Full DNSH coverage
- 100% PAI coverage
- ISIN: LU9876543210

### test_incomplete.md
Generic fund without SFDR disclosures.

Key features:
- No Article classification
- Missing sustainable investment definition
- No DNSH information
- No PAI data
- ISIN: LU0000000001

## Expected Outputs

Expected outputs are provided for validation but should be treated as approximate. Actual LLM outputs may vary slightly in:
- Exact wording of extracted text
- Confidence scores
- Page numbers (depending on parsing)

The expected outputs validate:
- Overall structure
- Field presence/absence
- Approximate values (e.g., PAI coverage ratio)
- DNSH coverage level (none/partial/full)

## Usage in Tests

These fixtures are used by:
- Integration tests (full pipeline)
- E2E tests (end-to-end workflows)
- Validation tests (output format checking)

Example:
```python
from pathlib import Path

# Load sample document
doc_path = Path(__file__).parent / "fixtures/sample_documents/test_article_8.md"
with open(doc_path) as f:
    markdown = f.read()

# Load expected output
expected_path = Path(__file__).parent / "fixtures/expected_outputs/expected_state_article_8.json"
with open(expected_path) as f:
    expected = json.load(f)
```
