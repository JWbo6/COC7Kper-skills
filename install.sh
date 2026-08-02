#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_URL="${COC7KPER_ARCHIVE_URL:-https://github.com/JWbo6/COC7Kper-skills/archive/refs/heads/main.tar.gz}"
DEFAULT_DEST="${CODEX_HOME:-$HOME/.codex}/skills"
DESTINATION="$DEFAULT_DEST"
FORCE=0
REQUESTED=()
BOOTSTRAP_DIR=""

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

cleanup() {
  if [[ -n "$BOOTSTRAP_DIR" && -d "$BOOTSTRAP_DIR" ]]; then
    rm -rf -- "$BOOTSTRAP_DIR"
  fi
}
trap cleanup EXIT

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/skills"
if [[ ! -d "$SOURCE_DIR" ]]; then
  command -v curl >/dev/null 2>&1 || { printf '%s\n' 'error: curl is required when installing from a downloaded script' >&2; exit 1; }
  command -v tar >/dev/null 2>&1 || { printf '%s\n' 'error: tar is required when installing from a downloaded script' >&2; exit 1; }
  BOOTSTRAP_DIR="$(mktemp -d)"
  curl -fsSL "$ARCHIVE_URL" | tar -xz -C "$BOOTSTRAP_DIR"
  SOURCE_DIR="$(find "$BOOTSTRAP_DIR" -mindepth 2 -maxdepth 2 -type d -name skills -print | head -n 1)"
  [[ -n "$SOURCE_DIR" && -d "$SOURCE_DIR" ]] || { printf '%s\n' 'error: downloaded archive has no skills directory' >&2; exit 1; }
fi

AVAILABLE=()
for path in "$SOURCE_DIR"/*; do
  [[ -d "$path" ]] && AVAILABLE+=("${path##*/}")
done
((${#AVAILABLE[@]} > 0)) || { printf '%s\n' "error: no skills found: $SOURCE_DIR" >&2; exit 1; }

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
