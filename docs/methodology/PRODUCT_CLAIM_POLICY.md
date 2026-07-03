# Product Claim Policy

Implements PR-4 / §12 of the COGVERITAS Institutional Level-Up Specification.

> A higher score is not earned by adding features.
> A higher score is earned by making unsupported claims impossible.

The Product Claim Audit (`scripts/product_claim_audit.py`, gate `product-claim-audit`)
scans every public surface and **fails the release** if the product language asserts
a capability the evidence boundary does not support. It runs in the release battery,
so an overclaim cannot ship.

## Surfaces governed

README, `docs/**`, OpenAPI (`docs/openapi.json`), frontend copy
(`src/bive/web/**`), CLI help (`src/bive/cli.py`), and the capability / methodology /
dossier text.

## What is blocked (asserted, un-disclaimed)

| Category | Example that FAILS |
|---|---|
| Automatic person-status inference | "is a lie detector", "detects deception", "identifies liars" |
| Unsupported probability language | "deception probability", "truth score" |
| Unqualified reliability/accuracy | "highly reliable", "98% accurate" (no citation) |
| Guarantees | "guarantees", "proven to detect" |
| Truth detection | "truth detection" |

## What is allowed (and required)

A **disclaimed** mention is not a claim — surfacing the limit is the whole point:

- negated on the line or a nearby list header: "**not** a lie detector", "does **not**
  detect deception", "**не** детектор брехні", under "BIVE is **not**:";
- the no-verdict framing: "no verdict", "verdict: null", "за задумом";
- a **scholarly citation** with a year: "Bond & DePaulo 2006 (54% accuracy)".

## Rationale

The system's credibility rests on its evidence boundary being *stricter* than its
product language. This gate makes that structural: the boundary is enforced in CI,
not left to editorial vigilance. See `docs/EMPIRICAL_VALIDATION.md` for the evidence
that bounds every capability claim, and `NO_VERDICT_INVARIANT.md` for the person-level
invariant enforced separately in the output contract.
