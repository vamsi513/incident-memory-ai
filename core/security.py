import re

_EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
_PHONE_RE = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "send secrets",
    "exfiltrate",
    "disregard prior",
    "forget all instructions",
    "you are now",
    "act as if",
]


def mask_pii(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = _SSN_RE.sub("[REDACTED_SSN]", text)
    text = _CARD_RE.sub("[REDACTED_CARD]", text)
    return text


def detect_prompt_injection(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in _INJECTION_PATTERNS)
