"""Rebuild the char-3-gram language-ID model at src/bive/cogveritas/lid_model.json.

Reproducible recipe (Tatoeba per-language sentence exports, CC BY 2.0 FR):

    for l in ukr rus eng; do
      curl -sL "https://downloads.tatoeba.org/exports/per_language/$l/${l}_sentences.tsv.bz2" \
        -o "$l.tsv.bz2" && bunzip2 -kf "$l.tsv.bz2"
    done
    PYTHONPATH=src python research/cogveritas/validation/build_lid_model.py <dumps_dir>

Each dump row is ``id \t lang \t text``. The first N sentences per language (by file
order = id-sorted) are used, EXCLUDING every sentence in lang_corpus.json /
lang_heldout.json so the model never sees the validation data (no leakage). The
profile is a naive-Bayes char-3-gram count table — pure counts, so the build is
deterministic and the model is dependency-free at runtime.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "src" / "bive" / "cogveritas" / "lid_model.json"
N_PER_LANG = 20000
TOP_K = 5000
_CODES = {"uk": "ukr", "ru": "rus", "en": "eng"}


def _clean(text: str) -> str:
    out: list[str] = []
    prev_space = False
    for ch in text.lower():
        if ch.isalpha():
            out.append(ch)
            prev_space = False
        elif not prev_space:
            out.append(" ")
            prev_space = True
    return " " + "".join(out).strip() + " "


def _grams(text: str, n: int = 3) -> list[str]:
    s = _clean(text)
    return [s[i : i + n] for i in range(len(s) - n + 1)] if len(s) >= n else []


def _exclusions() -> set[str]:
    excl: set[str] = set()
    for name in ("lang_corpus", "lang_heldout"):
        data = json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
        excl |= {r["text"] for r in data["sentences"]}
    return excl


def build(dumps_dir: Path) -> dict[str, object]:
    excl = _exclusions()
    profiles: dict[str, dict[str, int]] = {}
    totals: dict[str, int] = {}
    for lang, code in _CODES.items():
        counter: Counter[str] = Counter()
        taken = 0
        for line in (dumps_dir / f"{code}.tsv").read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            text = parts[2].strip()
            if not text or text in excl or len(text) < 6 or len(text) > 200:
                continue
            counter.update(_grams(text))
            taken += 1
            if taken >= N_PER_LANG:
                break
        top = dict(counter.most_common(TOP_K))
        profiles[lang] = top
        totals[lang] = sum(top.values())
        print(f"{lang}: trained on {taken} sentences, kept {len(top)} grams")
    vocab = {g for prof in profiles.values() for g in prof}
    return {
        "n": 3,
        "langs": ["uk", "ru", "en"],
        "vocab_size": len(vocab),
        "totals": totals,
        "profiles": profiles,
        "provenance": "Tatoeba per-language exports (CC BY 2.0 FR); disjoint from validation corpora",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: build_lid_model.py <dumps_dir>", file=sys.stderr)
        return 2
    model = build(Path(sys.argv[1]))
    OUT.write_text(json.dumps(model, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
