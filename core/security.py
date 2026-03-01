import re

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def mask_pii(text: str) -> str:
    return EMAIL_RE.sub("[REDACTED_EMAIL]", text)


def detect_prompt_injection(text: str) -> bool:
    patterns = [
        "ignore previous instructions",
        "reveal system prompt",
        "send secrets",
        "exfiltrate",
    ]
    lower = text.lower()
    return any(pattern in lower for pattern in patterns)
