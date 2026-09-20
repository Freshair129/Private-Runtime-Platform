"""Opaque identifiers. Business references stay opaque metadata (ARCH-PRP §8)."""

import uuid


def new_id() -> str:
    return str(uuid.uuid4())
