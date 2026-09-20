"""Composition root and process mains: prp-api, prp-dispatcher, prp-observer.

The only package that wires adapters into core ports. Three processes from one codebase
(ARCH-PRP §2, §6): scaling API workers never adds model processes (PRP-NFR-021).
"""
