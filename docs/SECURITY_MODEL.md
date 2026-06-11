# Security Model

## Protected assets

- transcript payloads;
- generated verification reports;
- audit logs;
- API token;
- local SQLite storage;
- optional external adapter outputs.

## Trust boundaries

- CLI input files are untrusted.
- API request bodies are untrusted.
- optional media adapters and external executables are untrusted subprocess boundaries.
- generated reports are machine-assisted evidence artifacts, not final judgments.

## Current controls

- production/staging API auth via bearer token or `X-BIVE-API-Key`;
- request body size limit;
- segment count and text length limits;
- schema validation;
- controlled CLI failure contract;
- static security scan gate;
- human-review invariant.

## Required deployment controls outside the app

- TLS termination;
- secret manager or protected environment variables;
- network allowlist if internal;
- log retention policy;
- backup and retention policy for SQLite data;
- dependency vulnerability audit before release.
