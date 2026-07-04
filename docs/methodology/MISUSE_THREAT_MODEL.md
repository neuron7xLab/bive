# Misuse and Human-Impact Threat Model

Implements PR-5 / §13 of the COGVERITAS Institutional Level-Up Specification.
Validated by `scripts/misuse_threat_model_check.py` (`MISUSE_THREAT_MODEL_PASS`):
each scenario below MUST name a safeguard, and each safeguard MUST map to a
mechanism that actually exists in the repository.

COGVERITAS analyses testimony. The dominant harm is not a software fault but a
*human* one: treating a structuring aid as a verdict about a person. The design
makes that structurally hard; this model states how.

## Scenario: guilt-by-gap

**Misuse:** an operator reads an "elevated verifiability gap" or an "unverifiable"
flag as evidence that the person lied or is guilty.
**Safeguard:** the no-verdict invariant — `verdict` is structurally `null`
(`src/bive/cogveritas/output_contract.py`); the gap is ordinal, never a probability.
**Mechanism:** output contract validator + `cogveritas_gates.py no-verdict`.

## Scenario: coercive interviewing

**Misuse:** using the output to justify pressure or accusation in an interrogation.
**Safeguard:** interview questions are elicit-only (Verifiability Approach), never
accusatory; human-in-the-loop is declared; the capability envelope lists hard limits.
**Mechanism:** `src/bive/cogveritas/interview.py` + `capabilities.py` (`human_in_the_loop`).

## Scenario: lie-detector overclaim

**Misuse:** presenting the tool to a court or decision-maker as a validated lie
detector or a deception score.
**Safeguard:** the product may not overclaim; the empirical basis (RLT AUC ≈ 0.56,
CI straddles chance) is machine-discoverable.
**Mechanism:** `scripts/product_claim_audit.py` (release gate) + `methodology.py`.

## Scenario: out-of-domain application

**Misuse:** applying in-domain metrics to a domain the system was never tested on.
**Safeguard:** metrics are regime-labelled; in-domain numbers cannot masquerade as
general capability.
**Mechanism:** `scripts/domain_distance_check.py` (release gate).

## Scenario: surveillance overreach

**Misuse:** mass, automated processing that removes the human reviewer.
**Safeguard:** text-only (no audio/video/physiological inference), human-in-the-loop;
every finding is a pointer for a human, not an automated decision.
**Mechanism:** `capabilities.py` hard limits + no-verdict invariant.

## Scenario: evidence tampering

**Misuse:** altering a dossier and passing it off as the original analysis.
**Safeguard:** a deterministic, reproducible chain-of-custody fingerprint; any change
alters the hash.
**Mechanism:** `src/bive/cogveritas/integrity.py` + `/verify-integrity`.
