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
import ev05_admission_load as ev05  # noqa: E402
import ev06_interrupt_probe as ev06  # noqa: E402
import ev08_exit_probe as ev08  # noqa: E402
import host_inventory  # noqa: E402
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


WINDOWS_SMI_HEADER = (
    "Sun Sep 20 23:42:26 2026       \n"
    "+-----------------------------------------------------------------------------------------+\n"
    "| NVIDIA-SMI 616.92                 KMD Version: 616.92        CUDA UMD Version: 13.4     |\n"
    "+-----------------------------------------+------------------------+----------------------+\n"
)
LINUX_SMI_HEADER = (
    "Sat Sep 19 10:00:00 2026       \n"
    "+-----------------------------------------------------------------------------------------+\n"
    "| NVIDIA-SMI 550.54.14              Driver Version: 550.54.14      CUDA Version: 12.4     |\n"
    "+-----------------------------------------+------------------------+----------------------+\n"
)


class TestHostInventoryCudaParsing(unittest.TestCase):
    def test_windows_header_uses_cuda_umd_label(self) -> None:
        self.assertEqual(
            host_inventory.parse_cuda_version(WINDOWS_SMI_HEADER), ("CUDA UMD Version:", "13.4")
        )

    def test_linux_header_uses_cuda_version_label(self) -> None:
        self.assertEqual(
            host_inventory.parse_cuda_version(LINUX_SMI_HEADER), ("CUDA Version:", "12.4")
        )

    def test_header_without_cuda_field_returns_none(self) -> None:
        header = (
            "| NVIDIA-SMI 616.92                 KMD Version: 616.92                              |"
        )
        self.assertIsNone(host_inventory.parse_cuda_version(header))


class TestHostInventoryNtpParsing(unittest.TestCase):
    def test_w32tm_stripchart_offsets(self) -> None:
        text = (
            "Tracking time.windows.com [52.148.114.188:123].\n"
            "Collecting 3 samples.\n"
            "The current time is 9/20/2026 11:44:07 PM.\n"
            "23:44:07, -00.6247612s\n"
            "23:44:09, -00.6253330s\n"
            "23:44:11, +00.0012000s\n"
        )
        self.assertEqual(
            host_inventory.parse_w32tm_stripchart(text), [-0.6247612, -0.625333, 0.0012]
        )

    def test_chronyc_fast_is_positive_local_minus_server(self) -> None:
        text = "Reference ID    : A9FEA97B\nSystem time     : 0.000012 seconds fast of NTP time\n"
        self.assertEqual(host_inventory.parse_chronyc_tracking(text), [0.000012])

    def test_chronyc_slow_is_negative(self) -> None:
        text = "System time     : 0.250000 seconds slow of NTP time\n"
        self.assertEqual(host_inventory.parse_chronyc_tracking(text), [-0.25])

    def test_ntpdate_offset_sign_is_inverted_to_local_minus_server(self) -> None:
        text = "server 1.2.3.4, stratum 2, offset -0.001234, delay 0.02567\n"
        self.assertEqual(host_inventory.parse_ntpdate_query(text), [0.001234])

    def test_unparseable_ntp_output_gives_empty_list(self) -> None:
        self.assertEqual(host_inventory.parse_w32tm_stripchart("The command failed"), [])
        self.assertEqual(host_inventory.parse_chronyc_tracking("nothing"), [])
        self.assertEqual(host_inventory.parse_ntpdate_query("no servers"), [])

    def test_default_ntp_server_by_platform(self) -> None:
        self.assertEqual(host_inventory.default_ntp_server("Windows"), "time.windows.com")
        self.assertEqual(host_inventory.default_ntp_server("Linux"), "pool.ntp.org")

    def test_ntp_check_disabled_returns_none_without_observation(self) -> None:
        observations: list[str] = []
        self.assertIsNone(host_inventory.collect_ntp_offset(False, None, observations))
        self.assertEqual(observations, [])


def _req(sent: float, first: float | None, done: float | None) -> dict[str, float | None]:
    return {"sent": sent, "first_token": first, "done": done}


