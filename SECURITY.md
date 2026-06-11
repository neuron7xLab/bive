# Security Policy

## Supported version

| Version | Status |
| --- | --- |
| 0.4.x | active research/product hardening |

## Reporting

Report vulnerabilities privately to the maintainer before public disclosure. Include:

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
