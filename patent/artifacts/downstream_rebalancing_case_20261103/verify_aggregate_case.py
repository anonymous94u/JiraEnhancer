#!/usr/bin/env python3
"""Verify supplied checksums and aggregate arithmetic; not a raw-trace replay."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
for line in (root/'CHECKSUMS.sha256').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert Path(name).name==name
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
data=json.loads((root/'rebalance_case_verified_metrics.json').read_text())
case=json.loads((root/'story_case_manifest.json').read_text())
assert case['record_kind']=='structured_case_summary'
assert case['story_count']==len(case['stories'])==3
assert {s['component'] for s in case['stories']}=={'Subscriber Service','Java SDK','Python SDK'}
assert case['provenance']['jira_enhancer_origin']=='author-confirmed'
assert case['execution_evidence']['file']=='rebalance_case_verified_metrics.json'
assert set(case['execution_evidence']['run_ids'])=={run['run_id'] for run in data['runs']}
assert len(data['runs'])==2
assert hashlib.sha256((root/'extract_rebalance_case_evidence.py').read_bytes()).hexdigest()==data['extractor_sha256']
for run in data['runs']:
    assert sum(run['client_sizes'])==3300 and run['persistent_client_processes']==5
    assert run['same_client_process_generations_across_retained_stages']
    for stage in run['stages']:
        assert sum(stage['bindings_by_pod_alias'].values())==3300
        assert stage['ready_client_subscription_bindings']==3300
        if stage['stage_end_snapshot_retained']:
            assert stage['minimum_worker_hold_seconds']>=stage['required_minimum_hold_seconds']
    h=run['handoffs'];t=run['main_telemetry']
    assert h['phase_records_total']==8*h['completed']
    assert all(n==h['completed'] for n in h['phase_record_counts'].values())
    assert all(n==h['completed'] for n in h['source_wire_response_counts'].values())
    assert t['main_frames']-t['physical_session_groups']==t['strict_main_to_main_intervals']
    assert t['maximum_seconds']<11 and t['intervals_above_11_seconds']==0
    assert all(code==0 for code in run['cleanup']['worker_exit_codes_by_client_size'].values())
    assert run['business_activity']['business_frames_received']==0
    assert run['business_activity']['ack_frames_sent']==run['business_activity']['nack_frames_sent']==0
print('PASS: file hashes, three-component case manifest, both run aggregates, stage binding totals, holds, phase counts, cadence accounting and cleanup. Raw traces are not included.')
