# Product Manager Readiness

This repository uses product management as an execution discipline, not as packaging theater.

## Product evidence table

| Product question | Repo answer | Validator |
|---|---|---|
| What is the user job? | `jobs_to_be_done` in product model | `validate_product_operating_model.py` |
| What is the forbidden claim? | explicit non-claims + release policy | `test_product_model_preserves_hard_non_claims` |
| How does a user activate value? | activation path commands | product model validator |
| How do we know it is not production-ready yet? | scorecard UNKNOWN/HUMAN_REVIEW_REQUIRED dimensions | product readiness API test |
| Can the state be inspected at runtime? | `/api/v1/system/product-readiness` and `bive-aos product` | tests |

## Product decision rule

A product manager may publish the repository as an open-source candidate if:

- local gates pass;
- package artifacts exist;
- limitations are explicit;
- forbidden claims are present;
- external unknowns are not hidden.

A product manager must block production deployment if:

- CVE audit is unavailable;
- Docker runtime is untested;
- deployment smoke is missing;
- real person-impacting usage has no review policy.
