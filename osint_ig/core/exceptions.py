"""Domain exceptions for OSINT IG investigations."""


class InvestigationError(Exception):
    """Base exception for OSINT IG intelligence collection errors."""


class TargetNotFoundError(InvestigationError):
    """The target Instagram username does not exist."""


class PrivateProfileError(InvestigationError):
    """The requested capability requires access to a public or followed profile."""


class ProviderError(InvestigationError):
    """The Instagram data provider returned an error or failed to respond."""


class CancelledError(Exception):
    """Raised when an operator cancels an active investigation run."""


class RequestLimitReachedError(InvestigationError):
    """Raised when the per-run cap on uncached backend requests is reached."""
