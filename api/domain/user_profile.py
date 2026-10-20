from dataclasses import dataclass


@dataclass(frozen=True)
class UserSummary:
    id: int
    username: str


@dataclass(frozen=True)
class UserProfile:
    id: int
    username: str
    email: str
