"""Control plane never imports or locks ML runtimes (PRP-NFR-021, PRP-NFR-022; Coding-Standards §4).

Collected under PRP-AT-089 for its import-smoke portion only; the acceptance case also requires a
live process-count measurement while API workers scale. Status stays NOT_RUN until that
receipt exists.
"""

import importlib
import multiprocessing
import pkgutil
import sys
import tomllib
from pathlib import Path

import pytest

import prp
from prp.api.app import Dependencies, create_app
from prp.settings import Settings

LOCK_FILE = Path(__file__).resolve().parents[2] / "uv.lock"

pytestmark = [
    pytest.mark.req("PRP-NFR-021"),
    pytest.mark.req("PRP-NFR-022"),
    pytest.mark.at("PRP-AT-089"),
]

ML_TOP_LEVEL_MODULES = {
    "torch",
    "torchaudio",
    "tensorflow",
    "jax",
    "transformers",
    "vllm",
    "whisper",
    "faster_whisper",
    "ctranslate2",
    "TTS",
    "onnxruntime",
    "xinference",
    "ray",
}
ML_LOCK_PACKAGES = {
    "torch",
    "torchaudio",
    "tensorflow",
    "jax",
    "transformers",
    "vllm",
    "openai-whisper",
    "faster-whisper",
    "ctranslate2",
    "tts",
    "onnxruntime",
    "xinference",
    "ray",
    "triton",
}


def import_every_prp_module() -> list[str]:
    names = [module.name for module in pkgutil.walk_packages(prp.__path__, "prp.")]
    for name in names:
        importlib.import_module(name)
    return names


def test_importing_the_whole_control_plane_loads_no_ml_runtime() -> None:
    names = import_every_prp_module()
    assert len(names) >= 30, names
    loaded = {module.split(".")[0] for module in sys.modules}
    assert not loaded & ML_TOP_LEVEL_MODULES


def test_lock_file_contains_no_ml_or_cuda_packages() -> None:
    lock = tomllib.loads(LOCK_FILE.read_text(encoding="utf-8"))
    names = {package["name"].lower() for package in lock["package"]}
    assert not names & ML_LOCK_PACKAGES, sorted(names & ML_LOCK_PACKAGES)
    assert not {name for name in names if name.startswith("nvidia-")}


def test_scaling_api_instances_spawns_no_model_processes() -> None:
    before = {module.split(".")[0] for module in sys.modules}
    apps = [create_app(Settings(), Dependencies()) for _ in range(4)]
    assert len(apps) == 4
    assert multiprocessing.active_children() == []
    after = {module.split(".")[0] for module in sys.modules}
    assert not (after - before) & ML_TOP_LEVEL_MODULES
