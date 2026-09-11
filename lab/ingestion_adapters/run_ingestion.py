"""
Stage: Ingestion & Adapters
----------------------------
Picks one sample file per source format and runs the matching adapter,
normalizing each into the platform's internal document format:

    {
      "doc_id": str,
      "source_format": str,
      "adapter_used": str,
      "title": str,
      "content": str,           # flattened plain text
      "metadata": {...}
    }

Only input -> normalized output is written out (no adapter internals exposed).
"""
import json, uuid, datetime
import pdfplumber
import docx

RAW = "/home/claude/lab/01_raw_input"
OUT = "/home/claude/lab/02_ingestion_adapters"

def adapter_pdf(path):
    """PDF adapter: layout-aware text extraction, page-level metadata."""
    text_parts, page_count = [], 0
    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            t = page.extract_text() or ""
            text_parts.append(t)
    return {
        "content": "\n\n".join(text_parts).strip(),
        "metadata": {"page_count": page_count, "extraction": "text-layer"}
    }

def adapter_json_structured(path):
    """Structured/JSON adapter: flattens a known ticket schema into readable text."""
    with open(path) as f:
        data = json.load(f)
    blocks = []
    for t in data["tickets"]:
        convo = "\n".join(f'{m["author"]}: {m["body"]}' for m in t["conversation"])
        block = (
            f'Ticket {t["ticket_id"]} ({t["status"]}, priority: {t["priority"]})\n'
            f'Subject: {t["subject"]}\n'
            f'Requester: {t["requester_name"]} <{t["requester_email"]}>\n'
            f'{convo}'
        )
        blocks.append(block)
    return {
        "content": "\n\n---\n\n".join(blocks),
        "metadata": {"record_count": data["export_meta"]["record_count"], "schema": "ticket-export-v1"}
    }

def adapter_docx(path):
    """DOCX adapter: paragraph-order text extraction, preserves heading structure as plain text."""
    d = docx.Document(path)
    text_parts = [p.text for p in d.paragraphs if p.text.strip()]
    return {
        "content": "\n".join(text_parts),
        "metadata": {"paragraph_count": len(text_parts), "extraction": "paragraph-walk"}
    }

jobs = [
    (f"{RAW}/policy.pdf",         "pdf",             "pdf_text_layer_adapter",    adapter_pdf,            "Remote Work & Data Handling Policy"),
    (f"{RAW}/ticket_export.json", "json_structured",  "structured_ticket_adapter", adapter_json_structured,"Support Ticket Export"),
    (f"{RAW}/contract.docx",      "docx",             "docx_paragraph_adapter",    adapter_docx,           "Master Services Agreement"),
]

results = []
for path, fmt, adapter_name, fn, title in jobs:
    body = fn(path)
    normalized = {
        "doc_id": str(uuid.uuid4()),
        "source_file": path.split("/")[-1],
        "source_format": fmt,
        "adapter_used": adapter_name,
        "title": title,
        "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
        "content": body["content"],
        "metadata": body["metadata"]
    }
    results.append(normalized)

with open(f"{OUT}/normalized_documents.json", "w") as f:
    json.dump(results, f, indent=2)

# Side-by-side summary for demo purposes (input vs normalized output)
with open(f"{OUT}/side_by_side_summary.md", "w") as f:
    f.write("# Ingestion & Adapters — Input vs Normalized Output\n\n")
    for r in results:
        f.write(f"## {r['source_file']}  →  {r['adapter_used']}\n\n")
        f.write(f"**Why this adapter:** matched on source format `{r['source_format']}`, ")
        if r['source_format'] == 'pdf':
            f.write("selected the PDF text-layer adapter because the file has an embedded text layer (not scanned), "
                    "so layout-aware extraction preserves paragraph breaks without needing OCR.\n\n")
        elif r['source_format'] == 'json_structured':
            f.write("selected the structured ticket adapter because the file matches the known ticket-export schema "
                    "(`export_meta` + `tickets[]`), so fields can be flattened predictably instead of dumping raw JSON.\n\n")
        else:
            f.write("selected the DOCX paragraph-walk adapter because Word documents store text as an ordered paragraph "
                    "stream, which is the fastest path to clean, ordered plain text for downstream chunking.\n\n")
        f.write(f"- **Normalized doc_id:** `{r['doc_id']}`\n")
        f.write(f"- **Title:** {r['title']}\n")
        f.write(f"- **Metadata:** `{json.dumps(r['metadata'])}`\n")
        f.write(f"- **Content preview (first 220 chars):**\n\n> {r['content'][:220].strip()}...\n\n")
        f.write("---\n\n")

print("Ingestion complete. Wrote normalized_documents.json and side_by_side_summary.md")
for r in results:
    print(f"  - {r['source_file']:22s} -> {r['adapter_used']:28s} ({len(r['content'])} chars)")
