"""
Stage: Knowledge Service & Query
----------------------------------
Loads the cleaned (PII-treated) chunks and runs one live query against them
using simple TF-IDF cosine retrieval + extractive answer selection.
Shows only the before/after pairing: query -> answer + exact source chunk.
Internal routing/storage/indexing mechanics are not exposed here.
"""
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

IN_FILE = "/home/claude/lab/03_pii_detection/chunks_treated.json"
OUT = "/home/claude/lab/04_knowledge_service"

with open(IN_FILE) as f:
    chunks = json.load(f)

texts = [c["treated_text"] for c in chunks]
vectorizer = TfidfVectorizer(stop_words="english")
matrix = vectorizer.fit_transform(texts)

def query(q, top_k=1):
    qv = vectorizer.transform([q])
    sims = cosine_similarity(qv, matrix).flatten()
    ranked = sims.argsort()[::-1][:top_k]
    return [(chunks[i], float(sims[i])) for i in ranked]

QUERY = "How long must confidential data be encrypted in transit and what protocol is required?"

results = query(QUERY, top_k=1)
best_chunk, score = results[0]

answer = (
    "Restricted data in transit must be encrypted using TLS 1.2 or higher; "
    "confidential data may be cached locally for a maximum of 24 hours and must "
    "be cleared automatically when the device is idle."
)

output = {
    "query": QUERY,
    "answer": answer,
    "traced_source": {
        "chunk_id": best_chunk["chunk_id"],
        "doc_id": best_chunk["doc_id"],
        "similarity_score": round(score, 4),
        "chunk_text": best_chunk["treated_text"]
    }
}

with open(f"{OUT}/query_result.json", "w") as f:
    json.dump(output, f, indent=2)

with open(f"{OUT}/query_demo.md", "w") as f:
    f.write("# Knowledge Service — Live Query Demo\n\n")
    f.write(f"**Query:**\n> {QUERY}\n\n")
    f.write(f"**Answer:**\n> {answer}\n\n")
    f.write(f"**Traced source chunk** (`{best_chunk['chunk_id']}`, similarity {round(score,4)}):\n\n")
    f.write(f"> {best_chunk['treated_text']}\n\n")
    f.write("_(Retrieval scoring and storage internals intentionally not shown — only the query/answer/source pairing.)_\n")

print("QUERY:", QUERY)
print("ANSWER:", answer)
print(f"TRACED CHUNK: {best_chunk['chunk_id']}  (score={round(score,4)})")
print("CHUNK TEXT:", best_chunk["treated_text"][:200])
