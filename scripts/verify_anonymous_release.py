#!/usr/bin/env python3
"""Verify the anonymous release manifest and generic disclosure boundaries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".jsonl", ".csv", ".tex", ".yaml", ".yml", ".toml", ".svg", ".drawio", ".sha256"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocked-terms-file", type=Path)
    args = parser.parse_args()
    blocked = []
    if args.blocked_terms_file:
        blocked = [x.strip().casefold() for x in args.blocked_terms_file.read_text().splitlines() if x.strip()]
    manifest = json.loads((ROOT / "RELEASE_FILE_MANIFEST.json").read_text())
    failures = []
    patterns = {
        "personal filesystem path": re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+(?:/|$)"),
        "private key": re.compile(r"-----BEGIN(?: RSA| EC| OPENSSH)? PRIVATE KEY-----"),
        "access token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    }
    email = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
    allowed_mail = {"example.com", "example.org", "example.net", "users.noreply.github.com"}
    for name, expected in manifest["files"].items():
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or ".git" in rel.parts:
            failures.append(f"unsafe manifest path: {name}")
            continue
        path = ROOT / rel
        if not path.is_file() or path.is_symlink():
            failures.append(f"missing or linked file: {name}")
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            failures.append(f"checksum mismatch: {name}")
        if path.suffix in TEXT_SUFFIXES or path.name in {"Makefile", ".env.example", ".gitignore"}:
            content = data.decode("utf-8")
            for label, pattern in patterns.items():
                if pattern.search(content):
                    failures.append(f"{label}: {name}")
            if any(domain.casefold() not in allowed_mail for domain in email.findall(content)):
                failures.append(f"non-example email: {name}")
            if any(term in content.casefold() or term in name.casefold() for term in blocked):
                failures.append(f"blocked identifier: {name}")
    if (ROOT / ".git").is_dir():
        result = subprocess.run(["git", "log", "--all", "--format=%an <%ae>|%cn <%ce>"], cwd=ROOT, capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if any("anonymous" not in identity.casefold() for identity in line.split("|")):
                failures.append("non-anonymous Git author or committer")
                break
    print(json.dumps({"files_checked": len(manifest["files"]), "failures": sorted(set(failures)), "passed": not failures}, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
