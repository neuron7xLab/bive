# No-Verdict Invariant

COGVERITAS never emits a person-level judgment. This is structural, not advisory.

- `COGVERITASOutput.verdict` is typed `None` and validated to `None` at
  construction (`bive.cogveritas.output_contract`).
- Forbidden output strings (release blockers): `liar`, `truthful person`,
  `guilty`, `deceptive person`, `lie detected`, `truth detected`, `is lying`,
  `is truthful`, `person is deceptive`.
- Allowed framing only: `externally checkable markers elevated / nominal`,
  `insufficient data`, `corroboration required`, `uncertainty high`.
- Ordinal flags: `markers_elevated`, `markers_nominal`, `insufficient_data`.

Enforcement: `make no-verdict-check` scans emitted artifacts and asserts the
contract disables float probabilities and carries no forbidden string. Any
violation fails the build.
