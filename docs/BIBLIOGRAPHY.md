# Bibliography and Source Registry

## Scientific foundations

1. Vrij, A. et al. “Reading Lies: Nonverbal Communication and Deception.” Annual Review of Psychology. Core position: nonverbal cues to deception are faint/unreliable; behavioral lie catching is weak.
2. Bogaard, G. et al. “No evidence that instructions to ignore nonverbal cues improve deception detection accuracy.” Applied Cognitive Psychology. Core position: relying on nonverbal cues is not a reliable path to accuracy.
3. Pérez-Rosas, V. et al. “Deception Detection using Real-life Trial Data.” ICMI 2015. Introduces real-life trial video deception dataset and multimodal framing.
4. Ott, M., Choi, Y., Cardie, C., Hancock, J. “Finding Deceptive Opinion Spam by Any Stretch of the Imagination.” ACL 2011. Text deception dataset and computational linguistics baseline.
5. Zadeh, A. et al. “Multimodal Language Analysis in the Wild: CMU-MOSEI Dataset and Dynamic Fusion Graph.” ACL 2018. Multimodal language/emotion/sentiment fusion reference.
6. Ekman, P. / FACS literature. Use action units as behavior descriptors, not lie proof.

## Open-source tools

1. OpenFace: facial landmarks, head pose, gaze, facial Action Units.
2. OpenFace 3.0: lightweight multitask facial analysis research direction.
3. LibreFace: open-source facial behavior analysis / AU-oriented tooling.
4. MediaPipe: face, pose, and hand landmarks.
5. MMPose: pose estimation framework.
6. Whisper: multilingual ASR, speech translation, language ID.
7. pyannote.audio: speaker diarization toolkit.
8. openSMILE: acoustic feature extraction.
9. DVC: data/model versioning.
10. MLflow: ML lifecycle, experiment tracking, registry.
11. Evidently: ML/LLM evaluation, testing, monitoring.
12. W3C PROV: provenance data model and serializations.

## Dataset candidates

1. Real-Life Trial Deception Detection Dataset.
2. Bag-of-Lies.
3. Miami University Deception Detection Database / MU3D.
4. Deceptive Opinion Spam Corpus.
5. CMU-MOSEI / CMU-MOSI.
6. MELD / IEMOCAP for affective baselines, not deception proof.

## Bibliographic standard

Every dataset/tool added to production must record:

```yaml
name:
url:
license:
task:
modalities:
known_limitations:
allowed_use:
validation_status:
```


## Stage 7 bounded scientific and engineering registry

The following identifiers must stay synchronized with `src/bive/resources/science_registry.json` and are validated by `make bibliography`:

- `ekman_friesen_1969` — nonverbal leakage as bounded cue evidence, not deterministic deception proof.
- `vrij_2008` — deception detection limitations and human-review boundary.
- `newman_pennebaker_2003` — linguistic markers as weak task-bound evidence.
- `picard_1997` — affective computing as HCI/socio-technical framing, not mental-state certainty.
- `kahneman_tversky_1974` — judgment under uncertainty and bias-aware review prompts.
- `nist_ai_rmf_1_0` — AI risk governance and managed deployment posture.
- `nist_ssdf_800_218` — secure software development and release evidence.
- `owasp_api_top10_2023` — API auth, object access and resource-consumption control mapping.
- `wcag_2_2` — accessible operational interface target.
- `friston_2010` — predictive-processing metaphor for uncertainty and feedback, not neural inference.
- `fuster_2001` — temporal context and executive-control framing, not cognition reading.
- `gross_1998` — emotion regulation context over time, not emotion diagnosis.
- `cacioppo_handbook_2007` — physiological measurement discipline, baselines and confounds.
- `zadeh_mosei_2018` — multimodal fusion evaluation discipline, not deception proof.
- `perez_rosas_2015` — dataset-bound multimodal deception research, not production authority.
- `w3c_prov_2013` — provenance and artifact lineage.
- `pip_audit_2026` — Python dependency vulnerability audit automation.
- `openssf_scorecard` — open-source security posture automation.

## Engineering validation standard

A reference is valid only when it records `source_url`, operational mapping, and negative claim boundary. BIVE must never convert bibliographic authority into a runtime verdict. The registry licenses review questions, constraints, provenance and test design only.
