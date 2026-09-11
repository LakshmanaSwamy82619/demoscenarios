"""Pure, testable helpers for natural-language querying of the Nexora graph:
schema text, prompt building, Cypher extraction, the read-only check, and
result formatting. Cypher generation and execution themselves (the calls to
the LLM and to Neo4j) live directly in 03_natural_language_querying.ipynb, not here, so
the class can see exactly what's happening at each step.
"""

import re

import pandas as pd

SCHEMA_DESCRIPTION = """Node labels (every node has a `name` property):
  Person, Company, Department, Project, Location, Client

Relationship types (all directed as shown):
  (Person)-[:IS_HEAD_OF]->(Department)
  (Person)-[:WORKS_IN]->(Department)
  (Department)-[:PART_OF]->(Company)
  (Company)-[:HEADQUARTERED_IN]->(Location)
  (Department)-[:BASED_IN]->(Location)
  (Person)-[:LEADS]->(Project)
  (Person)-[:WORKS_ON]->(Project)
  (Company)-[:PARTNERS_WITH]->(Client)
  (Project)-[:FOR_CLIENT]->(Client)"""

_FORBIDDEN_KEYWORDS = (
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP", "CALL", "LOAD CSV",
)
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE
)
_CODE_BLOCK_RE = re.compile(r"```(?:cypher)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def build_nl_to_cypher_prompt(question: str) -> str:
    return (
        "You translate natural-language questions into Cypher queries for a Neo4j graph.\n\n"
        f"Schema:\n{SCHEMA_DESCRIPTION}\n\n"
        "Rules:\n"
        "- Write exactly one read-only Cypher query (MATCH/WHERE/RETURN only, no writes).\n"
        "- Use only the labels, relationship types, and the `name` property listed above.\n"
        "- RETURN the name of every node you filter or match on, not just the node(s) being asked\n"
        "  about — the results must be self-explanatory on their own, without needing to re-read\n"
        "  the query, since whoever reads them won't see this query, only its results.\n"
        "- Respond with ONLY the Cypher query in a ```cypher fenced code block, nothing else.\n\n"
        f"Question: {question}"
    )


def extract_cypher(response_text: str) -> str:
    """Pull the Cypher out of a ```cypher fenced block; fall back to the raw text."""
    match = _CODE_BLOCK_RE.search(response_text)
    return (match.group(1) if match else response_text).strip()


def is_read_only(cypher: str) -> bool:
    """True if the query contains none of the write/admin keywords in _FORBIDDEN_KEYWORDS."""
    return _FORBIDDEN_RE.search(cypher) is None


def format_query_results(results_df: pd.DataFrame) -> str:
    """Turn a Cypher query's result rows into a fact list for the answer step."""
    if results_df.empty:
        return "The query returned no results."
    lines = [
        "- " + ", ".join(f"{column}: {value}" for column, value in row.items())
        for _, row in results_df.iterrows()
    ]
    return "Query results:\n" + "\n".join(lines)
