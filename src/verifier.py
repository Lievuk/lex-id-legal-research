"""
Verifier: re-reads every citation in the synthesized answer to make sure it matches
the retrieved source. Hallucinated citations are stripped.
"""
import re
from dataclasses import dataclass
from typing import List, Dict


CITATION_PATTERNS = [
    re.compile(r"UU\s+No\.?\s*(\d+)\s+Tahun\s+(\d{4})\s+Pasal\s+(\d+[a-z]?)", re.I),
    re.compile(r"Perpres\s+No\.?\s*(\d+)\s+Tahun\s+(\d{4})", re.I),
    re.compile(r"Putusan\s+MA\s+No\.?\s*([\w/\.\-]+)", re.I),
]


@dataclass
class Citation:
    raw: str
    parsed: Dict[str, str]
    verified: bool
    matched_doc_id: str | None


def extract_citations(answer: str) -> List[Citation]:
    out: List[Citation] = []
    for pat in CITATION_PATTERNS:
        for m in pat.finditer(answer):
            out.append(Citation(
                raw=m.group(0),
                parsed={f"g{i}": v for i, v in enumerate(m.groups())},
                verified=False,
                matched_doc_id=None,
            ))
    return out


def verify_against_retrieved(citations: List[Citation], retrieved_docs: List[dict]) -> List[Citation]:
    """Mark each citation `verified=True` only if at least one retrieved doc matches."""
    by_id = {d["doc_id"]: d for d in retrieved_docs}
    for cit in citations:
        for doc_id, doc in by_id.items():
            if cit.raw.lower() in doc["text"].lower():
                cit.verified = True
                cit.matched_doc_id = doc_id
                break
    return citations


def strip_unverified(answer: str, citations: List[Citation]) -> str:
    """Replace unverified citations with [REJECTED-CITATION] so the user sees the gap."""
    out = answer
    for cit in citations:
        if not cit.verified:
            out = out.replace(cit.raw, "[REJECTED-CITATION]")
    return out
