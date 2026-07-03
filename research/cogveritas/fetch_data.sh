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
