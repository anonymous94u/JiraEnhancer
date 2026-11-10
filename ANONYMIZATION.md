# Anonymous replication release

This repository contains the executable workflow, synthetic connector fixtures,
aggregate study records, verification scripts, and figure-generation inputs.
The deployment environment is described as **Organization Cloud Infrastructure**.

Personal names, institutional affiliations, internal endpoints, original issue
and component identifiers, location-specific run names, private filesystem
paths, original commit identities, and private source digests are excluded or
replaced by consistent neutral aliases. Missing private-source digests are
explicitly marked as withheld; public-file checksums verify the distributed
files and do not substitute for restricted-source provenance.

The release preserves the measured quantities, aggregation units, experimental
conditions, policy behavior, and statistical calculations. Demonstration issue,
page, and pull-request identifiers are synthetic and are remapped consistently
across fixtures and tests. Plot metadata contains no personal attribution or
machine-specific timestamps. Original raw traces and private reviewer records
are not distributed.

The repository is published as a new history, with anonymous commit authorship.
It does not include identified manuscripts, title pages, local credentials,
runtime caches, or earlier Git history. The public code and research subject
may still be recognizable by comparison with other public materials.

## Verify the snapshot

```sh
python3 scripts/verify_anonymous_release.py
```

This verifies every distributed file against `RELEASE_FILE_MANIFEST.json`,
checks for private key/token material, non-example contact addresses, personal
filesystem paths, and identified commit authorship when Git history is present.
An optional `--blocked-terms-file` accepts an external newline-separated list
for an additional identity scan. Keep such a list outside the repository;
including the original names in a public redaction dictionary would disclose
them again.

The reproduction commands and evidence boundaries are documented in
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).
