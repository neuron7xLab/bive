# Component Architecture

```text
Browser UI
  -> FastAPI API
    -> Pipeline
      -> Ingest
      -> Linguistic analyzer
      -> Evidence fusion
      -> Falsifier
      -> Question generator
    -> SQLite report store
    -> Markdown/JSON renderer
```

## Deterministic boundaries

- UI never interprets truth.
- API validates payloads.
- Pipeline creates reports from explicit segments.
- Fusion scores hypotheses from evidence events.
- Falsifier adds alternative explanations.
- Storage records immutable report JSON.
- PR gate prevents invariant drift.

## Extension points

- `adapters/whisper_adapter.py` for ASR.
- `adapters/openface_adapter.py` for facial/action-unit features.
- `adapters/opensmile_adapter.py` for acoustic features.
- Future `vision`, `audio`, `context` modules can emit the same EvidenceEvent contract.
