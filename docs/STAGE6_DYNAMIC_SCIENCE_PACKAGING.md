# Stage 6 Dynamic Science Packaging Summary

## Added

- Packaged bounded science registry under `src/bive/resources/science_registry.json`.
- Review mirror under `data/science/science_registry.json`.
- Dynamic scenario registry under `data/operations/dynamic_scenarios.json`.
- API endpoints for science registry summary and full registry.
- Frontend science registry panel and hard-boundary panel.
- `make science-registry` validation gate.
- `make dynamic-probe` runtime probe gate.
- Tests for registry validity, science API contract and dynamic runtime behavior.
- Docs for dynamic environment behavior and scientific foundation mapping.

## Verified behavior expected

- repeated runs keep normalized structural hash stable;
- report IDs remain unique in normal runtime;
- malformed input is rejected;
- oversized payload is rejected;
- production mode fails closed without token;
- concurrent SQLite writes complete without lock failure;
- science registry has enough references, claim boundaries and linked disciplines.

## Explicit non-claims

- not a lie detector;
- not a clinical diagnostic system;
- not a legal decision engine;
- not validated for person-level truth, intent or guilt inference.
