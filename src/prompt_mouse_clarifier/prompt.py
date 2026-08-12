"""Conservative prompt clarification rules and output guards."""

from __future__ import annotations

import re

PROMPT_SYSTEM = """You rewrite rough, plain-language user prompts into clear, precise prompts for a coding or technical agent.

Your job is terminology compression and clarity, not invention or product management.

Rules:
1. Keep the user's intent exactly. Do not add features, constraints, stack choices, files, paths, numbers, APIs, tests, or preferences they did not state.
2. When a well-known technical term accurately matches what the user described, use that term instead of the long description. Examples:
   - \"remember old card positions, measure new ones, animate between them\" -> \"FLIP animation\"
   - \"thumbnail grows into the large image on the next screen so it feels like the same image\" -> \"shared-element transition\"
   - \"one small part working end-to-end from UI through backend and database\" -> \"vertical slice\"
   - \"show the new state right away, then fix it if the server fails\" -> \"optimistic update\"
   - \"wait until the user stops typing before searching\" -> \"debounce the search input\"
   Apply the same principle in any domain: use the standard name for the pattern, algorithm, UX behavior, architecture choice, protocol, or process the user is actually describing.
3. Prefer short, exact terms over long explanations. Do not force jargon when it is not an exact fit.
4. Preserve every concrete detail: product names, file names, paths, URLs, commands, versions, numbers, constraints, UI copy, error text, language, tone, and acceptance criteria.
5. Keep the user's language. Spanish stays Spanish; English stays English.
6. Keep implementation requests as implementation requests. Do not turn them into a plan-only answer or answer the task yourself.
7. If the original is already precise, make only light cleanup. Do not expand it merely to make it look more technical.
8. Structure multi-part asks with short bullets or headings only when that makes the same request clearer. Do not invent missing sections or requirements.
9. Return only the ready-to-send rewritten prompt. No preamble, quotes, Markdown fences, or meta-commentary."""

MAX_CHARS = 16_000
MAX_LINES = 240

_NUMBER_WORDS = {
    0: ("cero", "zero"),
    1: ("uno", "un", "una", "one"),
    2: ("dos", "two"),
    3: ("tres", "three"),
    4: ("cuatro", "four"),
    5: ("cinco", "five"),
    6: ("seis", "six"),
    7: ("siete", "seven"),
    8: ("ocho", "eight"),
    9: ("nueve", "nine"),
    10: ("diez", "ten"),
    11: ("once", "eleven"),
    12: ("doce", "twelve"),
    13: ("trece", "thirteen"),
    14: ("catorce", "fourteen"),
    15: ("quince", "fifteen"),
    16: ("dieciséis", "sixteen"),
    17: ("diecisiete", "seventeen"),
    18: ("dieciocho", "eighteen"),
    19: ("diecinueve", "nineteen"),
    20: ("veinte", "twenty"),
}


def normalize_result(result: str) -> str:
    cleaned = (result or "").strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = re.sub(r"^```[^\n]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned).strip()
    return re.sub(
        r"^(?:Here(?:'s| is) the (?:rewritten|enhanced|clarified) prompt:|Prompt:)[ \t]*\n?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()


def _literal_tokens(text: str) -> list[str]:
    raw = re.findall(r"(?:/[^\s]+|https?://[^\s]+|\b\d+(?:[._-]\d+)*\b|`[^`]+`)", text)
    return [token.strip("`").rstrip(".,;:!?)]}") for token in raw]


def _literal_is_preserved(token: str, result: str) -> bool:
    if token in result:
        return True
    if token.isdigit():
        return any(
            re.search(rf"\b{re.escape(word)}\b", result, flags=re.IGNORECASE)
            for word in _NUMBER_WORDS.get(int(token), ())
        )
    return False


def is_usable(original: str, result: str) -> bool:
    if not result.strip() or len(result) > max(MAX_CHARS, len(original) * 4):
        return False
    plain_result = result.replace("`", "")
    return all(
        token and _literal_is_preserved(token, plain_result)
        for token in _literal_tokens(original)
    )


def validate_input(text: str) -> None:
    if not text.strip():
        raise ValueError("No prompt text was selected")
    if len(text) > MAX_CHARS or len(text.splitlines()) > MAX_LINES:
        raise ValueError(f"Prompt exceeds {MAX_CHARS} characters or {MAX_LINES} lines")
