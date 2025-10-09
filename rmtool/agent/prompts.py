"""
Prompt templates for the RMTool AI agent layer.

Provides reusable system prompts with version metadata and helper utilities
for formatting canonical genealogy workflows (biography, quality analysis,
timeline planning, and Q&A).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class FewShotExample:
    """Minimal representation of a few-shot example."""

    user: str
    assistant: str


@dataclass(frozen=True)
class PromptTemplate:
    """Prompt text with metadata."""

    key: str
    version: str
    description: str
    template: str
    few_shots: List[FewShotExample]

    def render(self, substitutions: Mapping[str, str]) -> str:
        """Render the prompt template with safe substitution."""

        class _SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        safe_values = _SafeDict(**substitutions)
        return self.template.format_map(safe_values)


PROMPT_VERSION = "2025-01-08"

BIOGRAPHY_TEMPLATE = PromptTemplate(
    key="biography",
    version=PROMPT_VERSION,
    description="Structured biography generation aligned with RM11 best practices.",
    template=(
        "You are a professional genealogist creating a narrative biography.\n"
        "Follow the standard ten-section outline from RM11_Biography_Best_Practices.md.\n"
        "Respond in Markdown with section headings and cite supporting Rootsmagic sources.\n\n"
        "Person Summary:\n{person_summary}\n\n"
        "Timeline Highlights:\n{timeline_overview}\n\n"
        "Key Relationships:\n{relationship_notes}\n\n"
        "Notable Sources:\n{source_notes}\n\n"
        "If data is missing, acknowledge gaps and suggest next research steps."
    ),
    few_shots=[
        FewShotExample(
            user="Summarize the biography for Carmen Henrietta Cecile White-Wright using the supplied timeline.",
            assistant=(
                "## Introduction\n"
                "Carmen Henrietta Cecile White-Wright was born on 12 March 1890 in Baltimore, "
                "Maryland, the daughter of John and Louisa White-Wright.\n\n"
                "## Early Life & Family Background\n"
                "Carmen grew up in a bilingual household in Baltimore alongside three siblings..."
            ),
        )
    ],
)

QUALITY_TEMPLATE = PromptTemplate(
    key="quality",
    version=PROMPT_VERSION,
    description="Analyze Rootsmagic quality issues using RM11_Data_Quality_Rules.md.",
    template=(
        "You are validating RootsMagic quality issues.\n"
        "Dataset summary:\n{quality_summary}\n\n"
        "Critical items:\n{critical_issues}\n\n"
        "High severity items:\n{high_issues}\n\n"
        "Medium severity items:\n{medium_issues}\n\n"
        "Low severity items:\n{low_issues}\n\n"
        "Explain the top issues, reference relevant rules, and recommend remediation steps."
    ),
    few_shots=[
        FewShotExample(
            user="Explain the most urgent quality fixes for the Iiams database.",
            assistant=(
                "- Rule 2.1 (Death before birth): 3 people require immediate verification.\n"
                "- Rule 4.1 (Unsourced vital events): 18,403 events lack citations.\n"
                "Recommend prioritizing death-before-birth conflicts before adding citations."
            ),
        )
    ],
)

QA_TEMPLATE = PromptTemplate(
    key="qa",
    version=PROMPT_VERSION,
    description="Conversational fact recall and explanation prompt.",
    template=(
        "You answer questions about RootsMagic data precisely and cite supporting facts.\n"
        "Question: {question}\n"
        "Context snippets:\n{context_snippets}\n"
        "Answer directly, list relevant events, and note citation IDs when available."
    ),
    few_shots=[
        FewShotExample(
            user="Who were Michael Dorsey Iams' parents?",
            assistant="Michael Dorsey Iams is recorded as the son of Donald Richard Iams and Gail Cynthia Shepherd (Citation 1184, Source 337).",
        )
    ],
)

TIMELINE_TEMPLATE = PromptTemplate(
    key="timeline",
    version=PROMPT_VERSION,
    description="Timeline synthesis instructions aligned with RM11_Timeline_Construction.md.",
    template=(
        "Create an annotated event timeline for TimelineJS3 export.\n"
        "Subject: {person_name}\n"
        "Events JSON:\n{events_json}\n"
        "Apply ordering rules (SortDate, event priority) and flag data gaps."
    ),
    few_shots=[
        FewShotExample(
            user="Draft a timeline summary for Donna Lynn Jones using supplied events.",
            assistant="1964-06-12 marriage in Maricopa County, Arizona (Marriage FactType 300). Annotate missing citations for the 1970 relocation event.",
        )
    ],
)

PROMPTS: Dict[str, PromptTemplate] = {
    tmpl.key: tmpl
    for tmpl in (
        BIOGRAPHY_TEMPLATE,
        QUALITY_TEMPLATE,
        QA_TEMPLATE,
        TIMELINE_TEMPLATE,
    )
}


def list_prompts() -> Iterable[str]:
    """Return available prompt keys."""

    return PROMPTS.keys()


def get_prompt(key: str) -> PromptTemplate:
    """Retrieve a prompt template by key."""

    try:
        return PROMPTS[key]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise KeyError(f"Unknown prompt key '{key}'. Available: {sorted(PROMPTS)}") from exc


def render_prompt(key: str, substitutions: Optional[Mapping[str, str]] = None) -> str:
    """Render a prompt by key with optional substitutions."""

    template = get_prompt(key)
    if not substitutions:
        substitutions = {}
    return template.render(substitutions)


__all__ = [
    "PromptTemplate",
    "FewShotExample",
    "render_prompt",
    "get_prompt",
    "list_prompts",
    "PROMPTS",
]
