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
        "h_conflicts": "Потенційні суперечності — перевірити вручну",
        "h_worklist": "Лист корроборації — що перевірити",
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
        "h_conflicts": "Потенциальные противоречия — проверить вручную",
        "h_worklist": "Лист корроборации — что проверить",
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
        "h_conflicts": "Potential inconsistencies — verify manually",
        "h_worklist": "Corroboration worklist — what to check",
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
    lines: list[str] = []

    lines.append(f"# {t['title']}")
    lines.append("")
    lines.append(t["no_verdict"])
    lines.append("")
    lines.append(f"**{t['gap']}:** {gap.get(output.verifiability_gap, output.verifiability_gap)} · "
                 f"**{t['claims']}:** {len(output.audit_trail)}")
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
        for item in output.corroboration_worklist:
            lines.append(f"- «{item.quote}»")
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
