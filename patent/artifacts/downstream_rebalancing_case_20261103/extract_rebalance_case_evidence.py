#!/usr/bin/env python3
"""Read retained October 15 traces and write only sanitized aggregate JSON.

No network, process control, source modification, or experiments are performed.
All source inputs are read-only. Output must be beneath /private/tmp.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import statistics


DATE = "2026-10-15"
PHASES = ["handshake", "promote", "ready", "commit", "quiesce", "drain",
          "retire_authorized", "retire"]
SIZES = [100, 200, 500, 1000, 1500]



def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Source:
    def __init__(self, root):
        self.root = root.resolve()
        self.hashes = {}

    def path(self, relative):
        p = (self.root / relative).resolve()
        require(self.root in p.parents, "Source path escapes supplied root")
        return p

    def digest(self, relative):
        key = Path(relative).as_posix()
        current = sha256(self.path(relative))
        require(key not in self.hashes or self.hashes[key] == current,
                "Source changed during inspection: " + key)
        self.hashes[key] = current
        return current

    def json(self, relative):
        self.digest(relative)
        return json.loads(self.path(relative).read_text())

    def records(self, relative):
        self.digest(relative)
        with self.path(relative).open() as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)

    def verify_unchanged(self):
        for relative, expected in self.hashes.items():
            require(sha256(self.path(relative)) == expected,
                    "Source changed during inspection: " + relative)


def worker_list(snapshot):
    workers = snapshot["workers"]
    return list(workers.values()) if isinstance(workers, dict) else workers


def extract_run(source, mode, config):
    settings = config[mode]
    report_path = Path(settings["report_path"])
    report = source.json(report_path)
    run_id = f"validation-pooling-{mode}"
    require(report["run_id"] == settings["run_id"], "Unexpected run identity")
    require(report["scope"]["context"] == settings["development_context"],
            "Expected supplied development-validation environment")
    require(report["status"] == "passed_and_restored", "Unexpected run status")
    evidence = report["evidence"]
    require(source.digest(evidence["archive"]) == evidence["archive_sha256"],
            "Archive checksum mismatch")
    for relative, expected in evidence["source_sha256"].items():
        require(source.digest(relative) == expected, "Report source checksum mismatch: " + relative)
    manifest = source.json(evidence["manifest"])
    require(len(manifest) == 19 == evidence["manifest_file_count"], "Unexpected manifest size")
    base = Path(settings["evidence_base"])
    for relative, expected in manifest.items():
        require(source.digest(base / relative) == expected, "Evidence payload checksum mismatch")

    stages_report = report["stages"]
    baseline = report["baseline"]
    first_pod = baseline.get("pod") or baseline["added_pods"][0]
    pods = [first_pod] + [s["added_pods"][0] for s in stages_report]
    require(len(pods) == len(set(pods)) == 4, "Expected four creation-ordered server pods")
    aliases = {p: f"P{i + 1}" for i, p in enumerate(pods)}

    summaries = {}
    telemetry = collections.defaultdict(list)
    transitions = collections.defaultdict(list)
    wire = collections.defaultdict(list)
    unique_subscriptions = set()
    per_worker_subscriptions = {}
    observations_count = 0
    for size in SIZES:
        worker = f"client-{size:04d}"
        summaries[size] = source.json(base / worker / "summary.json")
        own_subscriptions = set()
        for record in source.records(base / worker / "observations.jsonl"):
            observations_count += 1
            kind = record.get("kind")
            if kind == "control_sent" and record.get("command") == "SUBSCRIBE":
                own_subscriptions.add(record["subscription_sha256"])
            if kind == "telemetry_frame_arrived" and record.get("probe") is False:
                group = (size, record["connection"], record["session_sha256"])
                telemetry[group].append(record["monotonic_seconds"])
            if kind == "sdk_handoff_event":
                event = record["event"]
                transitions[(size, event["transition_id"])].append(event)
            if kind == "server_handoff_response":
                wire[(size, record["operationId"])].append(record)
        require(len(own_subscriptions) == size, "Unexpected per-client subscription cardinality")
        per_worker_subscriptions[str(size)] = len(own_subscriptions)
        unique_subscriptions.update(own_subscriptions)
    require(len(unique_subscriptions) == 1500 == report["result"]["unique_subscriptions"],
            "Unique-subscription cardinality mismatch")

    phases = collections.Counter()
    moved = 0
    wire_counts = collections.Counter()
    for key, events in transitions.items():
        ordered = sorted(events, key=lambda e: e["sequence"])
        require([e["phase"] for e in ordered] == PHASES, "Incomplete or unordered handoff phases")
        require(all(a["monotonic_seconds"] <= b["monotonic_seconds"]
                    for a, b in zip(ordered, ordered[1:])), "Nonmonotonic phase timestamps")
        phases.update(e["phase"] for e in ordered)
        commit = next(e for e in ordered if e["phase"] == "commit")
        moved += commit["binding_count"]
        source_states = []
        for response in wire[key]:
            if response["state"] in {"DRAINED", "RETIRED"}:
                require(response["connection_id"] == commit["source_connection_id"]
                        and response["session_sha256"] == commit["source_session_sha256"],
                        "Source wire-response identity mismatch")
                source_states.append(response["state"])
                wire_counts[response["state"]] += 1
        require(source_states == ["DRAINED", "RETIRED"], "Missing or unordered source wire responses")
    expected_complete = report["result"].get("completed_handoffs", report["result"].get("proven_handoffs"))
    expected_moved = report["result"].get("moved_bindings_across_all_handoffs",
                                         report["result"].get("moved_bindings_across_stages"))
    require(len(transitions) == expected_complete, "Completed-handoff count mismatch")
    require(moved == expected_moved, "Cumulative moved-bindings mismatch")

    intervals = []
    for times in telemetry.values():
        gaps = [b - a for a, b in zip(times, times[1:])]
        require(all(g >= 0 for g in gaps), "Nonmonotonic telemetry")
        intervals.extend(gaps)
    cadence = {
        "main_frames": sum(map(len, telemetry.values())),
        "physical_session_groups": len(telemetry),
        "strict_main_to_main_intervals": len(intervals),
        "minimum_seconds": min(intervals),
        "median_seconds": statistics.median(intervals),
        "maximum_seconds": max(intervals),
        "intervals_above_11_seconds": sum(g > 11 for g in intervals),
        "grouping": "worker + physical connection + session; probe=false",
        "excluded_gaps": "cross-session and probe-to-main promotion gaps",
        "interpretation": "telemetry arrival cadence; not business-event latency"
    }
    original_cadence = report["main_connection_stats_cadence"]
    for new_key, original_key in [("main_frames", "main_stats_frames"),
                                  ("strict_main_to_main_intervals", "intervals"),
                                  ("physical_session_groups", "physical_session_groups"),
                                  ("minimum_seconds", "minimum_seconds"),
                                  ("median_seconds", "median_seconds"),
                                  ("maximum_seconds", "maximum_seconds"),
                                  ("intervals_above_11_seconds", "intervals_above_11_seconds")]:
        require(cadence[new_key] == original_cadence[original_key], "Exact cadence mismatch: " + new_key)
    require(cadence["main_frames"] - len(telemetry) == len(intervals), "Interval accounting mismatch")

    stage_results = []
    generations = []
    final_proofs = []
    for stage in [1, 2, 3, 4]:
        sr = baseline if stage == 1 else next(s for s in stages_report if s["stage"] == stage)
        snapshot_path = Path(settings["observation_root"]) / f"pooling-{mode}-v2" / f"stage{stage}-final-state.json"
        exists = source.path(snapshot_path).exists()
        if exists:
            workers = worker_list(source.json(snapshot_path))
            require(sorted(w["client_size"] for w in workers) == SIZES, "Worker count/size mismatch")
            require(all(w["stage"] == stage for w in workers), "Worker stage mismatch")
            require(all(w["ready_subscriptions"] == w["client_size"] for w in workers),
                    "Requested bindings not retained")
            distribution = collections.Counter()
            for w in workers:
                distribution.update(w["bindings_per_pod"])
            ready = sum(w["ready_subscriptions"] for w in workers)
            hold = min(w["stage_seconds"] for w in workers)
            generations.append({w["client_size"]: w["process_generation"] for w in workers})
            require(dict(distribution) == sr["bindings_per_pod"], "Stage placement mismatch")
            require(hold == sr["minimum_worker_hold_seconds"], "Stage hold mismatch")
            if stage == 4:
                final_proofs = [p for w in workers for p in w["proven_handoffs"]]
        else:
            require(mode == "enabled" and stage == 1, "Unexpected missing stage snapshot")
            distribution = {first_pod: baseline["ready_bindings"]}
            ready = baseline["ready_bindings"]
            hold = None
        require(ready == sum(distribution.values()) == 3300, "Stage binding accounting mismatch")
        required_hold = sr["required_hold_seconds"]
        if hold is not None:
            require(hold >= required_hold, "Minimum hold requirement failed")
        stage_results.append({
            "stage_index": stage,
            "server_pod_count": stage,
            "bindings_by_pod_alias": {aliases[p]: int(distribution.get(p, 0)) for p in pods},
            "ready_client_subscription_bindings": ready,
            "minimum_worker_hold_seconds": hold,
            "required_minimum_hold_seconds": required_hold,
            "hold_gate_passed": hold >= required_hold if hold is not None else baseline["hold_gate_passed"],
            "stage_end_snapshot_retained": exists,
            "completed_handoffs_in_rollout_window_reported": sr.get("completed_handoffs_in_rollout_window", sr.get("proven_handoffs", 0)),
            "new_pod_handoffs_verified": sr.get("credited_new_pod_handoffs", sr.get("proven_handoffs", 0)),
            "bindings_moved_to_added_pods": sr.get("moved_bindings_to_added_pods", 0)
        })
    require(all(g == generations[0] for g in generations), "Worker process generation changed")
    credited = collections.Counter()
    credited_bindings = collections.Counter()
    for proof in final_proofs:
        require(all(proof[k] is True for k in ["committed_owner_observed", "same_session_receipts",
                                               "wire_drained", "wire_retired"]), "Handoff proof flag failed")
        require(proof["target_pod"] == pods[proof["stage"] - 1], "New-pod attribution mismatch")
        credited[proof["stage"]] += 1
        credited_bindings[proof["stage"]] += proof["binding_count"]
    for stage in stage_results:
        i = stage["stage_index"]
        require(credited[i] == stage["new_pod_handoffs_verified"], "Credited stage count mismatch")
        require(credited_bindings[i] == stage["bindings_moved_to_added_pods"], "Credited binding count mismatch")

    traffic = {}
    for original, aggregate in [("business_frames", "business_frames_received"),
                                 ("callbacks_completed", "callbacks_completed"),
                                 ("ack_frames_sent", "ack_frames_sent"),
                                 ("nack_frames_sent", "nack_frames_sent"),
                                 ("server_errors", "server_errors")]:
        observed = sum(s["counters"][original] for s in summaries.values())
        require(observed == report["traffic"][aggregate] == 0, "Unexpected traffic or error count")
        traffic[aggregate] = observed
    traffic["events_published_by_test_reported"] = report["traffic"]["events_published_by_test"]
    require(traffic["events_published_by_test_reported"] == 0, "Unexpected published events")
    traffic["event_delivery_and_ack_nack_settlement_exercised"] = False

    matrix = source.json(base / "matrix-summary.json")
    cleanup = report["cleanup"]
    for key in ["owned_processes_stopped", "worker_exit_codes", "forced_termination", "cleanup_errors"]:
        require(matrix[key] == cleanup[key], "Cleanup summary mismatch")
    require(set(cleanup["worker_exit_codes"].values()) == {0}, "Nonzero worker exit")
    require(cleanup["owned_processes_stopped"] and not cleanup["forced_termination"]
            and not cleanup["cleanup_errors"], "Incomplete cleanup")
    return {
        "run_id": run_id, "date": DATE, "pooling": mode,
        "scope": "development validation; subscription-only scale-out; Python SDK",
        "client_sizes": SIZES, "persistent_client_processes": len(SIZES),
        "requested_client_subscription_bindings": sum(SIZES),
        "unique_logical_subscriptions": len(unique_subscriptions),
        "unique_subscription_basis": "distinct subscription hashes in recorded SUBSCRIBE sends",
        "pod_alias_rule": "P1..P4 in server-pod creation order, independently within each run",
        "same_client_process_generations_across_retained_stages": True,
        "stages": stage_results,
        "handoffs": {
            "completed": len(transitions), "credited_new_pod": len(final_proofs),
            "cumulative_binding_moves_all": moved,
            "cumulative_binding_moves_to_new_pods": sum(credited_bindings.values()),
            "binding_moves_are_not_distinct_subscription_counts": True,
            "exact_phase_sequence": PHASES, "phase_record_counts": dict(phases),
            "phase_records_total": sum(phases.values()),
            "incomplete_or_extra_phase_sequences": 0,
            "source_wire_response_counts": dict(wire_counts),
            "all_snapshot_proof_flags_true": True,
            "stage_attribution": "controller-confirmed newly added target pod; transitions may start before stage-control delivery"
        },
        "main_telemetry": cadence,
        "business_activity": traffic,
        "cleanup": {"owned_workers_stopped": True, "worker_exit_codes_by_client_size": cleanup["worker_exit_codes"],
                    "forced_termination_count": 0, "cleanup_error_count": 0,
                    "restoration_reported": bool(report["restoration"]["restored"])},
        "configuration_limits": {
            "test_probe_interval_seconds": report["configuration"]["probe_interval_seconds"],
            "test_probe_jitter_seconds": report["configuration"]["probe_jitter_seconds"],
            "test_cooldown_seconds": report["configuration"]["cooldown_seconds"],
            "default_probe_interval_seconds": report["configuration"]["sdk_default_probe_interval_seconds_unchanged"],
            "default_probe_jitter_seconds": report["configuration"]["sdk_default_probe_jitter_seconds_unchanged"],
            "tls_certificate_verification_enabled": report["configuration"]["verify_tls"]
        },
        "provenance": {
            "report_file": f"validation-pooling-{mode}.json", "report_sha256": None,
            "archive_file": f"validation-pooling-{mode}.tar.gz", "archive_sha256": None,
            "manifest_file": f"validation-pooling-{mode}-manifest.json", "manifest_sha256": None,
            "manifest_files_verified": len(manifest), "all_report_source_hashes_verified": True,
            "release_baseline_commit": None,
            "identifier_policy": "Source identifiers and original-source digests withheld; output names are aliases.",
            "release_baseline_is_not_event_identifier": True,
            "original_deployed_image_source_commit_established": False,
            "observations_read": observations_count
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Local retained source checkout; read-only")
    parser.add_argument("--private-config", type=Path, required=True,
                        help="Local configuration with enabled/disabled report_path, run_id, development_context, evidence_base and observation_root; never exported")
    parser.add_argument("--output", type=Path, default=Path("/private/tmp/rebalance_case_verified_metrics.json"))
    args = parser.parse_args()
    output = args.output.resolve()
    require(Path("/private/tmp") in output.parents, "Output must be beneath /private/tmp")
    require(output.parent.is_dir(), "Output directory must already exist")
    source = Source(args.source_root)
    config = json.loads(args.private_config.read_text())
    runs = [extract_run(source, mode, config) for mode in ["enabled", "disabled"]]
    source.verify_unchanged()
    result = {
        "schema_version": 1, "case": "subscription-migration downstream execution case",
        "verification": "read-only arithmetic, trace-sequence and source-checksum verification",
        "date_of_runs": DATE,
        "generation_link_status": "Jira Enhancer origin is author-reported; this extraction verifies runtime evidence only",
        "limits": ["Single downstream case, not a success-rate estimate for the broader pilot",
                   "No business-event delivery, callback, ACK or NACK exercise",
                   "Telemetry cadence does not establish business-event latency or no-loss delivery",
                   "Client processes, server pods, physical sessions and logical subscriptions are distinct units",
                   "Enabled baseline gate passed, but a separate baseline final-state snapshot was not retained",
                   "Pooling-mode runs are separate scenarios, not a matched statistical treatment-effect estimate"],
        "runs": runs,
        "source_files_sha256": [
            {"file": f"SOURCE_{index:03d}",
             "scope": next((f"validation-pooling-{mode}" for mode in ["enabled", "disabled"]
                            if Path(config[mode]["evidence_base"]) in Path(relative).parents), "shared"),
             "client_size": next((int(part.split("-")[1]) for part in Path(relative).parts
                                   if part.startswith("client-") and part[7:].isdigit()), None),
             "sha256": None}
            for index, (relative, digest) in enumerate(sorted(source.hashes.items()), 1)
        ],
        "all_source_bytes_unchanged_during_extraction": True,
        "extractor_sha256": sha256(Path(__file__).resolve()),
        "anonymous_provenance_note": "Original-source digests withheld; extractor_sha256 identifies this sanitized extractor. Private inputs and configuration are not exported."
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "runs_verified": len(runs),
                      "manifest_payloads_verified": sum(r["provenance"]["manifest_files_verified"] for r in runs),
                      "source_files_checked": len(source.hashes), "output_sha256": sha256(output)}))


if __name__ == "__main__":
    main()
