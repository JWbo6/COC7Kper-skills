#!/usr/bin/env bash
set -euo pipefail

DEFAULT_DEST="${CODEX_HOME:-$HOME/.codex}/skills"
DESTINATION="$DEFAULT_DEST"
FORCE=0
REQUESTED=()

usage() {
  cat <<'EOF'
Usage: install.sh [options] [skill ...]

Options:
  --destination DIR  Install into DIR (default: CODEX_HOME/skills or ~/.codex/skills)
  --force            Replace existing skill directories
  -h, --help         Show this help

Without skill names, all bundled skills are installed.
EOF
}

while (($#)); do
  case "$1" in
    --destination)
      (($# >= 2)) || { printf '%s\n' 'error: --destination needs a directory' >&2; exit 2; }
      DESTINATION="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      REQUESTED+=("$@")
      break
      ;;
    -* )
      printf 'error: unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
    *)
      REQUESTED+=("$1")
      shift
      ;;
  esac
done

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/skills"
[[ -d "$SOURCE_DIR" ]] || { printf '%s\n' "error: skills directory not found: $SOURCE_DIR" >&2; exit 1; }

mapfile -t AVAILABLE < <(find "$SOURCE_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
if ((${#REQUESTED[@]} == 0)); then
  REQUESTED=("${AVAILABLE[@]}")
fi

contains_skill() {
  local wanted="$1" item
  for item in "${AVAILABLE[@]}"; do
    [[ "$item" == "$wanted" ]] && return 0
  done
  return 1
}

mkdir -p "$DESTINATION"
for skill in "${REQUESTED[@]}"; do
  contains_skill "$skill" || { printf 'error: unknown skill: %s\n' "$skill" >&2; exit 2; }
  source="$SOURCE_DIR/$skill"
  target="$DESTINATION/$skill"
  [[ -f "$source/SKILL.md" || "$skill" == "coc-shared" ]] || { printf 'error: missing SKILL.md: %s\n' "$source" >&2; exit 1; }
  if [[ -e "$target" && "$FORCE" -ne 1 ]]; then
    printf 'skip existing: %s\n' "$target"
    continue
  fi
  if [[ -e "$target" ]]; then
    rm -rf -- "$target"
  fi
  cp -R -- "$source" "$target"
  printf 'installed: %s\n' "$target"
done

printf '\nInstalled into: %s\n' "$DESTINATION"
printf 'Restart Codex/ZCode to discover the skills.\n'
