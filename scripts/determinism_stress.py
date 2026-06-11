#!/usr/bin/env python
"""Adversarial determinism calibration for the dynamic-probe structural hash.

Fails closed (non-zero exit) if the normalized structural hash is not invariant
across:

* many in-process report rebuilds (catches time-tick drift), and
* independent interpreter processes with different ``PYTHONHASHSEED`` values
  (catches set/dict iteration-order leakage into serialized output).

Run locally or in CI: ``python scripts/determinism_stress.py``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

IN_PROCESS_BUILDS = 256
HASH_SEEDS = ("0", "1", "2", "17", "42", "1000", "random")


def _load_probe() -> Any:
    spec = importlib.util.spec_from_file_location(
        "dynamic_environment_probe", ROOT / "scripts" / "dynamic_environment_probe.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _structural_hash() -> str:
    probe = _load_probe()
    from bive.pipeline import analyze_transcript_payload

    sample = json.loads((ROOT / "samples" / "demo_transcript.json").read_text(encoding="utf-8"))
    return str(probe._stable_hash(analyze_transcript_payload(sample).to_dict()))


def _in_process_sweep() -> set[str]:
    return {_structural_hash() for _ in range(IN_PROCESS_BUILDS)}


def _subprocess_for_seed(seed: str) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    if seed != "random":
        env["PYTHONHASHSEED"] = seed
    else:
        env.pop("PYTHONHASHSEED", None)  # let CPython randomize
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--emit-hash"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
        check=True,
    )
    return result.stdout.strip().splitlines()[-1]


def main() -> int:
    if "--emit-hash" in sys.argv:
        print(_structural_hash())
        return 0

    in_process = _in_process_sweep()
    if len(in_process) != 1:
        print(f"DETERMINISM_STRESS_FAIL in-process drift: {sorted(in_process)}", file=sys.stderr)
        return 1
    reference = next(iter(in_process))

    seen: dict[str, str] = {}
    for seed in HASH_SEEDS:
        digest = _subprocess_for_seed(seed)
        seen[seed] = digest
        if digest != reference:
            print(
                f"DETERMINISM_STRESS_FAIL PYTHONHASHSEED={seed} -> {digest} "
                f"!= reference {reference}",
                file=sys.stderr,
            )
            return 1

    print(
        f"DETERMINISM_STRESS_PASS builds={IN_PROCESS_BUILDS} "
        f"seeds={len(HASH_SEEDS)} hash={reference}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