class TestEv05AdmissionLoad(unittest.TestCase):
    METRICS = (
        "# HELP vllm:num_requests_running Number of requests in model execution batches.\n"
        "# TYPE vllm:num_requests_running gauge\n"
        'vllm:num_requests_running{engine="0",model_name="typhoon"} 4.0\n'
        'vllm:num_requests_waiting{engine="0",model_name="typhoon"} 8.0\n'
        "vllm:num_requests_waiting_by_reason NaN\n"
        "broken line without value\n"
    )

    def test_parse_prometheus_sums_label_sets_and_skips_comments(self) -> None:
        parsed = ev05.parse_prometheus(self.METRICS + 'vllm:num_requests_running{engine="1"} 1\n')
        self.assertEqual(parsed[ev05.RUNNING], 5.0)
        self.assertEqual(parsed[ev05.WAITING], 8.0)
        self.assertNotIn("broken", parsed)

    def test_client_bounds_upper_lower_streaming(self) -> None:
        requests = [
            _req(0.0, 1.0, 10.0),  # inside the whole window
            _req(4.5, None, None),  # failed at send, inside window -> upper only
            _req(6.0, 7.0, 8.0),  # sent after the window
            _req(0.0, 0.5, 2.0),  # finished before the window
        ]
        bounds = ev05.client_bounds(requests, 4.0, 5.0)
        self.assertEqual(bounds, {"upper": 2, "lower": 1, "streaming_upper": 1})

    def test_compare_flags_over_count_and_limit(self) -> None:
        requests = [_req(0.0, 0.1, 10.0) for _ in range(5)]
        samples = [
            {"t0": 1.0, "t1": 1.1, "status": 200, "running": 4.0, "waiting": 1.0},  # exact
            {"t0": 2.0, "t1": 2.1, "status": 200, "running": 5.0, "waiting": 2.0},  # over + limit
            {"t0": 3.0, "t1": 3.1, "status": 500, "running": None, "waiting": None},  # unscored
        ]
        stats = ev05.compare(samples, requests, limit=4)
        self.assertEqual(stats["samples_scored"], 2)
        self.assertEqual(stats["samples_total_above_client_upper"], 1)
        self.assertEqual(stats["samples_running_above_client_upper"], 0)
        self.assertEqual(stats["samples_running_above_limit"], 1)
        self.assertEqual(stats["max_waiting"], 2.0)

    def test_compare_counts_under_count(self) -> None:
        requests = [_req(0.0, 0.1, 10.0) for _ in range(3)]
        samples = [{"t0": 1.0, "t1": 1.1, "status": 200, "running": 1.0, "waiting": 0.0}]
        stats = ev05.compare(samples, requests, None)
        self.assertEqual(stats["samples_total_below_client_lower"], 1)

    def test_find_max_num_seqs_in_log_json_and_absence(self) -> None:
        log = "INFO args: Namespace(max_num_seqs=4, max_model_len=8192)"
        self.assertEqual(ev05.find_max_num_seqs(log), [4])
        self.assertEqual(ev05.find_max_num_seqs('{"max_num_seqs": 256}'), [256])
        self.assertEqual(ev05.find_max_num_seqs('{"max_model_len": 8192}'), [])


def _sample(t: float, gen: float | None, proc: float = 1.0, running: float = 0.0) -> dict:
    return {"t": t, "gen_tokens": gen, "proc_start": proc, "running": running, "waiting": 0.0}


class TestEv06InterruptProbe(unittest.TestCase):
    def test_classify_ending(self) -> None:
        cases = [
            ({"status": None}, "no_response"),
            ({"status": None, "client_cancel_at": 5.0}, "client_cancelled_before_response"),
            ({"status": 500}, "http_500"),
            ({"status": 200, "finish_reason": "length"}, "completed"),
            ({"status": 200, "client_cancel_at": 5.0}, "client_cancelled"),
            ({"status": 200}, "cut_without_finish_reason"),
            ({"status": 200, "error_chunk": '{"code": 500}'}, "error_chunk_in_stream"),
        ]
        for record, expected in cases:
            self.assertEqual(ev06.classify_ending(record), expected, record)

    def test_counter_rise_within_one_process_and_window(self) -> None:
        samples = [_sample(0, 10), _sample(1, 15), _sample(2, 15), _sample(3, 40), _sample(9, 99)]
        self.assertEqual(ev06.counter_rise(samples, 0, 5), 30.0)
        self.assertEqual(ev06.counter_rise(samples, 2, 2), 0.0)

    def test_counter_rise_ignores_reset_on_restart(self) -> None:
        samples = [_sample(0, 500, proc=1), _sample(1, 0, proc=2), _sample(2, 7, proc=2)]
        self.assertEqual(ev06.counter_rise(samples, 0, 5), 7.0)
        self.assertEqual(ev06.counter_rise([_sample(0, None), _sample(1, 3)], 0, 5), 0.0)

    def test_first_idle_after(self) -> None:
        samples = [_sample(0, 0, running=1), _sample(1, 0, running=0), _sample(2, 0, running=0)]
        self.assertEqual(ev06.first_idle_after(samples, 0.5), 1)
        self.assertIsNone(ev06.first_idle_after(samples[:1], 0))

    def test_engine_pids_from_grep_output(self) -> None:
        out = "/proc/131/cmdline\n/proc/131/comm\n/proc/1/cmdline\n/proc/self/cmdline\n"
        self.assertEqual(ev06.engine_pids(out), [1, 131])

    def test_find_routes(self) -> None:
        spec = {"paths": {"/v1/chat/completions": {}, "/abort_request": {}, "/health": {}}}
        self.assertEqual(ev06.find_routes(spec), ["/abort_request"])
        self.assertEqual(ev06.find_routes({}), [])


