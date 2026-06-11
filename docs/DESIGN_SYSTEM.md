# BIVE Design System

## Purpose

BIVE uses an operational-console design language: the interface must make system state, evidence quality, gates, unknowns, and human-review boundaries visible before it makes anything decorative. Visual polish is allowed only when it improves orientation, confidence, hierarchy, and safe action.

## Design principles

1. Evidence before spectacle.
2. Status before action.
3. Unknown must be visible, not hidden.
4. Dynamic data must be rendered through safe DOM APIs, not raw HTML injection.
5. Keyboard operation and visible focus are release requirements.
6. The frontend is dependency-light by design: no build chain is required for the shipped console.

## Visual language

- Base mode: dark operational console.
- Primary accent: gold for system affordances and semantic headings.
- Secondary accent: blue for busy/unknown operational state.
- Success: green for ready/pass.
- Failure: red for fail/error.
- Typography: system UI stack for portability; monospace only for JSON/Markdown outputs.
- Layout: responsive evidence dashboard with hero, metrics, analysis console, report cards, operational contract, and raw machine output.

## Core tokens

- `--bg`: root background.
- `--panel`: glass operational panel.
- `--gold`: primary action/heading signal.
- `--good`: ready/pass state.
- `--bad`: fail/error state.
- `--busy`: in-progress/unknown state.
- `--muted`: secondary text.
- `--focus`: keyboard focus ring.

## Accessibility contract

The console targets WCAG 2.2 AA-oriented implementation practices:

- semantic sections and headings;
- visible skip link;
- explicit labels for inputs;
- `aria-live="polite"` status feedback;
- keyboard-operable buttons and links;
- visible focus states;
- responsive layout;
- reduced-motion media query;
- no essential information communicated by color alone.

## Security contract

Frontend dynamic report data must use `textContent` and DOM node creation. `innerHTML`, `outerHTML`, and `insertAdjacentHTML` are forbidden by `scripts/check_frontend_quality.py` because transcript-derived text is untrusted input. Apparently browsers still execute HTML when asked to execute HTML. Shocking, but here we are.

## Verification

Run:

```bash
make frontend-quality
make ui-check
make api-smoke
make wheel-smoke
```

Acceptance:

- frontend assets are present;
- packaged wheel contains UI assets;
- API serves the UI;
- no forbidden dynamic HTML tokens exist;
- core accessibility markers exist.
