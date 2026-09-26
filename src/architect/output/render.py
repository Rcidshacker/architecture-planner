"""Architecture brief, diagram data, and coding-agent prompt, all rendered from one ResolvedPlan.

Nothing here decides architecture: every component, provider, and state printed is read from the plan.
"""

import json
from typing import Any

from architect.requirements import RequirementState
from architect.requirements.fields import FIELD_PATHS, get_value
from architect.resolution import ResolvedPlan
from architect.rules import ComponentRequirement, ComponentStatus


def _built(plan: ResolvedPlan) -> list[ComponentRequirement]:
    """Components that appear in the diagram and prompt: everything except NOT_REQUIRED."""
    return [c for c in plan.architecture.components if c.status is not ComponentStatus.NOT_REQUIRED]


def _name(plan: ResolvedPlan) -> str:
    name = plan.requirements.application.name.value
    return str(name) if name is not None else "(unnamed application)"


def diagram_data(plan: ResolvedPlan) -> dict[str, Any]:
    """Nodes/edges for the architecture diagram. Provider options are node attributes, not new nodes."""
    nodes: list[dict[str, Any]] = [{"id": "application", "label": _name(plan), "kind": "application"}]
    edges = []
    for c in _built(plan):
        providers = sorted(
            {cfg.covers[c.component] for cfg in plan.architecture.provider_candidates if c.component in cfg.covers}
        )
        nodes.append(
            {
                "id": c.component,
                "label": c.component,
                "kind": "component",
                "status": str(c.status),
                "spec": c.spec,
                "provider_options": providers,
            }
        )
        edges.append({"from": "application", "to": c.component, "status": str(c.status)})
    return {"nodes": nodes, "edges": edges}


def _label(text: str) -> str:
    """Escape text for a quoted Mermaid label."""
    return text.replace('"', "#quot;")


def _mermaid(data: dict[str, Any]) -> str:
    lines = ["flowchart LR", f'  application["{_label(data["nodes"][0]["label"])}"]']
    for node in data["nodes"][1:]:
        options = ", ".join(node["provider_options"]) or "no verified provider"
        lines.append(f'  {node["id"]}["{_label(node["id"])} ({node["status"]})<br/>{_label(options)}"]')
    for edge in data["edges"]:
        arrow = "-.->" if edge["status"] == "UNDETERMINED" else "-->"
        lines.append(f"  {edge['from']} {arrow} {edge['to']}")
    return "\n".join(lines)


def _requirement_lines(plan: ResolvedPlan, state: RequirementState) -> list[str]:
    lines = []
    for path in FIELD_PATHS:
        rv = get_value(plan.requirements, path)
        if rv.state is state:
            quote = f' — "{rv.source_text}"' if rv.source_text else ""
            lines.append(f"- `{path}` = {json.dumps(rv.value, ensure_ascii=False)} ({rv.provenance}){quote}")
    return lines or ["- none"]


