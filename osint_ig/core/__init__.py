"""Core intelligence collection and Instagram provider package."""

from osint_ig.core.exceptions import (
    CancelledError,
    InvestigationError,
    PrivateProfileError,
    ProviderError,
    RequestLimitReachedError,
    TargetNotFoundError,
)

__all__ = [
    "CancelledError",
    "InvestigationError",
    "PrivateProfileError",
    "ProviderError",
    "RequestLimitReachedError",
    "TargetNotFoundError",
]
