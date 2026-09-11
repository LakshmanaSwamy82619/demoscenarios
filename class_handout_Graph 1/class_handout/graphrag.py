"""Graph-augmented Q&A: prompt-building and Azure OpenAI helpers.

The Cypher-querying functions (fetch_person_context, fetch_path_context) live
directly in 02_graph_augmented_qa.ipynb, not here, so the class can see exactly
what's sent to Neo4j. This module only holds the LLM plumbing and the pure
formatting/prompt logic around it.
"""

import os

import httpx
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

from graph_ops import _NETSKOPE_BUNDLE


def get_llm_client() -> AzureOpenAI:
    """Azure OpenAI client, working around this machine's Netskope TLS interception."""
    load_dotenv()
    verify = _NETSKOPE_BUNDLE if os.path.exists(_NETSKOPE_BUNDLE) else True
    return AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        http_client=httpx.Client(verify=verify),
    )


def get_deployment_name() -> str:
    load_dotenv()
    return os.environ["AZURE_OPENAI_DEPLOYMENT"]


def format_person_context(person_name: str, context_df: pd.DataFrame) -> str:
    if context_df.empty:
        return f"No graph facts found for {person_name}."
    facts = "\n".join(f"- {row.type}: {row.name}" for row in context_df.itertuples())
    return f"Facts about {person_name}, from the graph:\n{facts}"


def format_path_context(person_a: str, person_b: str, steps: list[str]) -> str:
    if not steps:
        return f"No connection found in the graph between {person_a} and {person_b}."
    return "Shortest connection path in the graph:\n" + " -> ".join(steps)


def build_prompt(question: str, context: str | None) -> str:
    if context is None:
        return question
    return (
        "Answer the question using ONLY the facts below. "
        "If the facts don't cover it, say so explicitly.\n\n"
        f"Facts:\n{context}\n\nQuestion: {question}"
    )


def ask_llm(client: AzureOpenAI, question: str, context: str | None = None) -> str:
    response = client.chat.completions.create(
        model=get_deployment_name(),
        max_completion_tokens=300,
        messages=[{"role": "user", "content": build_prompt(question, context)}],
    )
    return response.choices[0].message.content
