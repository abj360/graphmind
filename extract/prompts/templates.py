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
    format_few_shot(): renders worked examples as prompt text
    DOMAIN_HINT_TECHNICAL: extraction guidance for technical docs
    DOMAIN_HINT_NEWS: extraction guidance for news prose
    DOMAIN_HINT_BIOMEDICAL: extraction guidance for biomedical text
    DOMAIN_HINTS: domain key to hint text mapping
    render_domain_hint(): looks up the hint for a domain
    predicate_guidance(): suggests predicate phrasing per domain
    DEFAULT_FEW_SHOT_COUNT: examples included by default
    estimate_prompt_tokens(): rough token estimate for a prompt
    validate_domain(): rejects unsupported domain keys
    list_available_domains(): reports registered domain keys
    select_examples(): chooses worked examples for a config
    summarize_template(): one-line description of the template set
    TEMPLATE_VERSION: semantic version of the prompt set
    CITATION_REQUIREMENT: mandatory source-span citation block
    CITATION_FEW_SHOT_EXAMPLE: worked example with citations
    citation_block(): renders the citation requirement block
    merge_domain_hints(): combines hints for compound domains
    validate_few_shot_examples(): sanity-checks the example registry
    render_prompt_preview(): abbreviated prompt for debugging
    template_hash(): content fingerprint of the template set
    reload_templates(): re-reads templates after an edit
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


def format_few_shot(examples: list[dict[str, object]]) -> str:
    """Renders worked examples as demonstration blocks for the prompt.

    Args:
        examples: Example mappings with input and output keys.

    Returns:
        block: Demonstration text with one block per example.
    """
    import json

    blocks = []
    for example in examples:
        rendered = json.dumps(example["output"], indent=2)
        blocks.append(f"Example input:\n{example['input']}\nExample output:\n{rendered}")
    return "\n\n".join(blocks)


DOMAIN_HINT_TECHNICAL = (
    "Prefer SOFTWARE, PROTOCOL, and CONCEPT entity types. Versioned "
    "dependencies and configuration relationships are usually explicit."
)

DOMAIN_HINT_NEWS = (
    "Prefer PERSON, ORG, and GPE entity types. Acquisitions, employment, "
    "and location relationships dominate; keep predicates in past tense."
)

DOMAIN_HINT_BIOMEDICAL = (
    "Prefer GENE, DISEASE, DRUG, and PATHWAY entity types. Only extract "
    "experimentally stated interactions, not background-knowledge ones."
)

DOMAIN_HINTS = {
    "technical": DOMAIN_HINT_TECHNICAL,
    "news": DOMAIN_HINT_NEWS,
    "biomedical": DOMAIN_HINT_BIOMEDICAL,
}


def render_domain_hint(domain: str) -> str:
    """Looks up the guidance hint for a domain key.

    Args:
        domain: Domain key such as technical, news, or biomedical.

    Returns:
        hint: Guidance sentence, or an empty string for unknown domains.
    """
    return DOMAIN_HINTS.get(domain, "")


def predicate_guidance(domain: str) -> list[str]:
    """Suggests common predicate phrasings for a domain.

    Args:
        domain: Domain key to suggest predicates for.

    Returns:
        predicates: Short predicate phrases typical for the domain.
    """
    suggestions = {
        "technical": ["depends on", "ships with", "configures", "replaces"],
        "news": ["acquired", "founded", "joined", "is based in"],
        "biomedical": ["interacts with", "inhibits", "expresses", "mutates in"],
    }
    return suggestions.get(domain, ["relates to"])


DEFAULT_FEW_SHOT_COUNT = 2


