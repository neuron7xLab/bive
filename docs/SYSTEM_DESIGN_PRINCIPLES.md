# System Design Principles

## Secure software baseline

The repository follows a fail-closed release model: build, lint, typecheck, test, schema, OpenAPI, wheel smoke, API smoke, static security and manifest gates must pass before release. Dependency CVE audit and Docker runtime verification are required when network and Docker are available.

## API security baseline

API design treats authentication, object access, unrestricted resource consumption and security misconfiguration as production blockers. Local demo mode may run without auth; staging and production require an API token.

## Accessibility baseline

The UI targets WCAG 2.2 AA-oriented implementation practices: perceivable content, operable controls, understandable error/status feedback and robust semantic structure.

## Product-management baseline

Every visible capability must map to one of four states:

1. implemented and machine-verified;
2. implemented but externally gated;
3. planned but not implemented;
4. explicitly out of scope.

No marketing claim may bypass that state model.
