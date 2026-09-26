"""`architect` CLI: extraction, human requirement review (V1 review surface), planning."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from architect.clarification import ClarificationQuestion, run_clarification
from architect.extraction import ExtractionError, claude_cli, extract
from architect.output import agent_prompt, architecture_brief, diagram_data
from architect.providers import load_seed_bundles
from architect.requirements import RequirementModel, RequirementValue
from architect.requirements.fields import FIELD_PATHS, get_value, parse_user_value, with_value
from architect.resolution import is_infeasible, resolve


def apply_edit(model: RequirementModel, path: str, raw: str) -> RequirementModel:
    """Set `path` from user input: KNOWN/USER, or UNKNOWN for `?`. Any edit clears confirmation.

    Raises:
        KeyError: `path` is not a requirement field.
        ValueError: `raw` is not a valid value for the field.
    """
    new = parse_user_value(path, raw, "set in review")
    return with_value(model, path, new).model_copy(update={"confirmed": False})


def format_requirements(model: RequirementModel) -> str:
    lines = [f"Description: {model.application.description}", ""]
    for path in FIELD_PATHS:
        rv = get_value(model, path)
        value = "-" if rv.value is None else json.dumps(rv.value, ensure_ascii=False)
        quote = f'  "{rv.source_text}"' if rv.source_text else ""
        lines.append(f"{path:36} {value:18} {rv.state:9} {rv.provenance:10}{quote}")
    return "\n".join(lines)


_REVIEW_HELP = "Edit with <field>=<value> (use ? for unknown). 'confirm' to accept, 'quit' to save unconfirmed."


def review(model: RequirementModel) -> RequirementModel:
    """Interactive review loop on stdin/stdout. Returns the (possibly confirmed) model."""
    print(format_requirements(model))
    print("\n" + _REVIEW_HELP)
    while True:
        try:
            line = input("review> ").strip()
        except (EOFError, KeyboardInterrupt):  # end of input: keep the edits, unconfirmed
            print()
            return model
        if line == "confirm":
            return model.model_copy(update={"confirmed": True})
        if line == "quit":
            return model
        path, sep, raw = line.partition("=")
        if not sep:
            print(_REVIEW_HELP)
            continue
        try:
            model = apply_edit(model, path.strip(), raw)
        except (KeyError, ValueError) as e:
            print(f"invalid edit: {e}")
            continue
        rv = get_value(model, path.strip())
        print(f"{path.strip()} = {rv.value!r} ({rv.state}, {rv.provenance})")


def _load(path: Path) -> RequirementModel:
    return RequirementModel.model_validate_json(path.read_text(encoding="utf-8"))


def _save(model: RequirementModel, path: Path) -> None:
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")


def _cmd_extract(args: argparse.Namespace) -> int:
    description = args.description if args.description is not None else Path(args.file).read_text(encoding="utf-8")
    try:
        result = extract(description, claude_cli)
    except (ExtractionError, ValueError) as e:
        print(f"extraction failed: {e}", file=sys.stderr)
        return 1
    _save(result.requirements, Path(args.out))
    print(format_requirements(result.requirements))
    for issue in result.issues:
        print(f"extraction issue: {issue}")
    print(f"\nSaved unconfirmed requirements to {args.out}. Next: architect review {args.out}")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    path = Path(args.requirements)
    model = review(_load(path))
    _save(model, path)
    print("confirmed" if model.confirmed else "saved, NOT confirmed")
    return 0


def ask_terminal(question: ClarificationQuestion) -> RequirementValue[Any] | None:
    """Ask one clarification question; re-ask on invalid input. Blank or `?` means "don't know"."""
    while True:
        try:
            raw = input(f"[priority {question.priority}] {question.prompt} (? = don't know): ").strip()
        except EOFError:  # no more answers: treat as "don't know"
            return None
        if raw in ("", "?"):
            return None
        try:
            return parse_user_value(question.field, raw, "clarification answer")
        except ValueError as e:
            print(f"invalid answer: {e}")


def _cmd_plan(args: argparse.Namespace) -> int:
    path, out = Path(args.requirements), Path(args.out_dir)
    model = _load(path)
    if not model.confirmed:
        print(f"requirements are not confirmed; run: architect review {path}", file=sys.stderr)
        return 2
    bundles = load_seed_bundles()
    outcome = run_clarification(model, ask_terminal, lambda m: is_infeasible(m, bundles))
    _save(outcome.requirements, path)
    plan = resolve(outcome.requirements, bundles).model_copy(
        update={"clarification_rounds": len(outcome.rounds), "clarification_stop": outcome.stop_reason.value}
    )

    out.mkdir(parents=True, exist_ok=True)
    brief = architecture_brief(plan)
    (out / "architecture_brief.md").write_text(brief, encoding="utf-8")
    (out / "diagram.json").write_text(json.dumps(diagram_data(plan), indent=2), encoding="utf-8")
    (out / "agent_prompt.md").write_text(agent_prompt(plan) + "\n", encoding="utf-8")
    (out / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    f = plan.architecture.feasibility
    print(f"clarification: {len(outcome.rounds)} round(s), stopped: {outcome.stop_reason}")
    print(
        f"feasibility: architecture={f.architecture} provider={f.provider} budget={f.budget} "
        f"compatibility={f.compatibility}"
    )
    print(f"wrote {out / 'architecture_brief.md'}, diagram.json, agent_prompt.md, plan.json")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="architect", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extract", help="extract requirements from a description (uses the claude CLI)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--description")
    src.add_argument("--file")
    p.add_argument("--out", default="requirements.json")
    p.set_defaults(func=_cmd_extract)

    p = sub.add_parser("review", help="review, edit, and confirm extracted requirements")
    p.add_argument("requirements")
    p.set_defaults(func=_cmd_review)

    p = sub.add_parser("plan", help="clarify, resolve, and write the brief, diagram data, and agent prompt")
    p.add_argument("requirements")
    p.add_argument("--out-dir", default="architecture")
    p.set_defaults(func=_cmd_plan)

    args = parser.parse_args(argv)
    code: int = args.func(args)
    return code
