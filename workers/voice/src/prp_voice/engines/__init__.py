"""Engine ports. The only package allowed to import ML runtimes, and only from M4 onwards.

Implementations stage model assets by revision + checksum + approved license/voice record before
reporting ready (Coding-Standards §7) and never download weights in response to a request.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class EngineDescription:
    model: str
    profile_revision: str
    languages: tuple[str, ...]
    formats: tuple[str, ...]


class AsrEngine(Protocol):
    def describe(self) -> EngineDescription: ...

    def transcribe(self, audio: Iterator[bytes], *, language: str) -> str: ...


class TtsEngine(Protocol):
    def describe(self) -> EngineDescription: ...

    def synthesize(self, text: str, *, voice: str, response_format: str) -> bytes: ...