def architecture_brief(plan: ResolvedPlan) -> str:
    arch, f = plan.architecture, plan.architecture.feasibility
    out = [
        f"# Architecture Brief: {_name(plan)}",
        "",
        "## Application summary",
        "",
        plan.requirements.application.description,
        "",
    ]
    out += ["## Confirmed requirements (stated by the user)", "", *_requirement_lines(plan, RequirementState.KNOWN), ""]
    out += [
        "## Assumptions and provenance (INFERRED — not verified)",
        "",
        *_requirement_lines(plan, RequirementState.INFERRED),
        "",
    ]

    out += [
        "## Abstract architecture",
        "",
        "| Component | Status | Spec | Provenance | Rules |",
        "|---|---|---|---|---|",
    ]
    for c in arch.components:
        spec = ", ".join(f"{k}={v}" for k, v in c.spec.items()) or "—"
        out.append(
            f"| {c.component} | {c.status} | {spec} | {', '.join(c.provenance)} | {', '.join(c.rules_triggered)} |"
        )

    out += ["", "## Provider options (from seeded, sourced facts; the tool does not pick one)", ""]
    if not arch.provider_candidates:
        out.append("- none: no configuration of seeded providers covers the REQUIRED components")
    for cfg in arch.provider_candidates:
        cost = f"{cfg.fixed_monthly} {cfg.currency}/month fixed" if cfg.fixed_monthly is not None else "cost unverified"
        out.append(
            f"- {' + '.join(cfg.bundles)}: provider {cfg.provider_state}, budget {cfg.budget_state} "
            f"({cost}; {'; '.join(cfg.explanations)})"
        )
    out.append("- Compatibility between providers: DEFERRED (not verified in V1)")

    out += [
        "",
        "## Feasibility",
        "",
        f"- architecture: {f.architecture}",
        f"- provider: {f.provider}",
        f"- budget: {f.budget}",
        f"- compatibility: {f.compatibility}",
    ]
    out += [f"- CONFLICT: {c}" for c in f.conflicts]
    out += [f"- {e}" for e in f.explanations]
    if f.missing_evidence:
        out += ["", "Missing evidence:", *[f"- {m}" for m in f.missing_evidence]]

    out += ["", "## Unresolved / UNDETERMINED decisions", "", *[f"- {u}" for u in arch.unresolved_items]]
    if plan.clarification_stop:
        out.append(f"- clarification stopped after {plan.clarification_rounds} round(s): {plan.clarification_stop}")
    out += [
        "",
        "## Scaling triggers",
        "",
        *([f"- {s}" for s in arch.scaling_triggers] or ["- none: no documented scaling rule exists in V1"]),
    ]
    out += [
        "",
        "## Items deliberately avoided",
        "",
        *(
            [f"- {a}: NOT_REQUIRED (default-avoid rule; no requirement justifies it)" for a in arch.avoided_items]
            or ["- none"]
        ),
    ]
    out += ["", "## Major decisions", ""]
    out += [
        f"- **{d.subject}** → {d.outcome} [{', '.join(d.provenance)}; {', '.join(d.references)}]: {d.explanation}"
        for d in arch.decisions
    ]
    out += ["", "## Architecture diagram", "", "```mermaid", _mermaid(diagram_data(plan)), "```"]
    out += ["", "## Implementation instructions for your coding agent", "", agent_prompt(plan)]
    return "\n".join(out) + "\n"


def agent_prompt(plan: ResolvedPlan) -> str:
    arch, f = plan.architecture, plan.architecture.feasibility
    lines = [f"You are implementing {_name(plan)}: {plan.requirements.application.description}", ""]
    if f.is_infeasible:
        lines += [
            "STOP: the architecture is INFEASIBLE. Do not start implementation. Show the user these "
            "conflicts and ask which constraint to change:",
            *[f"- {c}" for c in f.conflicts],
            "",
        ]
    lines.append(
        "Infrastructure components determined by this plan (do not add other infrastructure without asking the user):"
    )
    built = _built(plan)
    for c in built:
        spec = ", ".join(f"{k}={v}" for k, v in c.spec.items()) or "no spec attributes"
        lines.append(f"- {c.component} [{c.status}]: {spec}")
    if not built:
        lines.append("- none required by the confirmed requirements")
    options = [
        " + ".join(cfg.bundles) + f" (provider {cfg.provider_state}, budget {cfg.budget_state})"
        for cfg in arch.provider_candidates
    ]
    if options:
        lines += [
            "",
            "Provider options (ask the user to choose; do not choose for them):",
            *[f"- {o}" for o in options],
        ]
    lines += [
        "",
        "Rules:",
        "- Any value marked UNKNOWN or UNDETERMINED is unresolved: ask the user before implementing that "
        "part; never fill it with a default.",
        "- Cross-provider compatibility is DEFERRED (unverified); verify integrations yourself before relying on them.",
    ]
    if arch.avoided_items:
        lines.append(
            f"- Do not add: {', '.join(arch.avoided_items)} (deliberately avoided; no requirement justifies it)."
        )
    unresolved = [u for u in arch.unresolved_items if not u.startswith("compatibility")]
    if unresolved:
        lines += ["", "Unresolved items to ask the user about:", *[f"- {u}" for u in unresolved]]
    return "\n".join(lines)
