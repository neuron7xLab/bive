# Dataset Access Notes

Raw datasets are **not committed** (licensing + size). We commit manifests,
loaders, checksums and reproduction instructions. Fetch with
`research/cogveritas/fetch_data.sh`.

- **Op-Spam** (Ott et al.) — public; loaded via a consolidated CSV mirror;
  grouped by hotel (canonical 20×20 block order) for subject-independent CV.
- **Real-Life Trial** (Pérez-Rosas 2015) — high-stakes courtroom transcripts;
  used as the second real dataset. Grouped per clip (true speaker map not
  distributed; stated limitation).
- **MU3D** — requires registration and is not obtainable non-interactively; its
  manifest is marked `unavailable`. The Real-Life Trial corpus substitutes for
  it (a stronger, high-stakes choice). See `DECISION_PHASE0_DATASET_DIVERGENCE.md`.
