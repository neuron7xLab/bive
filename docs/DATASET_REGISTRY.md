# Dataset Registry

## Tier 1: deception-specific candidates

| Dataset | Modalities | Use | Warning |
|---|---:|---|---|
| Real-Life Trial | video/audio/transcript | multimodal deception research baseline | courtroom/public-trial bias; not universal |
| Bag-of-Lies | video/audio/text | benchmark deception competition candidate | controlled/game setting |
| MU3D | multimodal | benchmark candidate | verify access/license |
| Deceptive Opinion Spam | text | linguistic deception baseline | hotel-review domain only |

## Tier 2: multimodal affect/language support

| Dataset | Modalities | Use | Warning |
|---|---:|---|---|
| CMU-MOSEI | text/audio/video | multimodal fusion pretraining/eval | emotion/sentiment, not deception |
| CMU-MOSI | text/audio/video | multimodal fusion smoke tests | small, sentiment-focused |
| IEMOCAP | audio/video/text | emotion/acoustic baselines | acted emotion |
| MELD | multimodal dialogue | dialogue emotion context | TV/scripted domain |

## Dataset admission gate

A dataset is not admitted until it has:

- license recorded;
- source URL recorded;
- task definition recorded;
- label provenance recorded;
- known limitations recorded;
- train/test split policy recorded;
- leakage audit recorded;
- domain-shift warning recorded.
