# Security Policy

## Supported version

| Version | Status |
| --- | --- |
| 0.4.x | active research/product hardening |

## Reporting

Use **GitHub Private Vulnerability Reporting** (the *Report a vulnerability* button under
the repository **Security** tab) for coordinated, private disclosure. Do not open public
issues for security defects. Include:

- affected version or commit;
- reproduction steps;
- expected impact;
- logs, payloads or proof-of-concept when safe to share.

## Security boundaries

- BIVE is not a lie detector and must not be deployed as an automated decision system against people.
- Production/staging API mode requires `BIVE_API_TOKEN`.
- Public deployments must place BIVE behind TLS, authentication, request-size limits and operational logging.
- Optional media adapters call external tools and must be treated as untrusted subprocess boundaries.
- Dependency vulnerability state is release-blocking unless a documented waiver exists.

## Release security gates

```bash
make security-static
make dependency-audit
make verify-release
```

If dependency audit cannot reach the advisory service, release status is `UNKNOWN_SECURITY_STATE`, not `PASS`.

## Automated supply-chain controls

- **CodeQL** (`security-extended`, `security-and-quality`) on every PR, push to `main` and weekly schedule.
- **Dependency Review** blocks PRs that introduce high-severity or copyleft-incompatible dependencies.
- **OpenSSF Scorecard** publishes a public supply-chain posture score.
- **GitHub Actions are pinned to full commit SHAs**; updates flow through Dependabot.
- **Hardened runners** (`step-security/harden-runner`, egress audit) on all jobs.
- **SLSA build provenance attestation** + **CycloneDX SBOM** are produced for every tagged release.
- **PyPI publishing uses OIDC Trusted Publishing** — no long-lived API tokens.
