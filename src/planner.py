"""
Decomposes a legal question into sub-queries by source type.
Each sub-query becomes a separate retrieval call.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List


class SourceType(str, Enum):
    UU = "uu"  # Undang-Undang
    PERPRES = "perpres"
    PERMEN = "permen"
    MA_PUTUSAN = "ma_putusan"
    FATWA_MUI = "fatwa_mui"
    SE_OJK = "se_ojk"


@dataclass
class SubQuery:
    text: str
    source_types: List[SourceType]
    rationale: str


PLANNER_SYSTEM_PROMPT = """You are an expert Indonesian legal research planner.

Given a legal question, decompose it into 3–7 sub-queries. Each sub-query targets one or more source types: UU, Perpres, Permen, MA Putusan, Fatwa MUI, SE OJK.

Output strictly as JSON array, each item = {"text": str, "source_types": [str], "rationale": str}.

Rules:
- Statute interpretation questions need both the primary statute AND implementing regulations.
- Anything involving disputes between parties needs MA Putusan retrieval.
- Sharia or Islamic finance questions need Fatwa MUI alongside SE OJK.
- Never produce a sub-query without at least one source_type.
"""


def plan(question: str, llm_call) -> List[SubQuery]:
    """Decompose `question` into sub-queries via LLM call.

    `llm_call(system, user) -> str` is injected so callers can swap MiMo / Claude / vLLM.
    """
    raw = llm_call(PLANNER_SYSTEM_PROMPT, question)
    import json
    parsed = json.loads(raw)
    return [
        SubQuery(
            text=item["text"],
            source_types=[SourceType(s) for s in item["source_types"]],
            rationale=item["rationale"],
        )
        for item in parsed
    ]
