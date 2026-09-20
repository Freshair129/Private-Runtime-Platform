"""PRP control plane (SDD-PRP-REPO §6).

Thin Python API, policy and ports. Model runtimes live in separate processes and environments
(ADR-PRP-011); nothing in this package may import torch, CUDA or engine code (PRP-NFR-021).
"""

__version__ = "0.4.0a0"
