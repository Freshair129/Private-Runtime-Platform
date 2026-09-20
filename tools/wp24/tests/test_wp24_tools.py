"""Unit tests for the pure functions in tools/wp24 (CSV parsing, redaction, diffing).

Run with: python -m unittest discover -s tools/wp24/tests
Standard library only (unittest); no network, no subprocess, no GPU required.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ev02_gpu_binding  # noqa: E402
import wp24_common as common  # noqa: E402


class TestRedaction(unittest.TestCase):
    def test_redact_windows_home(self) -> None:
        self.assertEqual(
            common.redact_text(r"C:\Users\pc\AppData\file.txt"), r"<home>\AppData\file.txt"
        )

    def test_redact_posix_home(self) -> None:
        self.assertEqual(common.redact_text("/home/alice/data/file.txt"), "<home>/data/file.txt")

    def test_redact_macos_home(self) -> None:
        self.assertEqual(common.redact_text("/Users/bob/project"), "<home>/project")

    def test_redact_leaves_unrelated_text_untouched(self) -> None:
        self.assertEqual(common.redact_text("no secrets here"), "no secrets here")

    def test_redact_json_walks_nested_structures(self) -> None:
        payload = {"a": [r"C:\Users\pc\x", {"b": "fine", "c": 3}]}
        redacted = common.redact_json(payload)
        self.assertEqual(redacted["a"][0], r"<home>\x")
        self.assertEqual(redacted["a"][1]["b"], "fine")
        self.assertEqual(redacted["a"][1]["c"], 3)

    def test_redacted_header_lines_masks_authorization_only(self) -> None:
        lines = common.redacted_header_lines({"Authorization": "Bearer abc123", "X-Test": "1"})
        self.assertIn("Authorization: <redacted>", lines)
        self.assertIn("X-Test: 1", lines)
        self.assertNotIn("abc123", " ".join(lines))


class TestNvidiaSmiCsvParsing(unittest.TestCase):
    def test_parse_gpu_query_row(self) -> None:
        text = (
            "NVIDIA GeForce RTX 4090, 24564 MiB, 550.54.15, "
            "GPU-11111111-2222-3333-4444-555555555555\n"
        )
        rows = common.parse_nvidia_smi_csv(text, ("name", "memory.total", "driver_version", "uuid"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "NVIDIA GeForce RTX 4090")
        self.assertEqual(rows[0]["uuid"], "GPU-11111111-2222-3333-4444-555555555555")

    def test_parse_multiple_rows_and_blank_lines(self) -> None:
        text = "GPU-aaa, 0\n\nGPU-bbb, 1\n"
        rows = common.parse_nvidia_smi_csv(text, ("uuid", "index"))
        self.assertEqual(
            rows, [{"uuid": "GPU-aaa", "index": "0"}, {"uuid": "GPU-bbb", "index": "1"}]
        )

    def test_skips_row_with_wrong_field_count(self) -> None:
        text = "only-one-field\nGPU-aaa, 0\n"
        rows = common.parse_nvidia_smi_csv(text, ("uuid", "index"))
        self.assertEqual(rows, [{"uuid": "GPU-aaa", "index": "0"}])

    def test_looks_like_gpu_uuid(self) -> None:
        self.assertTrue(common.looks_like_gpu_uuid("GPU-11111111-2222-3333-4444-555555555555"))
        self.assertFalse(common.looks_like_gpu_uuid("model-7b-instruct"))


class TestIdentifierExtraction(unittest.TestCase):
    def test_extract_candidate_identifiers_from_list_body(self) -> None:
        parsed = {"data": [{"id": "model-a", "object": "model"}, {"id": "model-b"}]}
        found = common.extract_candidate_identifiers(parsed)
        self.assertEqual(found["data[0].id"], "model-a")
        self.assertEqual(found["data[1].id"], "model-b")
        self.assertEqual(found["data[0].object"], "model")

    def test_extract_candidate_identifiers_ignores_unlisted_keys(self) -> None:
        found = common.extract_candidate_identifiers({"unrelated_field": "value"})
        self.assertEqual(found, {})


class TestDiffIdentifiers(unittest.TestCase):
    def test_diff_reports_added_removed_changed_unchanged(self) -> None:
        before = {"a": "1", "b": "2", "c": "3"}
        after = {"a": "1", "b": "9", "d": "4"}
        diff = common.diff_identifiers(before, after)
        self.assertEqual(diff["added"], {"d": "4"})
        self.assertEqual(diff["removed"], {"c": "3"})
        self.assertEqual(diff["changed"], {"b": {"before": "2", "after": "9"}})
        self.assertEqual(diff["unchanged"], {"a": "1"})

    def test_diff_of_identical_maps_is_all_unchanged(self) -> None:
        same = {"a": "1", "b": "2"}
        diff = common.diff_identifiers(same, dict(same))
        self.assertEqual(diff["added"], {})
        self.assertEqual(diff["removed"], {})
        self.assertEqual(diff["changed"], {})
        self.assertEqual(diff["unchanged"], same)


class TestGpuBindingJoin(unittest.TestCase):
    def test_join_matches_pattern_and_counts_unrelated_without_naming_it(self) -> None:
        gpu_list = [{"uuid": "GPU-aaa", "index": "0"}, {"uuid": "GPU-bbb", "index": "1"}]
        compute_apps = [
            {
                "gpu_uuid": "GPU-aaa",
                "pid": "111",
                "process_name": "vllm-worker",
                "used_memory": "1024 MiB",
            },
            {"gpu_uuid": "GPU-bbb", "pid": "222", "process_name": "Xorg", "used_memory": "10 MiB"},
        ]
        matched, unrelated = ev02_gpu_binding.join_and_classify(
            gpu_list, compute_apps, "vllm|xinference|python"
        )
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["pid"], "111")
        self.assertEqual(matched[0]["gpu_index"], "0")
        self.assertEqual(unrelated, 1)
        self.assertNotIn("Xorg", str(matched))

    def test_join_leaves_gpu_index_none_when_uuid_unknown(self) -> None:
        gpu_list = [{"uuid": "GPU-aaa", "index": "0"}]
        compute_apps = [
            {"gpu_uuid": "GPU-zzz", "pid": "333", "process_name": "python", "used_memory": "5 MiB"}
        ]
        matched, unrelated = ev02_gpu_binding.join_and_classify(gpu_list, compute_apps, "python")
        self.assertEqual(matched[0]["gpu_index"], None)
        self.assertEqual(unrelated, 0)


if __name__ == "__main__":
    unittest.main()
