#!/usr/bin/env python3
"""Non-destructive file manager for the project-level CoC skills."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0.0"
ROOT_DIRS = ["COC须知", "模组", "进行中的团", "结束的团"]
NOTICE_DIRS = ["规则", "车卡资料", "KP资料", "时代与设定"]
MODULE_DIRS = ["待整理", "可开团", "已使用"]
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "assets" / "templates"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def inside(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def slug(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "-", value.strip())
    value = re.sub(r"\s+", "-", value)
    return value.strip(" .-") or "未命名"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def create_missing(path: Path, content: str | None, dry_run: bool, actions: list[str]) -> None:
    if path.exists():
        actions.append(f"跳过已有: {path}")
        return
    actions.append(f"创建: {path}")
    if not dry_run:
        if content is None:
            path.mkdir(parents=True, exist_ok=True)
        else:
            atomic_write(path, content)


def template_content(name: str) -> str:
    source = TEMPLATE_DIR / name
    if not source.is_file():
        raise FileNotFoundError(f"模板不存在: {source}")
    return source.read_text(encoding="utf-8")


def workspace_paths(root: Path) -> Iterable[Path]:
    yield root / "工作区说明.md"
    for directory in ROOT_DIRS:
        yield root / directory
    for directory in NOTICE_DIRS:
        yield root / "COC须知" / directory
    for directory in MODULE_DIRS:
        yield root / "模组" / directory


def init_workspace(root: Path, dry_run: bool) -> int:
    actions: list[str] = []
    for path in workspace_paths(root):
        create_missing(path, None, dry_run, actions) if path.suffix == "" else create_missing(path, template_content("工作区说明.md"), dry_run, actions)
    if not dry_run:
        explanation = root / "工作区说明.md"
        if not explanation.exists():
            atomic_write(explanation, template_content("工作区说明.md"))
    for action in actions:
        print(action)
    return 0


def campaign_tree(root: Path, campaign_dir: Path) -> dict[str, Path]:
    return {
        "root": campaign_dir,
        "00": campaign_dir / "00-团务",
        "01": campaign_dir / "01-模组资料",
        "raw": campaign_dir / "01-模组资料" / "原始模组",
        "kp": campaign_dir / "01-模组资料" / "主持人资料",
        "02": campaign_dir / "02-调查员",
        "03": campaign_dir / "03-场次记录",
        "04": campaign_dir / "04-调查状态",
        "05": campaign_dir / "05-素材",
    }


def file_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_campaign(root: Path, name: str, source: Path, dry_run: bool) -> int:
    source = source.expanduser().resolve()
    if not source.is_file():
        print(f"错误: 模组源不存在或不是文件: {source}", file=sys.stderr)
        return 2
    clean_name = slug(name)
    year = datetime.now().year
    campaign_dir = (root / "进行中的团" / f"{year}-{clean_name}").resolve()
    if not inside(root, campaign_dir):
        print("错误: 团目录越过工作区根目录", file=sys.stderr)
        return 2
    if campaign_dir.exists():
        print(f"冲突: 团目录已存在，未覆盖: {campaign_dir}", file=sys.stderr)
        return 3
    paths = campaign_tree(root, campaign_dir)
    campaign_copy = (paths["raw"] / source.name).resolve()
    if not inside(campaign_dir, campaign_copy):
        print("错误: 模组副本越过团目录", file=sys.stderr)
        return 2
    if campaign_copy == source:
        print("错误: 模组源不能与团内副本为同一文件", file=sys.stderr)
        return 2
    source_hash = sha256(source)
    source_record = {
        "source_id": "source_" + hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:20],
        "path": str(source),
        "absolute_path": str(source),
        "original_absolute_path": str(source),
        "campaign_copy_path": str(campaign_copy.relative_to(campaign_dir)).replace(os.sep, "/"),
        "copy_status": "verified",
        "format": source.suffix.lower().lstrip("."),
        "size_bytes": source.stat().st_size,
        "modified_at": file_mtime(source),
        "sha256": source_hash,
        "parse_status": "pending",
        "parse_method": "",
        "parse_time": None,
    }
    for path in paths.values():
        if path.suffix == "":
            print(f"创建: {path}")
            if not dry_run:
                path.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"复制并校验: {source} -> {campaign_copy} (sha256={source_hash})")
    else:
        shutil.copy2(source, campaign_copy)
        copied_hash = sha256(campaign_copy)
        if copied_hash != source_hash:
            print(f"错误: 模组副本哈希不一致: {campaign_copy}", file=sys.stderr)
            return 4
    stamp = now()
    campaign_id = "campaign_" + hashlib.sha1(str(campaign_dir).encode("utf-8")).hexdigest()[:20]
    files: dict[str, str] = {
        "00/团信息.json": json.dumps({"id": campaign_id, "record_type": "campaign", "schema_version": SCHEMA_VERSION, "campaign_id": campaign_id, "name": name, "path_name": campaign_dir.name, "rule_system": "Call of Cthulhu 7e", "status": "preparing", "kp": "", "players": [], "module_sources": [source_record], "current_session_id": None, "created_at": stamp, "updated_at": stamp, "revision": 1}, ensure_ascii=False, indent=2) + "\n",
        "00/场次索引.json": json.dumps({"schema_version": SCHEMA_VERSION, "campaign_id": campaign_id, "sessions": [], "updated_at": stamp, "revision": 1}, ensure_ascii=False, indent=2) + "\n",
        "00/当前状态.md": template_content("当前状态.md"),
        "00/玩家可知信息.md": template_content("玩家可知信息.md"),
        "01/模组索引.json": json.dumps({"schema_version": SCHEMA_VERSION, "campaign_id": campaign_id, "sources": [source_record], "public_summary": "", "kp_notes_path": "主持人资料/", "updated_at": stamp, "revision": 1}, ensure_ascii=False, indent=2) + "\n",
        "03/掷骰记录.jsonl": "",
        "04/线索.json": template_content("线索.json"),
        "04/NPC.json": template_content("NPC.json"),
        "04/地点.json": template_content("地点.json"),
        "04/道具.json": template_content("道具.json"),
    }
    for relative, content in files.items():
        prefix = {"00": paths["00"], "01": paths["01"], "03": paths["03"], "04": paths["04"]}[relative.split("/", 1)[0]]
        target = prefix / relative.split("/", 1)[1]
        print(f"创建: {target}")
        if not dry_run:
            atomic_write(target, content)
    return 0


def json_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.json")


def validate_json(root: Path, target: str | None) -> int:
    paths = [Path(target).resolve()] if target else list(json_files(root))
    errors = 0
    for path in paths:
        if not inside(root, path) or not path.is_file():
            print(f"错误: JSON 不在工作区或不存在: {path}", file=sys.stderr)
            errors += 1
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            print(f"有效 JSON: {path}")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"无效 JSON: {path}: {exc}", file=sys.stderr)
            errors += 1
    return 1 if errors else 0


def validate_campaign(root: Path, name: str) -> int:
    matches = list((root / "进行中的团").glob(f"*-{slug(name)}"))
    if not matches:
        print(f"未找到团: {name}", file=sys.stderr)
        return 2
    campaign_dir = matches[0]
    required = ["00-团务/团信息.json", "00-团务/场次索引.json", "00-团务/当前状态.md", "00-团务/玩家可知信息.md", "01-模组资料/模组索引.json", "03-场次记录/掷骰记录.jsonl", "04-调查状态/线索.json", "04-调查状态/NPC.json", "04-调查状态/地点.json", "04-调查状态/道具.json"]
    missing = [str(campaign_dir / item) for item in required if not (campaign_dir / item).exists()]
    if missing:
        for item in missing:
            print(f"缺失: {item}", file=sys.stderr)
        return 1
    index_path = campaign_dir / "01-模组资料" / "模组索引.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"错误: 无法读取模组索引: {exc}", file=sys.stderr)
        return 1
    source_errors = 0
    for source in index.get("sources", []):
        copy_path_value = source.get("campaign_copy_path")
        if not copy_path_value:
            if source.get("original_absolute_path") or source.get("absolute_path"):
                print(f"警告: 旧模组索引缺少团内副本字段: {source.get('absolute_path', source.get('original_absolute_path'))}", file=sys.stderr)
            continue
        copy_path = (campaign_dir / copy_path_value).resolve()
        if not inside(campaign_dir, copy_path) or not copy_path.is_file():
            print(f"错误: 模组副本缺失或越过团目录: {copy_path}", file=sys.stderr)
            source_errors += 1
            continue
        expected_hash = source.get("sha256")
        actual_hash = sha256(copy_path)
        if expected_hash and actual_hash != expected_hash:
            print(f"错误: 模组副本哈希不一致: {copy_path}", file=sys.stderr)
            source_errors += 1
        else:
            print(f"有效模组副本: {copy_path}")
    if source_errors:
        return 1
    print(f"结构有效: {campaign_dir}")
    return validate_json(campaign_dir, None)


def list_status(root: Path) -> int:
    active = root / "进行中的团"
    archived = root / "结束的团"
    for label, directory in (("进行中", active), ("已结束", archived)):
        print(f"[{label}]")
        for path in sorted(directory.iterdir()) if directory.is_dir() else []:
            if path.is_dir():
                state = path / "00-团务" / "当前状态.md"
                print(f"- {path.name}: {'有当前状态' if state.exists() else '缺当前状态'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="COC 工作区非破坏性文件管理工具")
    parser.add_argument("command", choices=["init", "create-campaign", "validate-json", "validate-campaign", "list-status"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--name")
    parser.add_argument("--source", help="新建团时复制到 01-模组资料/原始模组/ 的模组源文件")
    parser.add_argument("--path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    root = safe_root(args.root)
    if args.command == "init":
        return init_workspace(root, args.dry_run)
    if args.command == "create-campaign":
        if not args.name:
            parser.error("create-campaign 需要 --name")
        if not args.source:
            parser.error("create-campaign 需要 --source")
        return create_campaign(root, args.name, Path(args.source), args.dry_run)
    if args.command == "validate-json":
        return validate_json(root, args.path)
    if args.command == "validate-campaign":
        if not args.name:
            parser.error("validate-campaign 需要 --name")
        return validate_campaign(root, args.name)
    return list_status(root)


if __name__ == "__main__":
    raise SystemExit(main())
