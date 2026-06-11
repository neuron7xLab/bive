# Operational Excellence Model

The operational model is stored in `data/operations/service_slo.json` and validated by `make operational-excellence`.

It defines:

- reliability, security, operational excellence, performance efficiency and cost optimization pillars;
- service-level objectives for API smoke, release integrity, explicit security unknowns and performance evidence;
- release rings: `local`, `candidate`, `public_github`;
- rollback triggers and actions;
- observability contract: `x-ms-request-id`, `x-ms-client-request-id`, `/livez`, `/readyz`, `/metrics`, Microsoft-style error envelope.

Release gate:

```bash
make operational-excellence
```
