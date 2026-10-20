from typing import Annotated

from pydantic import AfterValidator


def to_lower(s: str) -> str:
    return s.lower()


type Lower[T: str] = Annotated[T, AfterValidator(to_lower)]