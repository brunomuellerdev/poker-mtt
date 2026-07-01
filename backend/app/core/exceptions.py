class DomainError(Exception):
    """Base for application/business errors."""


class EmailAlreadyExists(DomainError):
    pass


class InvalidCredentials(DomainError):
    pass