class TestEv08ExitProbe(unittest.TestCase):
    INSPECT = {
        "Image": "sha256:abc",
        "Args": ["--model", "/models", "--max-num-seqs", "4"],
        "Config": {
            "Image": "vllm/vllm-openai:latest",
            "Entrypoint": ["vllm", "serve"],
            "Cmd": ["--model", "/models", "--max-num-seqs", "4"],
            "Env": ["PATH=/usr/bin", "VLLM_API_KEY=sk-secret", "VLLM_WSL2_ENABLE_PIN_MEMORY=1"],
        },
        "HostConfig": {
            "PortBindings": {"8000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8000"}]},
            "DeviceRequests": [{"Count": -1, "Capabilities": [["gpu"]]}],
            "IpcMode": "host",
        },
        "Mounts": [
            {
                "Source": "/run/desktop/mnt/host/f/prp-models/m",
                "Destination": "/models",
                "RW": False,
            }
        ],
    }

    def test_user_env_drops_image_defaults(self) -> None:
        pairs = ev08.user_env(["PATH=/usr/bin", "A=1", "PATH2=x"], ["PATH=/usr/bin"])
        self.assertEqual(pairs, [("A", "1"), ("PATH2", "x")])

    def test_redact_env_keeps_only_allow_listed_values(self) -> None:
        out = ev08.redact_env([("VLLM_API_KEY", "sk-1"), ("SAFE", "1")], {"SAFE"})
        self.assertEqual(out[0], {"name": "VLLM_API_KEY", "value": ev08.REDACTED})
        self.assertEqual(out[1], {"name": "SAFE", "value": "1"})

    def test_host_path(self) -> None:
        self.assertEqual(ev08.host_path("/run/desktop/mnt/host/f/prp-models/m"), "F:/prp-models/m")
        self.assertEqual(ev08.host_path("/srv/models"), "/srv/models")

    def test_build_spec_redacts_and_keeps_launch_shape(self) -> None:
        spec = ev08.build_spec(self.INSPECT, ["PATH=/usr/bin"], {"VLLM_WSL2_ENABLE_PIN_MEMORY"})
        self.assertNotIn("sk-secret", str(spec))
        self.assertEqual(spec["gpus"], "all")
        self.assertEqual(spec["ipc_mode"], "host")
        self.assertEqual(
            spec["mounts"], [{"source": "F:/prp-models/m", "target": "/models", "ro": True}]
        )
        self.assertEqual(spec["ports"][0]["host_ip"], "127.0.0.1")
        self.assertEqual(spec["args"][-1], "4")
        self.assertIn({"name": "VLLM_WSL2_ENABLE_PIN_MEMORY", "value": "1"}, spec["env"])
        self.assertEqual(spec["entrypoint"], ["vllm", "serve"])  # differs from no image entrypoint
        same = ev08.build_spec(self.INSPECT, [], set(), ["vllm", "serve"])
        self.assertIsNone(same["entrypoint"])

    def test_build_spec_keeps_program_when_cmd_replaced(self) -> None:
        inspect = {
            "Path": "python",
            "Args": ["-u", "/app/x.py"],
            "Config": {"Cmd": ["python", "-u", "/app/x.py"]},
        }
        self.assertEqual(ev08.build_spec(inspect, [], set())["args"], ["python", "-u", "/app/x.py"])

    def test_diff_fingerprints(self) -> None:
        a = {
            "non_default_args": "x",
            "models": [1],
            "cache_config_info": "c",
            "completion_text": "t",
        }
        self.assertTrue(ev08.diff_fingerprints(a, dict(a))["equal"])
        diff = ev08.diff_fingerprints(a, {**a, "completion_text": "u"})
        self.assertFalse(diff["equal"])
        self.assertFalse(diff["completion_text"]["equal"])
        self.assertTrue(diff["models"]["equal"])

    def test_find_markers_case_insensitive(self) -> None:
        self.assertEqual(ev08.find_markers("Server: Uvicorn", ["uvicorn", "vllm"]), ["uvicorn"])

    def test_parse_docker_diff(self) -> None:
        rows = ev08.parse_docker_diff("C /root\nA /root/.cache/x\nD /tmp/y\nnoise\n")
        self.assertEqual([r["kind"] for r in rows], ["C", "A", "D"])
        self.assertEqual(rows[1]["path"], "/root/.cache/x")

    def test_non_default_args_takes_last_line(self) -> None:
        log = "x non-default args: {'a': 1}\ny non-default args: {'a': 2, 'b': 3}\n"
        self.assertEqual(ev08.non_default_args(log), "{'a': 2, 'b': 3}")
        self.assertIsNone(ev08.non_default_args("nothing here"))


if __name__ == "__main__":
    unittest.main()
