"""Analyst dossier — render a COGVERITAS review as a printable Markdown report.

The artifact a reviewer keeps: timeline, flagged inconsistencies, the corroboration
worklist (which record to pull), open questions, unverifiable assertions, a
provenance table, and a limits footer. Every section is drawn from the structured
output; nothing new is inferred here. The header states plainly that there is no
verdict — the dossier is a research aid, not a judgment.
"""

from __future__ import annotations

from .output_contract import COGVERITASOutput

_GAP_LABEL: dict[str, dict[str, str]] = {
    "uk": {"elevated": "підвищений", "nominal": "номінальний", "insufficient": "недостатньо даних"},
    "ru": {"elevated": "повышенный", "nominal": "номинальный", "insufficient": "недостаточно данных"},
    "en": {"elevated": "elevated", "nominal": "nominal", "insufficient": "insufficient data"},
}

_CONFLICT_LABEL: dict[str, dict[str, str]] = {
    "uk": {"negation_polarity": "протилежні твердження", "figure_mismatch": "розбіжність у числах"},
    "ru": {"negation_polarity": "противоположные утверждения", "figure_mismatch": "расхождение в числах"},
    "en": {"negation_polarity": "opposite statements", "figure_mismatch": "figure mismatch"},
}

_STATUS_LABEL: dict[str, dict[str, str]] = {
    "uk": {"pending": "очікує", "confirmed": "підтверджено", "refuted": "спростовано"},
    "ru": {"pending": "ожидает", "confirmed": "подтверждено", "refuted": "опровергнуто"},
    "en": {"pending": "pending", "confirmed": "confirmed", "refuted": "refuted"},
}

_CROSS_LABEL: dict[str, dict[str, str]] = {
    "uk": {"cross_contradiction": "суперечність між свідками", "cross_corroboration": "взаємне підтвердження"},
    "ru": {"cross_contradiction": "противоречие между свидетелями", "cross_corroboration": "взаимное подтверждение"},
    "en": {"cross_contradiction": "cross-witness contradiction", "cross_corroboration": "mutual corroboration"},
}

# All section headings and fixed prose, per language.
_T: dict[str, dict[str, str]] = {
    "uk": {
        "title": "Досьє перевірюваності — COGVERITAS",
        "no_verdict": (
            "**Вирок: відсутній (за задумом).** Це не детектор брехні. Система структурує "
            "твердження, будує хронологію, позначає розбіжності та маршрутизує до зовнішніх "
            "записів для перевірки людиною."
        ),
        "gap": "Розрив перевірюваності",
        "claims": "тверджень",
        "h_timeline": "Хронологія",
        "h_entities": "Сутності справи",
        "h_witnesses": "Свідки",
        "h_cross": "Крос-звірка показів свідків",
        "h_conflicts": "Потенційні суперечності — перевірити вручну",
        "h_worklist": "Лист корроборації — що перевірити",
        "progress": "Прогрес перевірки",
        "h_questions": "Питання для корроборації",
        "h_unverifiable": "Неперевірювані твердження",
        "h_provenance": "Провенанс",
        "p_claim": "Твердження",
        "p_check": "Перевірюваність",
        "p_entities": "Сутності",
        "h_limits": "Межі та наукова основа",
        "approx": " (приблизно)",
        "limit_1": (
            "Пасивна текстова детекція брехні не працює на реальній high-stakes брехні "
            "(Real-Life Trial: AUC 0.56, довірчий інтервал перекриває випадковість)."
        ),
        "limit_2": "Жодних ймовірностей поза доменом; вирок про людину не виноситься.",
        "source": "Джерело",
    },
    "ru": {
        "title": "Досье проверяемости — COGVERITAS",
        "no_verdict": (
            "**Вердикт: отсутствует (по замыслу).** Это не детектор лжи. Система структурирует "
            "утверждения, строит хронологию, отмечает расхождения и маршрутизирует к внешним "
            "записям для проверки человеком."
        ),
        "gap": "Разрыв проверяемости",
        "claims": "утверждений",
        "h_timeline": "Хронология",
        "h_entities": "Сущности дела",
        "h_witnesses": "Свидетели",
        "h_cross": "Кросс-сверка показаний свидетелей",
        "h_conflicts": "Потенциальные противоречия — проверить вручную",
        "h_worklist": "Лист корроборации — что проверить",
        "progress": "Прогресс проверки",
        "h_questions": "Вопросы для корроборации",
        "h_unverifiable": "Непроверяемые утверждения",
        "h_provenance": "Провенанс",
        "p_claim": "Утверждение",
        "p_check": "Проверяемость",
        "p_entities": "Сущности",
        "h_limits": "Границы и научная основа",
        "approx": " (приблизительно)",
        "limit_1": (
            "Пассивная текстовая детекция лжи не работает на реальной high-stakes лжи "
            "(Real-Life Trial: AUC 0.56, доверительный интервал перекрывает случайность)."
        ),
        "limit_2": "Никаких вероятностей вне домена; вердикт о человеке не выносится.",
        "source": "Источник",
    },
    "en": {
        "title": "Verifiability dossier — COGVERITAS",
        "no_verdict": (
            "**Verdict: none (by design).** This is not a lie detector. The system structures "
            "claims, builds a timeline, flags disagreements, and routes to external records for "
            "human review."
        ),
        "gap": "Verifiability gap",
        "claims": "claims",
        "h_timeline": "Timeline",
        "h_entities": "Case entities",
        "h_witnesses": "Witnesses",
        "h_cross": "Cross-witness comparison",
        "h_conflicts": "Potential inconsistencies — verify manually",
        "h_worklist": "Corroboration worklist — what to check",
        "progress": "Verification progress",
        "h_questions": "Corroboration questions",
        "h_unverifiable": "Unverifiable assertions",
        "h_provenance": "Provenance",
        "p_claim": "Claim",
        "p_check": "Verifiability",
        "p_entities": "Entities",
        "h_limits": "Limits and empirical basis",
        "approx": " (approximate)",
        "limit_1": (
            "Passive verbal deception detection does not work on real high-stakes deception "
            "(Real-Life Trial: AUC 0.56, confidence interval straddles chance)."
        ),
        "limit_2": "No probabilities out of domain; no person-level verdict is produced.",
        "source": "Source",
    },
}

