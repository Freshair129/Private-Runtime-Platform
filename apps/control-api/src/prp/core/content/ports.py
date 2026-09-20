from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from prp.core.content.model import Artifact, ArtifactGrant


class ArtifactStore(Protocol):
    """Object storage port. Bytes only; authorization happens in the content context."""

    def put(self, artifact_id: str, chunks: Iterator[bytes]) -> str:
        """Store and return the sha256 checksum of the written bytes."""
        ...

    def open(self, artifact_id: str) -> Iterator[bytes]: ...

    def purge(self, artifact_id: str) -> None: ...


class ArtifactRepository(Protocol):
    def get(self, artifact_id: str) -> Artifact | None: ...

    def get_grant(self, grant_id: str) -> ArtifactGrant | None: ...
