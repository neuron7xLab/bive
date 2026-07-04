<div align="center">

<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='104' height='104' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='15' fill='none' stroke='%23888' stroke-opacity='.35'/%3E%3Ccircle cx='32' cy='32' r='19' fill='none' stroke='%23ffc46f' stroke-width='3'/%3E%3Ccircle cx='32' cy='32' r='6' fill='%23ffc46f'/%3E%3C/svg%3E" alt="COGVERITAS" width="104" height="104" />

# COGVERITAS

### Evidence-first testimony review — deliberately without a verdict.

Turn a raw statement into a structured review: which claims are **externally checkable**,
where to find the record that confirms them, the reconstructed **timeline**, the entities,
the follow-up questions — and a tamper-evident fingerprint. It never labels a person a liar.

<br/>

[![CI](https://github.com/neuron7xLab/bive/actions/workflows/ci.yml/badge.svg)](https://github.com/neuron7xLab/bive/actions/workflows/ci.yml)
[![CodeQL](https://github.com/neuron7xLab/bive/actions/workflows/codeql.yml/badge.svg)](https://github.com/neuron7xLab/bive/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/neuron7xLab/bive/badge)](https://scorecard.dev/viewer/?uri=github.com/neuron7xLab/bive)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache_2.0-3b6ea8)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10_·_3.11_·_3.12-3b6ea8)](pyproject.toml)
<br/>
[![verdict](https://img.shields.io/badge/verdict-null%20by%20construction-c9964a)](#the-invariant-that-earns-trust)
[![not a lie detector](https://img.shields.io/badge/not-a%20lie%20detector-8b8f9e)](#the-honest-boundary)
[![language detection](https://img.shields.io/badge/language%20detection-99.4%25%20held--out-1f857a)](research/cogveritas/validation/)

**[▶  Open the live demo](https://claude.ai/code/artifact/33b3fbef-1254-4ea8-bf3c-6ae594b242f3)** &nbsp;·&nbsp; a real Ukrainian statement analysed by the live engine

</div>

---

> **COGVERITAS is an evidence-review surface, not a lie detector.** It extracts externally
> checkable claims, says what to corroborate and where, reports uncertainty, and preserves
> provenance — and leaves the judgment to a human. Passive verbal deception detection is
> empirically at chance on real high-stakes testimony, so no "truthfulness score" is emitted.
> That refusal is the feature.

## What it produces

From one block of testimony (Ukrainian, Russian or English — auto-detected):

| Output | What it gives an analyst |
| --- | --- |
| **Verifiability map** | Each statement tagged *externally checkable* vs *opinion / judgment* |
| **Corroboration worklist** | Per checkable claim, the record type that would confirm it — *where to look* |
| **Timeline** | Time-anchored claims in chronological order, with clean human dates |
| **Entity index** | People and places clustered across inflections, with mention counts |
| **Interview questions** | Elicit-only follow-ups that surface checkable detail — never accusations |
| **Integrity fingerprint** | Deterministic `sha256` chain-of-custody; any edit changes the hash |

Every response carries `verdict = null` — structurally, at the type boundary.

## Validated on real, open data

Measured on a real open corpus (Tatoeba, CC BY 2.0 FR), on a **held-out** split the model
was never tuned on, with 95% Wilson intervals. Full harness: [`research/cogveritas/validation/`](research/cogveritas/validation/).

| Property | Result |
| --- | --- |
| Language detection — overall | **0.994** &nbsp;[0.969, 0.999] |
| &nbsp;&nbsp;· Ukrainian / English | 1.000 / 1.000 |
| &nbsp;&nbsp;· Russian | 0.983 &nbsp;[0.911, 0.997] |
| Verifiability separation (face validity) | 0.958 &nbsp;[0.80, 0.99], n = 24 |
| No-verdict invariant | **holds** over 383 real + 14 adversarial inputs |
| Probability suppression | holds — 0 unproven probabilities emitted |
| Integrity fingerprint | reproducible in-run **and** across `PYTHONHASHSEED` |

```bash
PYTHONPATH=src python research/cogveritas/validation/validate_operational.py
# → OPERATIONAL_VALIDATION_PASS
```

## The invariant that earns trust

The no-verdict rule is **enforced at construction, not promised in prose**:

- `verdict` is typed `None` and rejected at construction if ever set.
- A calibrated probability is impossible unless calibration evidence (`ece < 0.10`) rides with it — checked on the type, not by convention.
- The forbidden-judgment scan closes over the **whole** output tree, fail-safe: any system-authored text field is scanned for person-level judgment unless explicitly declared user evidence.
- The institutional maturity score is derived only from passing gates and **capped below benchmark-grade** while no third-party replication exists.

> A higher maturity score is earned by making unsupported claims impossible — if the system
> cannot prove it is not lying, the correct state is *blocked*, not *pass*.

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,api,security]"
make verify-release          # → VERIFY_RELEASE_PASS
make api                     # → http://127.0.0.1:8080
```

Analyse a statement from the console (drag-and-drop) or the API:

```bash
curl -sS -X POST \
  "http://127.0.0.1:8080/api/v1/cogveritas/verifiability?api-version=2026-06-11" \
  --data-binary @statement.txt
# → the full COGVERITAS contract; verdict is always null
```

Or from the CLI, on a transcript in any supported format (JSON, JSONL, SRT, VTT, CSV, TXT — auto-detected):

```bash
bive analyze --input samples/demo_transcript.srt --output report.json
bive render  --input report.json --output report.md
```

## How it's built

A src-layout Python package (FastAPI + pydantic v2), `mypy --strict`, deterministic core,
SQLite storage and a packaged static web console. Correctness is defended by a release
battery and an institutional-verification capstone in CI (py 3.10 / 3.11 / 3.12 + CodeQL):

- **~46 release gates** — repo hygiene, contracts, lint, type, coverage, schema, security-static, wheel-smoke, manifest.
- **Mutation testing** — proves the crown-jewel invariant tests fail on a real defect.
- **Adversarial guard** — hostile inputs (injected verdicts, accusations, degenerate text) can't break the no-verdict / no-judgment invariant.
- **Institutional scorecard** — maturity computed only from passing gates, honestly capped.

<details>
<summary><b>Verification battery</b> — the full local gate list</summary>

```bash
make repo-clean metadata lint typecheck test coverage schema ui-check \
     frontend-quality science-registry aos-kernel cognitive-control \
     neurocognitive-protocol product-readiness dynamic-probe openapi \
     api-smoke wheel-smoke security-static manifest-check
make institutional-verify     # base battery → 11-gate roadmap → capped scorecard
make mutation-check           # crown-jewel tests are defect-sensitive
# network / Docker gates:
make dependency-audit docker-build
```
</details>

<details>
<summary><b>API surface</b> — endpoints</summary>

- **COGVERITAS** — `POST /api/v1/cogveritas/verifiability` · `/case` · `/verify-integrity` · `GET /capabilities` · `/methodology`
- **Reports** — `POST /api/v1/reports/from-transcript` · `/from-upload` · `GET /api/v1/reports` · `/{id}` · `/{id}/markdown`
- **Ops** — `GET /health` · `/livez` · `/readyz` · `/metrics` · `/api/v1/system/{status,design-contract,interface-contract,science-registry,product-readiness}`

Contract: [`docs/openapi.json`](docs/openapi.json). `/api/v1/*` requires `api-version=2026-06-11`.
</details>

<details>
<summary><b>Repository map</b></summary>

- `src/bive/` — core package, CLI, API, storage, report model
- `src/bive/cogveritas/` — verifiability engine, language packs, integrity
- `src/bive/web/` — static operational console shipped in the wheel
- `research/cogveritas/validation/` — the real-data validation harness
- `schemas/` · `docs/` — JSON contracts and methodology
- `scripts/` · `tests/` — release / verification tooling and behaviour tests
- `.github/` — CI, PR and issue workflow
</details>

## The honest boundary

#### BIVE v0.4.0 — Behavioral Integrity Verification Engine

COGVERITAS is a research-to-product engineering repository for analysts, auditors,
investigators, journalists, OSINT and safety teams who need **structured evidence review**.
It is not an automated decision system; any decision affecting a person requires human review
and external corroboration.

Empirical basis: passive verbal deception detection is at chance on real high-stakes cases
(RLT AUC ≈ 0.56, CI straddling chance — [`docs/EMPIRICAL_VALIDATION.md`](docs/EMPIRICAL_VALIDATION.md)), so
the system stays an assistant, never a detector. `make product-readiness` deliberately keeps
the product **below GREEN** while dependency-CVE audit, Docker runtime, deployment smoke and
human-impact review remain external gates — an open-source product candidate, not yet a
deployed service.

<div align="center"><br/><sub>Apache-2.0 · <code>verdict = null · probability = suppressed</code> · built to make unsupported claims impossible</sub></div>
