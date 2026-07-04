# Misuse and Human-Impact Threat Model

Implements the mandate's PR-5. Validated by `scripts/misuse_threat_model_check.py`
(`MISUSE_THREAT_MODEL_PASS`), which writes
`artifacts/verification/MISUSE_THREAT_MODEL_AUDIT.json`. Every risk below MUST carry
a **mitigation** and a **residual-risk** record, and every cited mitigation MUST map
to a mechanism that exists in the repository.

COGVERITAS analyses testimony. The dominant harm is human, not a software fault:
treating a structuring aid as a verdict. The design makes that structurally hard.

## Risk: misinterpretation

**Risk:** reading an "elevated verifiability gap" or "unverifiable" flag as a
statement that the person lied.
**Mitigation:** no-verdict invariant — `verdict` is structurally `null`
(`src/bive/cogveritas/output_contract.py`); the gap is ordinal, never a probability.
**Residual risk:** an operator may still misread ordinal flags; addressed by the
capability envelope and the dossier's explicit no-verdict header.

## Risk: over-reliance

**Risk:** substituting the tool's output for the human review it is meant to assist.
**Mitigation:** `human_in_the_loop` is declared in the capability envelope; every
finding is framed as a pointer, not a decision.
**Residual risk:** organisational pressure to automate; residual, not eliminable in code.

## Risk: false-authority

**Risk:** presenting the tool to a court or decision-maker as a validated lie
detector or a deception score.
**Mitigation:** `scripts/product_claim_audit.py` (release gate) blocks such claims on
every public surface; the empirical basis (RLT ≈ chance) is machine-discoverable via
the methodology endpoint.
**Residual risk:** verbal misrepresentation outside the product surfaces; unenforceable
in code, documented here.

## Risk: selective-evidence

**Risk:** citing only the flags that support a pre-formed conclusion.
**Mitigation:** the dossier reports the full claim set (checkable and unverifiable),
the timeline, and both corroboration and contradiction candidates; the integrity
fingerprint makes a truncated dossier detectable.
**Residual risk:** downstream selective quoting; residual.

## Risk: cross-language extraction error

**Risk:** mis-extraction on Ukrainian/Russian inflection or code-switching leading to
wrong anchors.
**Mitigation:** deterministic language packs with declared limits; provenance nodes
expose the exact extracted entities for human check.
**Residual risk:** proxy NER over-captures (documented as an honest limitation).

## Risk: record-routing misuse

**Risk:** treating the corroboration worklist's suggested record type as an
instruction to obtain records unlawfully.
**Mitigation:** the worklist suggests *where evidence would live*, not an authority to
obtain it; no verdict is attached.
**Residual risk:** lawful-access decisions are outside the tool; residual.

## Risk: dossier misuse

**Risk:** altering an exported dossier and presenting it as the original analysis.
**Mitigation:** deterministic chain-of-custody fingerprint (`src/bive/cogveritas/
integrity.py`, `/verify-integrity`); any change alters the hash.
**Residual risk:** a fabricated dossier with no fingerprint; detectable by absence.

## Risk: interview-question misuse

**Risk:** using generated interview questions to pressure or entrap.
**Mitigation:** questions are elicit-only (Verifiability Approach), never accusatory
(`src/bive/cogveritas/interview.py`).
**Residual risk:** tone of delivery is human; residual.

## Risk: privacy and sensitive-data

**Risk:** processing sensitive testimony without handling controls.
**Mitigation:** text-only, local processing; no external calls in the core; the
integrity artifact records provenance without leaking content.
**Residual risk:** operator data-handling outside the tool; residual.

## Risk: institutional escalation

**Risk:** the tool's output triggering escalation disproportionate to its (chance-
level, high-stakes) evidence.
**Mitigation:** the domain-distance policy and the institutional scorecard's honesty
cap keep maturity claims below benchmark-grade; the methodology contract states the
empirical limits.
**Residual risk:** policy decisions are institutional; residual, acknowledged.
