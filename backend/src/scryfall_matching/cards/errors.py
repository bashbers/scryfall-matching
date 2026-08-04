class CardsUnavailableError(RuntimeError):
    """Raised when the active card repository cannot satisfy a batch request."""
