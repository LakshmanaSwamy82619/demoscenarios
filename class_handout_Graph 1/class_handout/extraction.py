"""Rule-based (regex) extraction of entities and relationships from plain text.

Deliberately simple/deterministic rather than NLP- or LLM-based, so it is easy
to narrate live in a talk and easy to unit test. Each `extract_*` function
targets one fixed sentence pattern found in content.COMPANY_PROFILE_TEXT.
"""

import re

import pandas as pd

_WHITESPACE_RE = re.compile(r"\s+")

_HEAD_OF_DEPARTMENT_RE = re.compile(
    r"([A-Z][a-zA-Z'-]+ [A-Z][a-zA-Z'-]+) is the (Head) of ([A-Za-z ]+?) at ([A-Za-z ]+?)\."
)
_STAFF_DEPARTMENT_RE = re.compile(
    r"([A-Z][a-zA-Z'-]+ [A-Z][a-zA-Z'-]+) works in the ([A-Za-z ]+?) department at ([A-Za-z ]+?)\."
)
_COMPANY_LOCATION_RE = re.compile(
    r"([A-Z][a-zA-Z ]+?) is headquartered in ([A-Za-z, ]+?)\."
)
_DEPARTMENT_LOCATION_RE = re.compile(
    r"The ([A-Za-z ]+?) department is based in ([A-Za-z, ]+?)\."
)
_PROJECT_LEAD_RE = re.compile(
    r"The ([A-Za-z]+) project is led by ([A-Z][a-zA-Z'-]+ [A-Z][a-zA-Z'-]+)\."
)
_PROJECT_WORKER_RE = re.compile(
    r"([A-Z][a-zA-Z'-]+ [A-Z][a-zA-Z'-]+) works on the ([A-Za-z]+) project\."
)
_PARTNERSHIP_RE = re.compile(
    r"([A-Z][a-zA-Z ]+?) partners with ([A-Za-z ]+?) on the ([A-Za-z]+) project\."
)


def clean_text(raw_text: str) -> str:
    """Collapse newlines/repeated whitespace from PDF-extracted text into single spaces."""
    return _WHITESPACE_RE.sub(" ", raw_text).strip()


def extract_head_of_department(text: str) -> list[dict]:
    """Match "<person> is the Head of <department> at <company>." sentences."""
    return [
        {"person": person, "department": department.strip(), "company": company.strip()}
        for person, _role, department, company in _HEAD_OF_DEPARTMENT_RE.findall(text)
    ]


def extract_staff_department(text: str) -> list[dict]:
    """Match "<person> works in the <department> department at <company>." sentences."""
    return [
        {"person": person, "department": department.strip(), "company": company.strip()}
        for person, department, company in _STAFF_DEPARTMENT_RE.findall(text)
    ]


def extract_company_location(text: str) -> list[dict]:
    """Match "<company> is headquartered in <location>." sentences."""
    return [
        {"company": company.strip(), "location": location.strip()}
        for company, location in _COMPANY_LOCATION_RE.findall(text)
    ]


def extract_department_location(text: str) -> list[dict]:
    """Match "The <department> department is based in <location>." sentences."""
    return [
        {"department": department.strip(), "location": location.strip()}
        for department, location in _DEPARTMENT_LOCATION_RE.findall(text)
    ]


def extract_project_leads(text: str) -> list[dict]:
    """Match "The <project> project is led by <person>." sentences."""
    return [
        {"project": project.strip(), "person": person}
        for project, person in _PROJECT_LEAD_RE.findall(text)
    ]


def extract_project_workers(text: str) -> list[dict]:
    """Match "<person> works on the <project> project." sentences."""
    return [
        {"person": person, "project": project.strip()}
        for person, project in _PROJECT_WORKER_RE.findall(text)
    ]


def extract_partnerships(text: str) -> list[dict]:
    """Match "<company> partners with <client> on the <project> project." sentences."""
    return [
        {"company": company.strip(), "client": client.strip(), "project": project.strip()}
        for company, client, project in _PARTNERSHIP_RE.findall(text)
    ]


def build_entities_and_relationships(raw_text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run all extractors over `raw_text` and normalize the results into two tables.

    Returns:
        entities: columns [name, type]
        relationships: columns [source, source_type, rel_type, target, target_type]
    """
    text = clean_text(raw_text)

    heads = extract_head_of_department(text)
    staff = extract_staff_department(text)
    company_locations = extract_company_location(text)
    department_locations = extract_department_location(text)
    project_leads = extract_project_leads(text)
    project_workers = extract_project_workers(text)
    partnerships = extract_partnerships(text)

    entities: set[tuple[str, str]] = set()
    relationships: list[tuple[str, str, str, str, str]] = []

    for row in heads:
        entities.add((row["person"], "Person"))
        entities.add((row["department"], "Department"))
        entities.add((row["company"], "Company"))
        relationships.append((row["person"], "Person", "IS_HEAD_OF", row["department"], "Department"))
        relationships.append((row["department"], "Department", "PART_OF", row["company"], "Company"))

    for row in staff:
        entities.add((row["person"], "Person"))
        entities.add((row["department"], "Department"))
        entities.add((row["company"], "Company"))
        relationships.append((row["person"], "Person", "WORKS_IN", row["department"], "Department"))
        relationships.append((row["department"], "Department", "PART_OF", row["company"], "Company"))

    for row in company_locations:
        entities.add((row["company"], "Company"))
        entities.add((row["location"], "Location"))
        relationships.append((row["company"], "Company", "HEADQUARTERED_IN", row["location"], "Location"))

    for row in department_locations:
        entities.add((row["department"], "Department"))
        entities.add((row["location"], "Location"))
        relationships.append((row["department"], "Department", "BASED_IN", row["location"], "Location"))

    for row in project_leads:
        entities.add((row["person"], "Person"))
        entities.add((row["project"], "Project"))
        relationships.append((row["person"], "Person", "LEADS", row["project"], "Project"))

    for row in project_workers:
        entities.add((row["person"], "Person"))
        entities.add((row["project"], "Project"))
        relationships.append((row["person"], "Person", "WORKS_ON", row["project"], "Project"))

    for row in partnerships:
        entities.add((row["company"], "Company"))
        entities.add((row["client"], "Client"))
        entities.add((row["project"], "Project"))
        relationships.append((row["company"], "Company", "PARTNERS_WITH", row["client"], "Client"))
        relationships.append((row["project"], "Project", "FOR_CLIENT", row["client"], "Client"))

    entities_df = pd.DataFrame(sorted(entities), columns=["name", "type"])
    relationships_df = pd.DataFrame(
        relationships, columns=["source", "source_type", "rel_type", "target", "target_type"]
    ).drop_duplicates().reset_index(drop=True)

    return entities_df, relationships_df
