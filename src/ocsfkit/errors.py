class OCSFKitError(Exception):
    """Base exception for user-facing ocsfkit errors."""


class InputLoadError(OCSFKitError):
    """Raised when an input document cannot be loaded."""


class MappingError(OCSFKitError):
    """Raised when a mapping file or mapping operation is invalid."""


class QueryError(OCSFKitError):
    """Raised when a query expression cannot be evaluated."""

