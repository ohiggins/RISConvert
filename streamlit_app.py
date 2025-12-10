#!/usr/bin/env python3
"""
Streamlit app to convert APA 7th references (pasted as text)
into a RIS file suitable for EndNote import.

Assumptions:
- One APA reference per line in the input box.
- Year appears as (YYYY).
- Title starts after the year and ends at the next period.
"""

import re
from io import StringIO
from typing import List, Dict

import streamlit as st


def detect_reference_type(original: str, after_year: str) -> str:
    """
    Detect reference type and return a RIS TY code.

    Returns:
        "JOUR" for journal articles
        "RPRT" for reports or institutional documents
        "ELEC" for web pages and news articles
    """
    low_original = original.lower()
    low_after = after_year.lower()

    # Journal article indicators
    if "doi.org" in low_original or "doi:" in low_original:
        return "JOUR"

    if re.search(r"\b\d+\(\d+\)\s*,\s*\d", original):
        # Example: 221(10), 524–526 (volume(issue), pages)
        return "JOUR"

    # Report or institutional document indicators
    institution_keywords = [
        "department",
        "commission",
        "council",
        "university",
        "unicef",
        "ministry",
        "office",
        "organisation",
        "organization",
        "government",
        "authority",
    ]
    report_markers = [
        "[press release]",
        "[advocacy",
        "submission to the",
        "briefing]",
        "technical report",
        "working paper",
        "policy paper",
    ]

    if any(kw in low_original for kw in institution_keywords) and any(
        m in low_original for m in report_markers
    ):
        return "RPRT"

    if any(kw in low_original for kw in institution_keywords) and "doi" not in low_original:
        return "RPRT"

    # Default to electronic
    return "ELEC"


def parse_apa_reference(line: str) -> Dict[str, str]:
    """
    Parse a single APA 7th reference into basic RIS fields.

    Extracts:
      TY - type (JOUR, RPRT, ELEC)
      AU - authors or corporate author
      PY - year (YYYY)
      TI - title segment
      UR - first URL
      N1 - full original reference

    Returns an empty dict if the line is empty.
    """
    original = line.strip()
    if not original:
        return {}

    record = {
        "TY": "GEN",
        "AU": None,
        "PY": None,
        "TI": None,
        "UR": None,
        "N1": original,
    }

    # Year as (YYYY)
    year_match = re.search(r"\((\d{4})\)", original)
    if not year_match:
        # Cannot identify a standard APA year
        return record

    year = year_match.group(1)
    record["PY"] = year

    # Authors or corporate author before the year
    authors = original[:year_match.start()].strip()
    if authors.endswith("."):
        authors = authors[:-1].strip()
    authors=authors+","
    record["AU"] = authors if authors else None

    # Text after the year
    after_year = original[year_match.end():].lstrip()

    # Remove leading period after the year if present
    if after_year.startswith("."):
        after_year = after_year[1:].lstrip()

    # Title is text up to the first period
    period_index = after_year.find(".")
    if period_index != -1:
        title = after_year[:period_index].strip()
        remainder = after_year[period_index + 1 :].strip()
    else:
        title = after_year.strip()
        remainder = ""

    record["TI"] = title if title else None

    # Type detection
    record["TY"] = detect_reference_type(original, after_year)

    # First URL, if present
    url_match = re.search(r"(https?://\S+)", original)
    if url_match:
        record["UR"] = url_match.group(1)

    return record


def record_to_ris(record: Dict[str, str]) -> str:
    """
    Convert a parsed record dict into a RIS formatted string.
    Only non-empty fields are written.
    """
    lines: List[str] = []
    ty = record.get("TY") or "GEN"
    lines.append(f"TY  - {ty}")

    if record.get("AU"):
        lines.append(f"AU  - {record['AU']}")

    if record.get("TI"):
        lines.append(f"TI  - {record['TI']}")

    if record.get("PY"):
        lines.append(f"PY  - {record['PY']}")

    if record.get("UR"):
        lines.append(f"UR  - {record['UR']}")

    if record.get("N1"):
        lines.append(f"N1  - {record['N1']}")

    lines.append("ER  - ")

    return "\n".join(lines) + "\n\n"


def references_text_to_ris(text: str) -> str:
    """
    Convert pasted text containing APA references to a RIS string.

    Assumes one complete reference per non-empty line.
    """
    ris_entries: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        record = parse_apa_reference(line)
        if not record:
            continue
        ris_entries.append(record_to_ris(record))

    return "".join(ris_entries)


# Streamlit UI

st.title("APA 7th References to RIS Converter")

st.write(
    "Paste APA 7th references below. Use one full reference per line. "
    "Click the button to generate a RIS file you can import into EndNote."
)

sample_text = (
    "Australian Human Rights Commission. (2024). Proposed social media ban for under-16s in Australia "
    "[News story]. Retrieved from https://humanrights.gov.au/about-us/news/proposed-social-media-ban-under-16s-australia\n"
    "Christensen, H., Slade, A., & Whitton, A. E. (2024). Social media: The root cause of rising youth self-harm "
    "or a convenient scapegoat? Medical Journal of Australia, 221(10), 524–526. https://doi.org/10.5694/mja2.52503"
)

input_text = st.text_area(
    "APA 7th references",
    value=sample_text,
    height=250,
)

if st.button("Convert to RIS"):
    if not input_text.strip():
        st.warning("Please paste at least one APA 7th reference.")
    else:
        ris_text = references_text_to_ris(input_text)
        if not ris_text.strip():
            st.error("No RIS output generated. Check that the references are in APA 7th format.")
        else:
            st.success("RIS output generated.")
            st.text_area("RIS output", value=ris_text, height=300)

            # Download button
            st.download_button(
                label="Download RIS file",
                data=ris_text.encode("utf-8"),
                file_name="references.ris",
                mime="application/x-research-info-systems",
            )

