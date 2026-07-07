from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping


@dataclass
class Memory(Mapping[str, Any]):
    """
    Typed, dict-compatible factual memory for GOAP phases.

    Existing thinker/action code can keep using `memory["key"]` and
    `memory.get("key")`, while new code gets one documented type boundary.
    """
    facts: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.facts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.facts)

    def __len__(self) -> int:
        return len(self.facts)

    def get(self, key: str, default: Any = None) -> Any:
        return self.facts.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        return dict(self.facts)

    def with_fact(self, key: str, value: Any) -> "Memory":
        updated = self.as_dict()
        updated[key] = value
        return Memory(updated)


@dataclass(frozen=True)
class DecisionContext:
    """Pairs factual memory with server-derived legal actions."""
    memory: Memory
    legal_actions: list[dict[str, Any]]