def estimate_prompt_tokens(prompt: str) -> int:
    """Estimates the token count of a rendered prompt.

    Args:
        prompt: Rendered prompt text to measure.

    Returns:
        tokens: Approximate token count using the 4-chars heuristic.
    """
    return max(1, -(-len(prompt) // 4))


def validate_domain(domain: str) -> str:
    """Rejects domain keys that have no registered hint.

    Args:
        domain: Candidate domain key.

    Returns:
        domain: The same key, if registered.
    """
    if domain != "general" and domain not in DOMAIN_HINTS:
        valid = ", ".join(sorted(["general", *DOMAIN_HINTS]))
        msg = f"unknown domain {domain!r}; expected one of: {valid}"
        raise ValueError(msg)
    return domain


def list_available_domains() -> list[str]:
    """Reports the domain keys with registered extraction hints.

    Returns:
        domains: Sorted list of usable domain keys.
    """
    return sorted(DOMAIN_HINTS)


def select_examples(config: "PromptConfig") -> list[dict[str, object]]:
    """Chooses worked examples matching the configured domain and count.

    Args:
        config: Prompt configuration carrying domain and few-shot count.

    Returns:
        examples: Matching examples, capped at the configured count.
    """
    matching = [ex for ex in FEW_SHOT_EXAMPLES if ex["domain"] == config.domain]
    pool = matching or FEW_SHOT_EXAMPLES
    return pool[: max(0, config.few_shot_count)]


def summarize_template() -> str:
    """Describes the active template set in one log-friendly line.

    Returns:
        summary: Count of rules, examples, and domains in the template set.
    """
    return (
        f"rules={len(EXTRACTION_RULES)} examples={len(FEW_SHOT_EXAMPLES)} "
        f"domains={len(DOMAIN_HINTS)}"
    )


TEMPLATE_VERSION = "1.3.0"

CITATION_REQUIREMENT = (
    "For every triple you emit, you must also emit a source_span object "
    "with start and end character offsets and the verbatim text of the "
    "passage that states the relationship. If you cannot point to the exact "
    "passage, do not emit the triple."
)

CITATION_FEW_SHOT_EXAMPLE: dict[str, object] = {
    "domain": "technical",
    "input": "Kafka Connect ships with RabbitMQ.",
    "output": [
        {
            "subject": {"name": "Kafka Connect", "entity_type": "SOFTWARE"},
            "predicate": "ships with",
            "object": {"name": "RabbitMQ", "entity_type": "SOFTWARE"},
            "confidence": 0.95,
            "source_span": {"start": 0, "end": 35, "text": "Kafka Connect ships with RabbitMQ."},
        }
    ],
}


def citation_block(enabled: bool) -> str:
    """Renders the citation requirement block when citations are enabled.

    Args:
        enabled: Whether the active prompt configuration requires citations.

    Returns:
        block: Citation requirement text, or an empty string when disabled.
    """
    if not enabled:
        return ""
    import json

    example = json.dumps(CITATION_FEW_SHOT_EXAMPLE["output"], indent=2)
    return f"{CITATION_REQUIREMENT}\nExample output:\n{example}"


def merge_domain_hints(domains: list[str]) -> str:
    """Combines the hints of several domains into one guidance block.

    Args:
        domains: Domain keys whose hints are merged, in order.

    Returns:
        hint: Joined guidance text for the compound domain.
    """
    hints = [DOMAIN_HINTS[d] for d in domains if d in DOMAIN_HINTS]
    return " ".join(hints)


def validate_few_shot_examples() -> None:
    """Sanity-checks that every registered example is well-formed.

    Raises:
        ValueError: If an example lacks required keys or a known domain.
    """
    for example in FEW_SHOT_EXAMPLES:
        for key in ("domain", "input", "output"):
            if key not in example:
                msg = f"few-shot example missing key {key!r}"
                raise ValueError(msg)
        validate_domain(str(example["domain"]))


def render_prompt_preview(text: str, config: "PromptConfig | None" = None) -> str:
    """Renders an abbreviated prompt preview for debugging.

    Args:
        text: Text window the prompt would target.
        config: Prompt configuration; defaults are used when omitted.

    Returns:
        preview: Prompt truncated to its first 400 characters.
    """
    prompt = build_extraction_prompt(text, config)
    if len(prompt) <= 400:
        return prompt
    return prompt[:400] + "...[truncated]"


def template_hash() -> str:
    """Computes a content fingerprint of the current template set.

    Returns:
        fingerprint: Stable short hash of prompts and rules.
    """
    import hashlib

    material = f"{SYSTEM_PROMPT}|{EXTRACTION_RULES}|{TEMPLATE_VERSION}"
    return hashlib.sha256(material.encode()).hexdigest()[:12]


def reload_templates() -> str:
    """Re-validates the template set after an in-place edit.

    Returns:
        summary: Template summary line for logs.
    """
    validate_few_shot_examples()
    return summarize_template()
