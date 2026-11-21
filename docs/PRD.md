Product Requirements Document (PRD)

Project Title

Continuous Regulatory Intelligence – RLM/DSPy/Nemotron Demonstrator

Author

Jean-Baptiste Dézard

Date

2026-01

⸻

1. Objective

Build a minimal but credible demonstrator that proves:
	1.	Long regulatory documents can be processed without long-context prompts.
	2.	A recursive / TRM / RLM-style controller can extract a structured regulatory state.
	3.	The system can be extended into a continuous, long-running monitoring loop.

This is not a chatbot and not a RAG demo.
It is a stateful regulatory control system.

Primary goal:

Demonstrate that a DSPy + TRM/RLM controller + Nemotron worker can build and maintain an auditable SFDR state over time.

⸻

2. Target Users

Primary:
	•	Insurance CTO / Chief Architect
	•	Head of Data & AI Platforms
	•	RegTech / SupTech innovation teams

Secondary:
	•	Internal research & platform engineering teams
	•	EU research funding evaluators

⸻

3. Core Use Case (MVP Narrative)

“Given a long prospectus and SFDR annex for one EU fund:
	•	Build a structured SFDRState object with citations.
	•	Persist it in a database.
	•	When a new version of the document appears:
	•	recompute the state,
	•	detect drift,
	•	raise an alert.”

This must run autonomously on a schedule.

⸻

4. Non-Goals (Explicit)

The first iterations will NOT:
	•	Provide a conversational chatbot
	•	Support free-form natural language queries
	•	Cover the full SFDR RTS schema
	•	Integrate ESG vendor data
	•	Support many funds initially

Focus is on:
	•	correctness
	•	reproducibility
	•	state
	•	drift

⸻

5. System Principles
	1.	Small contexts only: no long-context inference.
	2.	Recursive control: the LLM is a worker, not a monolith.
	3.	Structured outputs: everything is written into canonical tables.
	4.	Provenance-first: every fact has page/span citations.
	5.	Idempotent execution: re-running jobs produces the same state.
	6.	Long-running by design: scheduler + versioning from day one.

⸻

6. High-Level Architecture

Components:
	1.	Ingestion Worker
	•	Input: PDF
	•	Output: DocumentGraph (pages, sections, tables, spans)
	2.	Retrieval Layer
	•	BM25 or ColBERT-lite over sections/spans
	3.	RLM / TRM Controller
	•	Goal-driven recursive loop
	•	Fills SFDRState schema field by field
	4.	Nemotron Worker (via vLLM on Koyeb)
	•	Executes small extraction tasks
	•	Produces structured JSON + citations
	5.	State Store
	•	DuckDB
	•	Versioned documents
	•	Versioned SFDR states
	6.	Drift Engine
	•	Compares SFDRState vN vs vN+1
	•	Produces DriftEvent + Alert
	7.	Scheduler
	•	Periodic re-ingestion and recomputation

⸻

7. Canonical Outputs (Iteration 1)

Minimal SFDRState fields:
	•	fund_isin
	•	doc_version
	•	claimed_article
	•	sustainable_investment_definition.present
	•	sustainable_investment_definition.text
	•	dnsh.present
	•	dnsh.coverage (none/partial/full)
	•	pai.mandatory_coverage_ratio
	•	missing_fields[]
	•	confidence

Each field must store:
	•	value
	•	confidence
	•	citation_spans[]

⸻

8. Key Success Criteria

Iteration 1 success:
	•	Extract correct sustainable investment definition from a 200+ page prospectus.
	•	Provide exact page/span citations.

Iteration 2 success:
	•	Combine 3 documents into one consistent fund state.
	•	Detect at least one real inconsistency.

Iteration 3 success:
	•	Detect a real wording or numeric drift across two versions.
	•	Generate a DriftEvent + Alert automatically.

⸻

9. Nemotron on vLLM (Important)

Your existing Nemotron inference on Koyeb is highly useful and strongly recommended.

Usage model:
	•	Nemotron is the “worker model”.
	•	Context size kept small (1–4k tokens).
	•	Used only for:
	•	section classification
	•	field extraction
	•	table row extraction
	•	evidence verification

This keeps:
	•	cost predictable
	•	latency low
	•	architecture aligned with RLM paradigm.

⸻

Implementation Plan (Three Iterations)

⸻

Iteration 1 — One Long Document (2–3 weeks)

Objective

Prove that we can extract a structured SFDR state from a single long document using recursive control.

