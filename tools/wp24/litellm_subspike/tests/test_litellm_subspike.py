"""Unit tests for the WP24 LiteLLM sub-spike kit's pure functions (tools/wp24/litellm_subspike/).

Run with: python -m unittest discover -s tools/wp24/litellm_subspike/tests

Covers _common.py (fingerprinting, redaction, the injected-clock polling loop), a smoke import of
both entrypoint scripts, and text-level checks that the two YAML templates contain the settings the
task brief and README.md describe (no PyYAML in this repo's stdlib-only toolchain -- README.md "การ
validate YAML" explains that `docker compose config` is the real validation at run time).
"""

from __future__ import annotations

import importlib
import re
import sys
import unittest
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_DIR))

import _common  # noqa: E402


class FingerprintTests(unittest.TestCase):
    def test_fingerprint_format(self) -> None:
        fp = _common.fingerprint("sk-super-secret-value")
        self.assertTrue(fp.startswith("sha256:"))
        self.assertEqual(len(fp), len("sha256:") + 12)
        self.assertRegex(fp, r"^sha256:[0-9a-f]{12}$")

    def test_fingerprint_deterministic(self) -> None:
        self.assertEqual(_common.fingerprint("same-value"), _common.fingerprint("same-value"))

    def test_fingerprint_differs_for_different_secrets(self) -> None:
        self.assertNotEqual(_common.fingerprint("sk-aaaa"), _common.fingerprint("sk-bbbb"))

    def test_fingerprint_never_contains_the_secret(self) -> None:
        secret = "sk-do-not-leak-this-value"
        self.assertNotIn(secret, _common.fingerprint(secret))


class RedactValueTests(unittest.TestCase):
    def test_matches_plaintext_becomes_fingerprint(self) -> None:
        secret = "sk-plaintext-key"
        redacted = _common.redact_value(secret, plaintext=secret)
        self.assertEqual(redacted, _common.fingerprint(secret))

    def test_key_shaped_without_known_plaintext_is_redacted(self) -> None:
        redacted = _common.redact_value("sk-some-other-key-1234")
        self.assertEqual(redacted, "<redacted:key-shaped-value>")

    def test_non_key_shaped_string_passes_through(self) -> None:
        self.assertEqual(_common.redact_value("hello world"), "hello world")

    def test_non_string_passes_through(self) -> None:
        self.assertEqual(_common.redact_value(42), 42)
        self.assertEqual(_common.redact_value(None), None)


class RedactMappingTests(unittest.TestCase):
    def test_secret_field_names_are_fingerprinted_regardless_of_plaintext(self) -> None:
        body = {"token": "sk-abcdefgh", "key": "sk-ijklmnop", "note": "harmless"}
        redacted = _common.redact_mapping(body)
        self.assertEqual(redacted["token"], _common.fingerprint("sk-abcdefgh"))
        self.assertEqual(redacted["key"], _common.fingerprint("sk-ijklmnop"))
        self.assertEqual(redacted["note"], "harmless")

    def test_recurses_into_nested_structures(self) -> None:
        body = {"info": {"token": "sk-nested-value"}, "items": [{"authorization": "sk-in-list"}]}
        redacted = _common.redact_mapping(body)
        self.assertEqual(redacted["info"]["token"], _common.fingerprint("sk-nested-value"))
        self.assertEqual(redacted["items"][0]["authorization"], _common.fingerprint("sk-in-list"))

    def test_never_leaves_the_plaintext_anywhere_in_the_result(self) -> None:
        secret = "sk-must-not-survive"
        body = {"token": secret, "echo": secret, "nested": {"key_name": secret}}
        redacted = _common.redact_mapping(body, plaintext=secret)
        self.assertNotIn(secret, str(redacted))


class FindPlaintextLocationsTests(unittest.TestCase):
    def test_finds_top_level_field(self) -> None:
        hits = _common.find_plaintext_locations({"token": "sk-x"}, "sk-x")
        self.assertEqual(hits, ["$.token"])

    def test_finds_nested_and_list_locations(self) -> None:
        obj = {"info": {"token": "sk-x"}, "items": [{"a": "no"}, {"b": "sk-x"}]}
        hits = _common.find_plaintext_locations(obj, "sk-x")
        self.assertIn("$.info.token", hits)
        self.assertIn("$.items[1].b", hits)

    def test_no_match_returns_empty(self) -> None:
        self.assertEqual(_common.find_plaintext_locations({"token": "sk-other"}, "sk-x"), [])

    def test_result_never_contains_the_plaintext_value_itself(self) -> None:
        hits = _common.find_plaintext_locations({"token": "sk-secret-value"}, "sk-secret-value")
        self.assertNotIn("sk-secret-value", hits)


class RedactArgvTests(unittest.TestCase):
    def test_redacts_key_shaped_arguments(self) -> None:
        argv = ["--base-url", "http://127.0.0.1:4000", "--key", "sk-oops-a-real-key"]
        redacted = _common.redact_argv(argv)
        self.assertEqual(redacted[:2], argv[:2])
        self.assertEqual(redacted[3], "<redacted:key-shaped-value>")

    def test_leaves_ordinary_arguments_untouched(self) -> None:
        argv = ["--master-key-env", "LITELLM_MASTER_KEY", "--count", "5"]
        self.assertEqual(_common.redact_argv(argv), argv)


