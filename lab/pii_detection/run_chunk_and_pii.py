"""
Stage: Chunking + PII Detection
--------------------------------
1. Chunks each normalized document (simple paragraph-aware windowing).
2. Scans chunk text for the seeded PII types: person names, emails,
   an account number, and a dummy SSN-shaped value.
3. Applies a per-field-type handling policy (redact / mask / tokenize)
   and writes a checklist of what was caught vs missed.

Only detection INPUT (chunk text) and OUTPUT (finding + treated text) are
shown in the summary — the matching internals are not exposed there.
"""
import json, re, hashlib

IN_FILE = "/home/claude/lab/02_ingestion_adapters/normalized_documents.json"
OUT = "/home/claude/lab/03_pii_detection"

with open(IN_FILE) as f:
    docs = json.load(f)

# ---- Chunking (simple, paragraph/sentence-aware, ~400 char target) ----
def chunk_text(text, doc_id, target_len=400):
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) + 1 > target_len and buf:
            chunks.append(buf.strip())
            buf = ""
        buf += (p + "\n")
    if buf.strip():
        chunks.append(buf.strip())
    return [
        {"chunk_id": f"{doc_id[:8]}-c{i}", "doc_id": doc_id, "text": c}
        for i, c in enumerate(chunks)
    ]

all_chunks = []
for d in docs:
    all_chunks.extend(chunk_text(d["content"], d["doc_id"]))

# ---- PII detectors (regex-based; seeded-field oriented) ----
PATTERNS = {
    "EMAIL":   re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "SSN":     re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "ACCOUNT_NUMBER": re.compile(r"\bAC-\d{5}-\d{4}\b"),
    # Simple full-name heuristic: two or three capitalized tokens in a row,
    # excluded from doc titles/headings by checking against a stoplist of
    # known non-name capitalized phrases seen in this dataset.
    "PERSON_NAME": re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b"),
}
NAME_STOPLIST = {
    "Remote Work", "Data Handling", "Information Security", "Master Services",
    "Northgate Analytics", "Client Billing", "Authorized Billing",
    "Support Ticket", "End of", "Provider Email", "Client Email",
}

# Field-type handling policy
HANDLING_POLICY = {
    "EMAIL": "mask",             # keep domain, mask local-part -> useful for routing/debugging without exposing identity
    "SSN": "redact",             # full removal, highest sensitivity, no legitimate downstream use in this pipeline
    "ACCOUNT_NUMBER": "tokenize",# replace with reversible token -> billing systems may need to re-resolve it later
    "PERSON_NAME": "mask",       # keep first initial for readability, mask remainder -> preserves searchability by role
}

def treat(field_type, value):
    if HANDLING_POLICY[field_type] == "redact":
        return "[REDACTED]"
    if HANDLING_POLICY[field_type] == "mask":
        if field_type == "EMAIL":
            local, _, domain = value.partition("@")
            return (local[0] if local else "*") + "*" * max(len(local)-1, 1) + "@" + domain
        if field_type == "PERSON_NAME":
            parts = value.split()
            return parts[0][0] + "." + " ".join("*" * len(p) for p in parts[1:])
    if HANDLING_POLICY[field_type] == "tokenize":
        token = "TOK_" + hashlib.sha256(value.encode()).hexdigest()[:10].upper()
        return token
    return value

findings = []
treated_chunks = []
for c in all_chunks:
    text = c["text"]
    treated_text = text
    for field_type, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            val = m.group(0)
            if field_type == "PERSON_NAME" and val in NAME_STOPLIST:
                continue
            treated_val = treat(field_type, val)
            findings.append({
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "field_type": field_type,
                "original_value": val,
                "handling": HANDLING_POLICY[field_type],
                "treated_value": treated_val,
            })
            treated_text = treated_text.replace(val, treated_val)
    treated_chunks.append({**c, "treated_text": treated_text})

with open(f"{OUT}/chunks.json", "w") as f:
    json.dump(all_chunks, f, indent=2)
with open(f"{OUT}/pii_findings.json", "w") as f:
    json.dump(findings, f, indent=2)
with open(f"{OUT}/chunks_treated.json", "w") as f:
    json.dump(treated_chunks, f, indent=2)

# ---- Seeded PII checklist (what we planted vs what was caught) ----
SEEDED = [
    ("PERSON_NAME", "Marcus Ellery Whitfield"),
    ("PERSON_NAME", "Renata Ocasio Silva"),
    ("PERSON_NAME", "David Whitfield"),
    ("PERSON_NAME", "Sofia Alvarez"),
    ("PERSON_NAME", "Priya Raghunathan"),
    ("EMAIL", "marcus.whitfield@clientcorp.com"),
    ("EMAIL", "renata.silva@northgateanalytics.com"),
    ("EMAIL", "priya.raghunathan@example.com"),
    ("EMAIL", "d.whitfield@example.com"),
    ("EMAIL", "sofia.alvarez@example.com"),
    ("ACCOUNT_NUMBER", "AC-88214-7743"),
    ("SSN", "512-04-8891"),
    ("SSN", "512048891"),  # same ID, no-dash format — intentionally seeded to test regex boundary
]
caught_values = {(f["field_type"], f["original_value"]) for f in findings}
checklist = []
for field_type, val in SEEDED:
    caught = (field_type, val) in caught_values
    checklist.append({"field_type": field_type, "seeded_value": val, "caught": caught})

with open(f"{OUT}/seeded_pii_checklist.json", "w") as f:
    json.dump(checklist, f, indent=2)

missed = [c for c in checklist if not c["caught"]]
print(f"Chunked into {len(all_chunks)} chunks across {len(docs)} documents.")
print(f"PII findings: {len(findings)}")
print(f"Seeded PII: {len(checklist)} total, {len(checklist)-len(missed)} caught, {len(missed)} missed")
for m in missed:
    print(f"  MISSED: {m['field_type']} -> {m['seeded_value']}")
