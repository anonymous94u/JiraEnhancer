Downstream subscription-rebalancing execution case

This package supports Appendix D of the Jira Enhancer manuscript. The study
owner identifies one enhancement spanning Subscriber Service, Java client,
and Python client stories as Jira Enhancer planning output. The original
story-generation payload for these selected stories is not reconstructed by
this package; that association is author-confirmed.

The October 15, 2026 runtime archives verify the Subscriber Service/Python
subscription-only path under pooling enabled and disabled. They do not test
Java active migration or business-event delivery. No business events, callbacks,
ACKs or NACKs occurred. These two runs are descriptive validations, not a
randomized planning-method comparison or an estimate of portfolio success.

Contents
- story_case_manifest.json: the three author-selected component records,
  author-confirmed story origin, verified execution coverage, and a relative
  link to the run aggregates. This is a structured case summary; full original
  story descriptions and acceptance criteria are not reconstructed.
- rebalance_case_verified_metrics.json: stage distributions, minimum holds,
  handoff/phase counts, physical-session telemetry aggregates, cleanup results,
  configuration limits and source-audit status. Pods use P1..P4 aliases within each
  run. Neither issue keys nor individual connection/worker identities appear.
- extract_rebalance_case_evidence.py: read-only trace/hash verification with
  restricted source archives and private path/run configuration supplied explicitly.
- verify_aggregate_case.py: checks this public package's hashes and arithmetic.
- CHECKSUMS.sha256: SHA-256 of all five other files.

Public aggregate checks (Python 3, standard library only)
  python3 verify_aggregate_case.py

Restricted-source reconstruction
  python3 extract_rebalance_case_evidence.py --source-root /path/to/checkout \
    --private-config /path/to/private-config.json \
    --output /private/tmp/rebalance_case_recomputed.json

The private configuration supplies enabled/disabled report_path, run_id,
development_context, evidence_base and observation_root values for the retained
Organization Cloud Infrastructure validation records. It is not included or exported.
The extractor checks both archive hashes, 19 payload hashes per run, source
hashes, ordered handoff sequences, receipt/wire-response counts, stage-end
snapshots, and cadence within each client/physical-connection/session group.
Its output is restricted to /private/tmp. It performs no network calls,
changes no source files, and does not rerun the experiment.

The raw logs and source archives are access-controlled and are not included.
Original-source digests and revision identifiers are withheld for anonymous
review. The retained source-verification flags describe the original inspection;
the public aggregate check cannot reconstruct the operational trace.
Run and file names are aliases, not original event IDs. CHECKSUMS.sha256 and
extractor_sha256 cover the sanitized files supplied here. The sanitized extractor
was not rerun against private archives for this release. The original deployed
image source revision remains unestablished.
