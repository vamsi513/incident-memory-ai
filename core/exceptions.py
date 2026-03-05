class IncidentMemoryError(Exception):
    """Base application exception."""


class RetrievalError(IncidentMemoryError):
    """Raised when retrieval pipeline fails."""


class ProviderError(IncidentMemoryError):
    """Raised when a model provider fails."""


class EvaluationError(IncidentMemoryError):
    """Raised when evaluation pipeline fails."""
