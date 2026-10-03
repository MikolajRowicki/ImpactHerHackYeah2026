from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Generation:
    text: str
    # Where the text came from. The contract lists the values (summary narrative source).
    source: str


class Provider(Protocol):
    def generate(self, prompt: str) -> Generation: ...