_PROVENANCE = "docs/EMPIRICAL_VALIDATION.md"


def to_dossier_markdown(output: COGVERITASOutput, lang: str = "uk") -> str:
    """Render the structured output as a printable analyst dossier in ``lang``."""
    t = _T.get(lang, _T["en"])
    gap = _GAP_LABEL.get(lang, _GAP_LABEL["en"])
    conflict_label = _CONFLICT_LABEL.get(lang, _CONFLICT_LABEL["en"])
    cross_label = _CROSS_LABEL.get(lang, _CROSS_LABEL["en"])
    lines: list[str] = []

    lines.append(f"# {t['title']}")
    lines.append("")
    lines.append(t["no_verdict"])
    lines.append("")
    lines.append(f"**{t['gap']}:** {gap.get(output.verifiability_gap, output.verifiability_gap)} · "
                 f"**{t['claims']}:** {len(output.audit_trail)}")
    lines.append("")

    if output.entities:
        lines.append(f"## {t['h_entities']}")
        for e in output.entities:
            forms = ", ".join(f for f in e.forms if f != e.canonical)
            suffix = f" ({forms})" if forms else ""
            lines.append(f"- **{e.canonical}** — ×{e.count}{suffix}")
        lines.append("")

    if output.witnesses:
        lines.append(f"**{t['h_witnesses']}:** {', '.join(output.witnesses)}")
        lines.append("")

    if output.cross_witness:
        lines.append(f"## {t['h_cross']}")
        for x in output.cross_witness:
            label = cross_label.get(x.type, x.type)
            who = " / ".join(x.speakers)
            lines.append(f"- _{label}_ — {who}")
            for q in x.quotes:
                lines.append(f"  - «{q}»")
        lines.append("")

    if output.timeline:
        lines.append(f"## {t['h_timeline']}")
        for i, entry in enumerate(output.timeline, 1):
            approx = "" if entry.resolved else t["approx"]
            when = entry.time_label or "—"
            lines.append(f"{i}. **[{when}{approx}]** «{entry.quote}»")
        lines.append("")

    if output.conflicts:
        lines.append(f"## {t['h_conflicts']}")
        for c in output.conflicts:
            label = conflict_label.get(c.type, c.type)
            lines.append(f"- _{label}_")
            for q in c.quotes:
                lines.append(f"  - «{q}»")
        lines.append("")

    if output.corroboration_worklist:
        lines.append(f"## {t['h_worklist']}")
        p = output.verification_progress
        status_label = _STATUS_LABEL.get(lang, _STATUS_LABEL["en"])
        lines.append(
            f"_{t['progress']}: {status_label['confirmed']} {p.confirmed} · "
            f"{status_label['refuted']} {p.refuted} · {status_label['pending']} {p.pending} "
            f"/ {p.total}_"
        )
        for item in output.corroboration_worklist:
            mark = "✓" if item.status == "confirmed" else "✗" if item.status == "refuted" else "•"
            tail = f" — {item.note}" if item.note else ""
            lines.append(f"- [{mark}] «{item.quote}» _({status_label.get(item.status, item.status)}{tail})_")
            for r in item.record_types:
                lines.append(f"  - → {r}")
        lines.append("")

    if output.corroboration_questions:
        lines.append(f"## {t['h_questions']}")
        for q in output.corroboration_questions:
            lines.append(f"- {q}")
        lines.append("")

    if output.rm_criteria_flagged:
        lines.append(f"## {t['h_unverifiable']}")
        for note in output.rm_criteria_flagged:
            lines.append(f"- {note}")
        lines.append("")

    lines.append(f"## {t['h_provenance']}")
    lines.append(f"| {t['p_claim']} | {t['p_check']} | {t['p_entities']} |")
    lines.append("| --- | --- | --- |")
    for node in output.audit_trail:
        # Wrap the quote as evidence (« ») with inner guillemets neutralised, so the
        # no-verdict scan treats it as user content, not the system's framing.
        quote = node.text.replace("«", '"').replace("»", '"').replace("|", "\\|")
        entities = ", ".join(node.entities[:6]).replace("|", "\\|")
        lines.append(f"| «{quote}» | {node.verifiability} | {entities} |")
    lines.append("")

    lines.append(f"## {t['h_limits']}")
    lines.append(f"- {t['limit_1']} {t['source']}: `{_PROVENANCE}`.")
    lines.append(f"- {t['limit_2']}")
    lines.append("")

    return "\n".join(lines)
