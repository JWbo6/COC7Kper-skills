#!/usr/bin/env python3
"""CoC 7e dice utilities. Standard library only; emits one JSON object."""
from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
import uuid
from datetime import datetime, timezone

EXPR = re.compile(r"^\s*(\d*)d(\d+)(?:\s*([+-])\s*(\d+))?\s*$", re.I)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_expr(text: str) -> dict:
    value = str(text).strip()
    if re.fullmatch(r"[+-]?\d+", value):
        return {"expression": value, "rolls": [], "modifier": int(value), "total": int(value)}
    match = EXPR.fullmatch(value)
    if not match:
        raise ValueError(f"invalid dice expression: {text}")
    count = int(match.group(1) or 1)
    sides = int(match.group(2))
    if not 1 <= count <= 1000 or not 1 <= sides <= 100000:
        raise ValueError("dice count must be 1..1000 and sides 1..100000")
    modifier = int(match.group(4) or 0)
    if match.group(3) == "-":
        modifier = -modifier
    rolls = [secrets.randbelow(sides) + 1 for _ in range(count)]
    return {
        "expression": value,
        "rolls": rolls,
        "modifier": modifier,
        "total": sum(rolls) + modifier,
    }


def d100(bonus: int = 0, penalty: int = 0) -> dict:
    if bonus < 0 or penalty < 0:
        raise ValueError("bonus and penalty must be non-negative")
    net_bonus = max(bonus - penalty, 0)
    net_penalty = max(penalty - bonus, 0)
    unit = secrets.randbelow(10)
    tens_count = max(net_bonus, net_penalty) + 1
    tens = [secrets.randbelow(10) for _ in range(tens_count)]
    raw_candidates = [t * 10 + unit for t in tens]
    candidates = [100 if raw == 0 else raw for raw in raw_candidates]
    value = min(candidates) if net_bonus else max(candidates) if net_penalty else candidates[0]
    return {
        "value": value,
        "display": "00" if value == 100 else f"{value:02d}",
        "unit": unit,
        "tens": tens,
        "candidates": candidates,
        "bonus": net_bonus,
        "penalty": net_penalty,
    }


def check(skill: int, difficulty: str = "normal", modifier: int = 0,
          bonus: int = 0, penalty: int = 0) -> dict:
    if not 0 <= skill <= 100:
        raise ValueError("skill must be 0..100")
    if difficulty not in {"normal", "hard", "extreme"}:
        raise ValueError("difficulty must be normal, hard, or extreme")
    effective = skill + modifier
    hard = effective // 2
    extreme = effective // 5
    target = {"normal": effective, "hard": hard, "extreme": extreme}[difficulty]
    roll = d100(bonus, penalty)
    value = roll["value"]
    if value == 1:
        level, success = "critical", True
    elif value == 100 or (effective < 50 and value >= 96):
        level, success = "fumble", False
    elif value <= extreme:
        level, success = "extreme", value <= target
    elif value <= hard:
        level, success = "hard", value <= target
    elif value <= effective:
        level, success = "regular", value <= target
    else:
        level, success = "failure", False
    return {
        "skill": skill,
        "modifier": modifier,
        "effective_skill": effective,
        "difficulty": difficulty,
        "target": target,
        "roll": roll,
        "success": success,
        "success_level": level,
    }


def base(mode: str) -> dict:
    return {
        "ok": True,
        "roll_id": str(uuid.uuid4()),
        "timestamp": timestamp(),
        "mode": mode,
        "execution_mode": "python-secrets",
    }


def opposed(args: argparse.Namespace) -> dict:
    left = check(args.skill_a, modifier=args.modifier_a, bonus=args.bonus_a, penalty=args.penalty_a)
    right = check(args.skill_b, modifier=args.modifier_b, bonus=args.bonus_b, penalty=args.penalty_b)
    ranks = {"fumble": 0, "failure": 1, "regular": 2, "hard": 3, "extreme": 4, "critical": 5}
    left_rank, right_rank = ranks[left["success_level"]], ranks[right["success_level"]]
    if left_rank > right_rank:
        winner, reason = "a", "higher success level"
    elif right_rank > left_rank:
        winner, reason = "b", "higher success level"
    elif left["effective_skill"] > right["effective_skill"]:
        winner, reason = "a", "same level, higher skill"
    elif right["effective_skill"] > left["effective_skill"]:
        winner, reason = "b", "same level, higher skill"
    else:
        winner, reason = "tie", "same level and skill"
    result = base("opposed")
    result.update({"a": left, "b": right, "winner": winner, "reason": reason})
    return result


def san(args: argparse.Namespace) -> dict:
    parts = args.loss.split("/", 1)
    if len(parts) != 2:
        raise ValueError("SAN loss must be written as success/failure, e.g. 0/1d6")
    check_result = check(args.san, modifier=args.modifier)
    loss_expr = parts[0] if check_result["success"] else parts[1]
    loss = parse_expr(loss_expr)
    if loss["total"] < 0:
        raise ValueError("SAN loss cannot be negative")
    result = base("san")
    result.update({
        "san_before": args.san,
        "check": check_result,
        "loss": loss,
        "san_after": max(0, args.san - loss["total"]),
    })
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CoC 7e dice utilities")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    roll = sub.add_parser("roll", help="roll a dice expression")
    roll.add_argument("expression")
    check_parser = sub.add_parser("check", help="CoC percentile check")
    check_parser.add_argument("--skill", type=int, required=True)
    check_parser.add_argument("--difficulty", choices=["normal", "hard", "extreme"], default="normal")
    check_parser.add_argument("--modifier", type=int, default=0)
    check_parser.add_argument("--bonus", type=int, default=0)
    check_parser.add_argument("--penalty", type=int, default=0)
    opposed_parser = sub.add_parser("opposed", help="opposed checks")
    opposed_parser.add_argument("--skill-a", type=int, required=True)
    opposed_parser.add_argument("--skill-b", type=int, required=True)
    opposed_parser.add_argument("--modifier-a", type=int, default=0)
    opposed_parser.add_argument("--modifier-b", type=int, default=0)
    opposed_parser.add_argument("--bonus-a", type=int, default=0)
    opposed_parser.add_argument("--bonus-b", type=int, default=0)
    opposed_parser.add_argument("--penalty-a", type=int, default=0)
    opposed_parser.add_argument("--penalty-b", type=int, default=0)
    damage = sub.add_parser("damage", help="damage expression minus armor")
    damage.add_argument("expression")
    damage.add_argument("--armor", type=int, default=0)
    san_parser = sub.add_parser("san", help="SAN check and loss")
    san_parser.add_argument("--san", type=int, required=True)
    san_parser.add_argument("--loss", required=True, help="success/failure, e.g. 0/1d6")
    san_parser.add_argument("--modifier", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "roll":
            result = base("roll")
            result["dice"] = parse_expr(args.expression)
        elif args.command == "check":
            result = base("check")
            result["check"] = check(args.skill, args.difficulty, args.modifier, args.bonus, args.penalty)
        elif args.command == "opposed":
            result = opposed(args)
        elif args.command == "damage":
            if args.armor < 0:
                raise ValueError("armor must be non-negative")
            dice = parse_expr(args.expression)
            result = base("damage")
            result.update({"dice": dice, "armor": args.armor, "damage": max(0, dice["total"] - args.armor)})
        else:
            if not 0 <= args.san <= 100:
                raise ValueError("san must be 0..100")
            result = san(args)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
        return 0
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