class PollUntilTests(unittest.TestCase):
    def test_succeeds_on_first_check(self) -> None:
        result = _common.poll_until(
            lambda: True, interval_s=0.2, timeout_s=30.0, clock=lambda: 0.0, sleep=lambda s: None
        )
        self.assertEqual(result, {"rejected": True, "elapsed_seconds": 0.0, "attempts": 1})

    def test_succeeds_after_n_polls_with_fake_clock(self) -> None:
        # Fake clock advances by interval_s each time it is read, simulating three failed checks
        # (0.0, 0.2, 0.4) followed by a success at the fourth call.
        clock_values = iter([0.0, 0.2, 0.4, 0.6])
        calls = {"n": 0}

        def fake_check() -> bool:
            calls["n"] += 1
            return calls["n"] >= 4

        result = _common.poll_until(
            fake_check,
            interval_s=0.2,
            timeout_s=30.0,
            clock=lambda: next(clock_values),
            sleep=lambda s: None,
        )
        self.assertTrue(result["rejected"])
        self.assertEqual(result["attempts"], 4)

    def test_times_out_without_success(self) -> None:
        clock_values = iter([0.0, 1.0, 2.0, 3.0])
        result = _common.poll_until(
            lambda: False,
            interval_s=1.0,
            timeout_s=2.5,
            clock=lambda: next(clock_values),
            sleep=lambda s: None,
        )
        self.assertFalse(result["rejected"])
        self.assertGreaterEqual(result["elapsed_seconds"], 2.5)

    def test_never_sleeps_past_a_successful_check(self) -> None:
        sleep_calls: list[float] = []
        result = _common.poll_until(
            lambda: True,
            interval_s=0.2,
            timeout_s=30.0,
            clock=lambda: 0.0,
            sleep=sleep_calls.append,
        )
        self.assertTrue(result["rejected"])
        self.assertEqual(sleep_calls, [])


class MeasurementTests(unittest.TestCase):
    def test_shape(self) -> None:
        expected = {"name": "latency_ms", "value": 12.5}
        self.assertEqual(_common.measurement("latency_ms", 12.5), expected)


class UtcNowIsoTests(unittest.TestCase):
    def test_matches_expected_format(self) -> None:
        self.assertRegex(_common.utc_now_iso(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ScriptImportSmokeTests(unittest.TestCase):
    """Both entrypoint scripts must import cleanly (argparse/network only runs inside main())."""

    def test_ev04_keys_imports(self) -> None:
        module = importlib.import_module("ev04_keys")
        self.assertTrue(hasattr(module, "main"))

    def test_ev03_retry_probe_imports(self) -> None:
        module = importlib.import_module("ev03_retry_probe")
        self.assertTrue(hasattr(module, "main"))


class TemplateYamlContentTests(unittest.TestCase):
    """Text-level checks only -- no PyYAML in this repo's stdlib-only toolchain (README.md "การ
    validate YAML"). `docker compose config` is the real parse/validate step at run time."""

    def test_compose_template_has_expected_keys(self) -> None:
        text = (PACKAGE_DIR / "docker-compose.litellm.template.yml").read_text(encoding="utf-8")
        for expected in (
            "TEMPLATE / NOT_QUALIFIED",
            "services:",
            "litellm:",
            "db:",
            "LITELLM_MASTER_KEY",
            "DATABASE_URL",
            "postgres:16",
            "127.0.0.1:4000:4000",
            "127.0.0.1:5432:5432",
            "# digest: <fill from docker inspect at run time>",
            "litellm_config.template.yaml",
        ):
            self.assertIn(expected, text, msg=f"missing {expected!r} in compose template")

    def test_config_template_has_expected_keys(self) -> None:
        text = (PACKAGE_DIR / "litellm_config.template.yaml").read_text(encoding="utf-8")
        for expected in (
            "TEMPLATE / NOT_QUALIFIED",
            "model_list:",
            "wp24-litellm-subspike-host-a",
            "wp24-litellm-subspike-host-b",
            "hosted_vllm/",
            "router_settings:",
            "num_retries: 0",
            "fallbacks: []",
            "content_policy_fallbacks: []",
            "context_window_fallbacks: []",
            "enable_weighted_failover: false",
            "disable_cooldowns: true",
            "routing_strategy: simple-shuffle",
        ):
            self.assertIn(expected, text, msg=f"missing {expected!r} in litellm config template")

    def test_no_stray_todo_placeholders_outside_declared_set_at_run_time(self) -> None:
        # Every placeholder value must be the documented sentinel, not an ad-hoc TODO/FIXME.
        for name in ("docker-compose.litellm.template.yml", "litellm_config.template.yaml"):
            text = (PACKAGE_DIR / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, re.compile(r"\bTODO\b|\bFIXME\b"))


if __name__ == "__main__":
    unittest.main()
