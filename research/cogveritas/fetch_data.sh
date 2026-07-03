#!/usr/bin/env bash
# Fetch the public labeled corpora used by the empirical validation.
# Datasets are NOT committed (licensing + size); this reproduces them locally.
set -euo pipefail
mkdir -p data
curl -sSL -o data/opspam.csv \
  "https://raw.githubusercontent.com/PauDK/Deceptive-Review-Detection/main/Chicago_Hotel_Review/Chicago_Hotel_Reviews.csv"
for f in train validation test; do
  curl -sSL -o "data/diplomacy_${f}.jsonl" \
    "https://raw.githubusercontent.com/DenisPeskoff/2020_acl_diplomacy/master/data/${f}.jsonl"
done
echo "fetched: $(wc -l < data/opspam.csv) opspam rows"

# Real-Life Trial transcripts (high-stakes courtroom deception, 61 lie / 60 truth)
RLT="https://raw.githubusercontent.com/ritikamotwani/Deception-Detection/master/RealLife/Real_Life_Trial_Data"
mkdir -p data/rlt/Deceptive data/rlt/Truthful
for i in $(seq -w 1 61); do curl -sSL -o "data/rlt/Deceptive/trial_lie_0${i}.txt" "$RLT/Deceptive/trial_lie_0${i}.txt" 2>/dev/null || true; done
for i in $(seq -w 1 60); do curl -sSL -o "data/rlt/Truthful/trial_truth_0${i}.txt" "$RLT/Truthful/trial_truth_0${i}.txt" 2>/dev/null || true; done
echo "fetched RLT: $(ls data/rlt/Deceptive | wc -l) lie / $(ls data/rlt/Truthful | wc -l) truth"
