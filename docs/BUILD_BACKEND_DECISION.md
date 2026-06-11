# Build Backend Decision

## Decision

BIVE uses the **standard, PyPA-maintained `setuptools.build_meta` backend** with
build-time requirements pinned to non-vulnerable floors:

```toml
[build-system]
requires = ["setuptools>=78.1.1", "wheel>=0.46.2"]
build-backend = "setuptools.build_meta"
```

## Rejected alternative

An **in-tree, hand-rolled PEP 517/660 backend** (`build_backend.py` at the
repository root, declared via `backend-path = ["."]` with `requires = []`).

## Why

The in-tree backend hand-authored wheel/sdist archives, `METADATA`, `WHEEL`,
`entry_points.txt` and the `RECORD` hash table itself. That carries three costs
that a research/product system should not pay:

1. **Specification drift.** `RECORD` hashing, metadata version fields, editable
   `.pth`/finder semantics and data-file handling are defined by living PEPs
   (627, 639, 660, …). A bespoke writer silently diverges from them over time;
   `setuptools.build_meta` tracks them by construction.
2. **Repository-hygiene failure.** `backend-path = ["."]` forces Python to import
   `build_backend.py` from the repo root during every `pip install`, which writes
   `./__pycache__/build_backend.cpython-3xx.pyc`. The first release gate
   (`repo-clean`) then fails with `REPO_DIRTY`. Removing the root backend removes
   this failure class entirely rather than papering over it with bytecode
   suppression that any contributor's manual `pip install` would re-break.
3. **No proof.** The in-tree backend shipped with no parity tests, so its
   correctness was asserted, not verified.

`setuptools.build_meta` is the proven default, requires no in-tree code to
maintain, and produces a wheel that satisfies the existing `wheel-smoke` gate
(package data under `bive/web/**` and `bive/resources/*.json`, the five console
-script entry points, and a temp-venv import check).

## Risks and mitigations

- **Build isolation fetches setuptools/wheel at build time.** Mitigated by
  pinning non-vulnerable floors in `[build-system].requires`, by the canonical
  `requirements/constraints.txt`, and by `make dependency-audit` (live
  `pip-audit`, fail-closed on any known vulnerability).
- **PEP 639 SPDX license string** (`license = "Apache-2.0"`) requires
  `setuptools>=77`; the pinned `>=78.1.1` floor satisfies this and the
  `GHSA-cx63-2mw6-8hw5` / `GHSA-5rjg-fvgr-3xxf` advisories.

## Verification commands

```bash
python -m pip install --constraint requirements/constraints.txt -e '.[dev,api,security]'
python scripts/check_environment.py     # build_backend → setuptools.build_meta, importable
make wheel-smoke                         # wheel members, entry points, temp-venv import
make verify-release                      # full gate spine
make dependency-audit                    # live advisory audit, fail-closed
```

## Rollback path

`git revert` the integration commit restores the in-tree backend and the prior
`[build-system]` table. No data migration is involved; the package layout
(`src/bive`, `package-data`) is backend-independent.
