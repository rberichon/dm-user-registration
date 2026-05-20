from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
    is_active: bool


class DuplicateEmailError(Exception):
    """Raised by a repository when a user with the given email already exists."""
