# Agent Protocols

## Linguistic Agent
Input: transcript segments.  
Output: claims, qualifiers, contradiction candidates, pressure-to-trust cues.  
Hard rule: no intent inference without evidence.

## Voice Agent
Input: audio file, diarization, ASR timestamps.  
Output: acoustic feature events: pitch, energy, pauses, jitter/shimmer, speaking-rate changes.  
Hard rule: acoustic stress is not deception.

## Vision/Kinesic Agent
Input: frames, face/pose/hand landmarks, action units.  
Output: movement and expression feature events.  
Hard rule: action units and gestures are hot spots, not verdicts.

## Context Agent
Input: documents, public records, timestamps, prior claims.  
Output: claim graph, timeline, external corroboration, source reliability.

## Fusion Agent
Input: evidence events.  
Output: calibrated hypotheses with uncertainty.

## Falsifier Agent
Input: hypothesis and evidence.  
Output: alternative explanations, counter-evidence, disconfirming questions.

## Red-Team Agent
Input: full report.  
Output: failure modes, overclaims, missing sources, adversarial manipulation risks.

## Report Agent
Input: full graph.  
Output: reviewable report.  
Hard rule: write “review required,” not “liar.”
