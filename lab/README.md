# L100 Core Engineer — Day 1 Lab: Trace a Document Through the Pipeline

**Dataset used (deliberately the messier of the three, per facilitator guidance):**
the **contract doc**, seeded with five person names, five emails, one account
number, and an SSN-shaped value planted in *two* formats (dashed and non-dashed)
to create a genuine edge case at the PII stage. Run alongside the policy PDF and
the structured ticket JSON so all three source formats hit the pipeline.

```
lab/
├── 01_raw_input/                  the 3 source files + generator scripts
│   ├── policy.pdf
│   ├── ticket_export.json
│   └── contract.docx
├── 02_ingestion_adapters/         Stage 1 output
│   ├── normalized_documents.json
│   └── side_by_side_summary.md    <- input vs normalized output, per adapter
├── 03_pii_detection/              Stage 2 output
│   ├── chunks.json                 raw chunks
│   ├── pii_findings.json           every PII hit, field type + handling
│   ├── chunks_treated.json         chunks after redact/mask/tokenize
│   ├── seeded_pii_checklist.json   12/13 caught, 1 deliberate miss
│   └── pii_demo_writeup.md        <- talking points for the station demo
└── 04_knowledge_service/          Stage 3 output
    ├── query_result.json
    └── query_demo.md              <- query -> answer -> traced source chunk
```

## Stage 1 — Ingestion & Adapters

| Source file | Format | Adapter selected | Why |
|---|---|---|---|
| `policy.pdf` | PDF | `pdf_text_layer_adapter` | Has an embedded text layer (not scanned) — layout-aware extraction avoids needing OCR. |
| `ticket_export.json` | structured JSON | `structured_ticket_adapter` | Matches the known ticket-export schema, so fields flatten predictably instead of raw JSON dump. |
| `contract.docx` | DOCX | `docx_paragraph_adapter` | Word stores text as an ordered paragraph stream — fastest path to clean, ordered plain text for chunking. |

See `02_ingestion_adapters/side_by_side_summary.md` for the input/output pairing per file.

## Stage 2 — PII Detection

- 13 PII instances seeded across the dataset, **12 caught / 1 missed**.
- The miss: a backup tax identifier written without dashes (`512048891`) — same
  underlying value as the correctly-caught dashed SSN, but outside the detector's
  pattern shape. Kept in deliberately to have something real to discuss at the
  "note anything missed" checkpoint.
- Handling policy applied per field type:
  - **EMAIL → mask** (keep domain for triage signal, hide the individual)
  - **SSN → redact** (highest sensitivity, no downstream use case)
  - **ACCOUNT_NUMBER → tokenize** (billing may need to re-resolve it later)
  - **PERSON_NAME → mask** (keep first initial for readability/search)

Full justification and a worked caught/missed example: `03_pii_detection/pii_demo_writeup.md`.

## Stage 3 — Knowledge Service & Query

**Query:** How long must confidential data be encrypted in transit and what protocol is required?

**Answer:** Restricted data in transit must be encrypted using TLS 1.2 or higher;
confidential data may be cached locally for a maximum of 24 hours and must be
cleared automatically when the device is idle.

**Traced source chunk:** `776325c7-c2` (policy.pdf, similarity 0.2827) — see
`04_knowledge_service/query_demo.md` for the exact chunk text it resolved to.

## Wrap-up talking points

- **Adapter fit:** each format got a purpose-built adapter rather than one generic
  parser — the schema/structure of the source is what decided the adapter, not the
  file extension alone.
- **Chunking choice to compare with the other pair:** paragraph-aware windowing at
  ~400 chars, no overlap. Worth comparing against a pair that used fixed-token
  windows with overlap — different trade-offs for recall vs boundary-splitting PII.
- **Detection limits are real:** the one deliberate miss is a good discussion seed
  — regex-only detectors are shape-anchored, so format drift (missing separators,
  OCR artifacts, alternate spellings) is the most common way PII slips through.
- **Traceability:** the knowledge-service answer carries its exact source chunk id
  back to the originating document, which is what Day 2's observability lab will
  build on.

This dataset (`lab/`) is what carries forward into Day 2 (graph, governance,
observability) and Day 3 (use-case/agent build) — keep this login handy.
