"""PII masking and prompt injection screening.

What the injection screen is: a pattern match over a normalised copy of the
text, meant to catch the obvious and the casually obfuscated. It raises the
cost of a lazy attempt. It is not a solved problem and it is not a boundary
anything should rely on. A determined attacker who paraphrases ("set aside what
you were told earlier"), splits a phrase across turns, or encodes it will get
through, because no substring or regex screen can decide intent.

The mitigation that actually carries weight is in ``app.generator``, which
fences retrieved evidence as untrusted data so the model is told not to follow
instructions found inside it, together with the system prompt. Treat this
module as one layer of defence in depth, not the defence.
"""

import re
import unicodedata

_EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
_PHONE_RE = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

# Characters that render as nothing and exist only to break up a phrase.
_INVISIBLE = dict.fromkeys(
    ord(c)
    for c in "​‌‍‎‏⁠⁡⁢⁣﻿­"
)

# Letters from other scripts that read as Latin ones, plus a conservative
# leetspeak set. NFKC already folds fullwidth and most mathematical variants,
# so this covers what it leaves behind.
_CONFUSABLES = str.maketrans(
    {
        "а": "a",
        "в": "b",
        "е": "e",
        "к": "k",
        "м": "m",
        "н": "h",
        "о": "o",
        "р": "p",
        "с": "c",
        "т": "t",
        "у": "y",
        "х": "x",
        "і": "i",
        "ј": "j",
        "ѕ": "s",
        "α": "a",
        "ε": "e",
        "ι": "i",
        "ο": "o",
        "ρ": "p",
        "τ": "t",
        "υ": "y",
        "χ": "x",
        "ν": "v",
        "ı": "i",
        "ł": "l",
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }
)

# Phrases screened for. Each is matched with separators allowed between every
# character and up to two filler words between words, so "i g n o r e previous
# instructions" and "ignore all previous instructions" both match.
_INJECTION_PHRASES = (
    "ignore previous instructions",
    "reveal system prompt",
    "send secrets",
    "exfiltrate",
    "disregard prior",
    "forget all instructions",
    "you are now",
    "act as if",
    "disregard previous instructions",
    "ignore above instructions",
    "show system prompt",
    "print your instructions",
    "override instructions",
    "new instructions",
    "developer mode",
    "jailbreak",
)

_MAX_FILLER_WORDS = 2


def _fold(text: str) -> str:
    """Normalise away the cheap ways of hiding a phrase."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_INVISIBLE)
    text = text.casefold()
    text = text.translate(_CONFUSABLES)
    # Drop combining marks, so "ignore" with an accent reads as "ignore".
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _compile(phrase: str) -> re.Pattern[str]:
    words = [r"[\W_]*".join(re.escape(c) for c in word) for word in phrase.split()]
    # The separator between words is optional, because folding away soft hyphens
    # or zero width characters can leave the words run together with nothing
    # between them at all. Filler words each still need a real separator.
    gap = r"[\W_]*(?:\w+[\W_]+){0,%d}" % _MAX_FILLER_WORDS
    # \b at both ends keeps a short phrase from matching across unrelated
    # words, so "artifact as if" does not trip "act as if".
    return re.compile(r"\b" + gap.join(words) + r"\b")


_INJECTION_PATTERNS = tuple(_compile(phrase) for phrase in _INJECTION_PHRASES)


def mask_pii(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = _SSN_RE.sub("[REDACTED_SSN]", text)
    text = _CARD_RE.sub("[REDACTED_CARD]", text)
    return text


def detect_prompt_injection(text: str) -> bool:
    """Report whether the text matches a screened phrase.

    False does not mean the text is safe, only that it did not match. See the
    module docstring for what this does and does not buy.
    """
    folded = _fold(text)
    return any(pattern.search(folded) for pattern in _INJECTION_PATTERNS)
