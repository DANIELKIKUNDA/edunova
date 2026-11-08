class DomainError(Exception):
    """Base error for business-rule violations."""


class ValidationError(DomainError):
    pass
