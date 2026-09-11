"""Shared Neo4j connection helper, used by 02_graph_augmented_qa.ipynb and
03_natural_language_querying.ipynb (01_pdf_to_knowledge_graph.ipynb sets up its own connection
inline instead, so you can see every step in one place there).
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase, TrustCustomCAs, TrustSystemCAs

_NETSKOPE_BUNDLE = os.path.expanduser(r"~\certs\combined-ca-bundle.pem")


def get_driver():
    """Connect to Neo4j Aura, working around this machine's Netskope TLS interception
    (see 01_pdf_to_knowledge_graph.ipynb Section 2 for the full explanation)."""
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USERNAME"]
    password = os.environ["NEO4J_PASSWORD"]

    trusted_certificates = (
        TrustCustomCAs(_NETSKOPE_BUNDLE) if os.path.exists(_NETSKOPE_BUNDLE) else TrustSystemCAs()
    )
    unencrypted_scheme_uri = uri.replace("neo4j+s://", "neo4j://").replace("neo4j+ssc://", "neo4j://")

    driver = GraphDatabase.driver(
        unencrypted_scheme_uri,
        auth=(username, password),
        encrypted=True,
        trusted_certificates=trusted_certificates,
    )
    driver.verify_connectivity()
    return driver