Scope
	•	1 fund
	•	1 long prospectus or SFDR annex
	•	No crawling
	•	No drift yet

Components to Build
	1.	Document Ingestion
	•	PDF → pages, sections, tables, spans
	•	Store in DuckDB
	2.	Minimal Retrieval
	•	BM25 over sections
	3.	RLM Controller (v1)
	•	Hard-coded traversal policy:
	•	find “Investment Objective” section
	•	find “Sustainability” sections
	•	find annex
	4.	Nemotron Worker
	•	Prompt templates for:
	•	extract sustainable investment definition
	•	detect DNSH presence
	5.	SFDRState Writer
	•	Write structured JSON into DuckDB

Deliverables
	•	DuckDB with:
	•	documents
	•	sections
	•	spans
	•	sfdr_states
	•	CLI:

python run_one_doc.py path/to/prospectus.pdf


	•	Output:
	•	sfdr_state.json
	•	evidence_pack.json

Acceptance Test
	•	On a real prospectus:
	•	correct extraction of definition
	•	citations point to correct page
	•	missing fields explicitly marked

⸻

Iteration 2 — One Fund, Multi-Document (3–4 weeks)

Objective

Prove cross-document reasoning and inconsistency detection.

Scope
	•	1 fund
	•	3 documents:
	•	prospectus
	•	annual report
	•	SFDR annex

New Components
	1.	FundContext
	•	Group documents by ISIN
	2.	RLM Controller (v2)
	•	Field-by-field goals:
	•	classification evidence
	•	definition
	•	DNSH
	•	PAI coverage
	•	For each field:
	•	retrieve candidates
	•	call Nemotron
	•	verify
	3.	Inconsistency Engine
	•	Compare:
	•	% sustainable across docs
	•	presence/absence of DNSH
	4.	Evidence Pack Exporter
	•	One JSON per fund

Deliverables
	•	fund_sfdr_state.json
	•	inconsistencies.json
	•	simple HTML or Streamlit page:
	•	show state
	•	show inconsistencies
	•	show citations

Acceptance Test
	•	At least one real inconsistency detected
	•	State assembled from >1 document

⸻

Iteration 3 — Versioning & Drift (4–6 weeks)

Objective

Prove continuous operation and drift detection.

Scope
	•	1–3 funds
	•	2 versions per document

New Components
	1.	Versioned Ingestion
	•	doc_id + version + checksum
	2.	Drift Engine
	•	Compare SFDRState vN vs vN+1
	•	Detect:
	•	numeric drift
	•	wording drift
	•	field disappearance
	3.	Alert Engine
	•	Generate DriftEvent
	•	Persist Alert
	4.	Scheduler
	•	Daily job:
	•	check for new version
	•	re-run pipeline

Deliverables
	•	drift_events table
	•	alerts table
	•	demo script:

python run_monitor.py



Acceptance Test
	•	Modify a document
	•	System detects drift
	•	Alert generated with old/new citations

⸻

10. DSPy Integration Strategy

DSPy is used to:
	•	Define program signatures:
	•	ExtractDefinition
	•	ExtractDNSH
	•	ExtractPAI
	•	VerifyConsistency
	•	Optimize:
	•	retrieval k
	•	prompt templates
	•	verification steps
	•	Evaluation set:
	•	10–20 labeled extraction cases

DSPy is introduced in Iteration 2, not Iteration 1.

⸻

11. Minimal Tech Stack
	•	Python 3.11
	•	DuckDB
	•	Unstructured / pdfplumber
	•	vLLM Nemotron on Koyeb
	•	DSPy
	•	APScheduler or BullMQ

⸻

12. Risks & Mitigations

Risk	Mitigation
Nemotron hallucinations	Add verifier step, conservative prompts
Table extraction errors	Pre-process tables with rule-based parser
Too many LLM calls	Hard budgets per run
Drift false positives	Thresholding + confidence scoring


⸻

13. Why This Is a Good Research Prototype
	•	Tests RLM in a real regulatory workload
	•	Tests Nemotron as a controllable worker
	•	Tests DSPy as pipeline compiler
	•	Produces measurable outcomes:
	•	precision
	•	recall
	•	drift recall
	•	cost per fund

⸻

14. Next Immediate Actions

Week 1:
	•	Finalize 1–2 funds dataset
	•	Implement ingestion + section model
	•	Wire Nemotron inference client

Week 2:
	•	Implement RLM v1 controller
	•	Extract 2–3 fields
	•	Build evidence pack export

Week 3:
	•	Stabilize pipeline
	•	Write first evaluation cases

