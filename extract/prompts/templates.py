#!/usr/bin/env python3
"""
templates.py --- prompt templates for SPO triple extraction across domains

Contains:
    SYSTEM_PROMPT: base instruction framing the extraction task
    EXTRACTION_RULES: hard output rules every prompt repeats
    format_rules(): renders the rule list as a numbered block
    build_extraction_prompt(): assembles the full prompt
    FEW_SHOT_EXAMPLE_TECHNICAL: worked example for technical docs
    FEW_SHOT_EXAMPLE_NEWS: worked example for news prose
    FEW_SHOT_EXAMPLES: registry of worked examples
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extract.prompts.config import PromptConfig

SYSTEM_PROMPT = (
    "You are an information-extraction engine. Extract "
    "subject-predicate-object triples from the supplied text, covering every "
    "relationship the text mentions or implies."
)

EXTRACTION_RULES = [
    "Return a JSON array; each element is one triple.",
    "Each triple has subject, predicate, and object keys.",
    "Subjects and objects have name and entity_type keys.",
    "Predicates are short verb phrases, at most five tokens.",
    "Include a confidence score between 0.0 and 1.0 per triple.",
    "Do not emit duplicates or self-loops.",
]


def format_rules(rules: list[str]) -> str:
    """Renders extraction rules as a numbered prompt block.

    Args:
        rules: Rule strings to enumerate.

    Returns:
        block: Newline-joined numbered rules.
    """
    return "\n".join(f"{position}. {rule}" for position, rule in enumerate(rules, 1))


def build_extraction_prompt(text: str, config: "PromptConfig | None" = None) -> str:
    """Assembles the full extraction prompt for one text window.

    Args:
        text: Text window the model should extract triples from.
        config: Prompt configuration; defaults are used when omitted.

    Returns:
        prompt: System prompt, rules, examples, and the target text.
    """
    from extract.prompts.config import load_prompt_config

    active = config or load_prompt_config()
    sections = [SYSTEM_PROMPT, format_rules(EXTRACTION_RULES)]
    sections.append(format_few_shot(FEW_SHOT_EXAMPLES[: active.few_shot_count]))
    sections.append(f"Text:\n{text}\n\nTriples JSON:")
    return "\n\n".join(sections)


FEW_SHOT_EXAMPLE_TECHNICAL: dict[str, object] = {
    "domain": "technical",
    "input": "Kafka Connect ships with RabbitMQ. RabbitMQ depends on Erlang.",
    "output": [
        {
            "subject": {"name": "Kafka Connect", "entity_type": "SOFTWARE"},
            "predicate": "ships with",
            "object": {"name": "RabbitMQ", "entity_type": "SOFTWARE"},
            "confidence": 0.95,
        },
        {
            "subject": {"name": "RabbitMQ", "entity_type": "SOFTWARE"},
            "predicate": "depends on",
            "object": {"name": "Erlang", "entity_type": "SOFTWARE"},
            "confidence": 0.97,
        },
    ],
}

FEW_SHOT_EXAMPLE_NEWS: dict[str, object] = {
    "domain": "news",
    "input": "Acme acquired ByteWorks on Tuesday. ByteWorks was founded by Ada Reyes.",
    "output": [
        {
            "subject": {"name": "Acme", "entity_type": "ORG"},
            "predicate": "acquired",
            "object": {"name": "ByteWorks", "entity_type": "ORG"},
            "confidence": 0.98,
        },
        {
            "subject": {"name": "Ada Reyes", "entity_type": "PERSON"},
            "predicate": "founded",
            "object": {"name": "ByteWorks", "entity_type": "ORG"},
            "confidence": 0.96,
        },
    ],
}

FEW_SHOT_EXAMPLES = [FEW_SHOT_EXAMPLE_TECHNICAL, FEW_SHOT_EXAMPLE_NEWS]
