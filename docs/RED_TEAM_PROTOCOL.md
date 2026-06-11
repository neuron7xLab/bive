# Red-Team Protocol v0.4.0

The red-team layer exists to find where BIVE cracks into pseudoscience.

## Built-in cases

1. `stress_not_deception`  
   Stressed language must not become an accusation.

2. `verification_pressure`  
   Discouraging verification should trigger review, not a verdict.

3. `local_tension`  
   Direct local contradiction should trigger review.

## Command

```bash
python -m bive.cli red-team
```

Expected: every case passes.

## Acceptance rule

A PR fails if any red-team case fails. The system may be incomplete. It may not pretend certainty.
