#!/usr/bin/env bash
set -euo pipefail

RAW_ROOT="/data/liuly/dataset/3DGS/GlossySynthetic"
CONVERTED_ROOT="/data/liuly/dataset/3DGS/GlossySyntheticConverted"
CONDA_ENV=""
NERO2BLENDER="/home/liuly/Surface_Reconstruction/Glossy/GS-2M/scripts/preprocess/nero2blender.py"
MODE="copy"   # copy|move
FORCE=0
DRY_RUN=0
SCENES=""

usage() {
  cat <<'EOF'
Batch-convert GlossySynthetic (raw NeRO-style) to Blender-style and collect into
GlossySyntheticConverted (so RC-RefGS runner can consume it).

This script ONLY prepares data. It does NOT start any training.

Default paths (override as needed):
  --raw_root PATH        default: /data/liuly/dataset/3DGS/GlossySynthetic
  --converted_root PATH  default: /data/liuly/dataset/3DGS/GlossySyntheticConverted

Conversion backend:
  --nero2blender PATH    default: /home/liuly/Surface_Reconstruction/Glossy/GS-2M/scripts/preprocess/nero2blender.py
  --conda_env NAME       optional: run conversion via `conda run -n NAME python`

Scene selection:
  --scenes LIST          optional: comma/space separated (e.g., "angel,bell")
                         default: auto-discover subdirs under --raw_root

Staging behavior:
  --mode copy|move       default: copy (move is destructive)
  --force                overwrite existing converted outputs
  --dry_run              print actions only

Examples:
  bash scripts/prepare_glossy_synthetic_converted.sh \
    --raw_root /data/liuly/dataset/3DGS/GlossySynthetic \
    --converted_root /data/liuly/dataset/3DGS/GlossySyntheticConverted \
    --conda_env ref_gs

  bash scripts/prepare_glossy_synthetic_converted.sh --dry_run
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 2
}

split_csv_or_space() {
  local value="$1"
  value="${value//,/ }"
  # shellcheck disable=SC2086
  printf '%s\n' $value
}

require_file() {
  local label="$1"
  local path="$2"
  [[ -f "${path}" ]] || die "${label} missing: ${path}"
}

require_dir() {
  local label="$1"
  local path="$2"
  [[ -d "${path}" ]] || die "${label} missing: ${path}"
}

python_cmd() {
  if [[ -n "${CONDA_ENV}" ]]; then
    echo "conda run -n ${CONDA_ENV} python"
  else
    echo "python"
  fi
}

run_or_echo() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

copy_or_move_dir() {
  local src="$1"
  local dst="$2"

  if [[ -e "${dst}" ]]; then
    if [[ "${FORCE}" -eq 1 ]]; then
      run_or_echo rm -rf "${dst}"
    else
      echo "[SKIP] exists: ${dst}" >&2
      return 0
    fi
  fi

  run_or_echo mkdir -p "$(dirname "${dst}")"

  if [[ "${MODE}" == "move" ]]; then
    run_or_echo mv "${src}" "${dst}"
  elif command -v rsync >/dev/null 2>&1; then
    run_or_echo rsync -a "${src}/" "${dst}/"
  else
    run_or_echo cp -a "${src}" "${dst}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      usage
      exit 0
      ;;
    --raw_root)
      RAW_ROOT="${2:-}"
      shift 2
      ;;
    --converted_root)
      CONVERTED_ROOT="${2:-}"
      shift 2
      ;;
    --conda_env)
      CONDA_ENV="${2:-}"
      shift 2
      ;;
    --nero2blender)
      NERO2BLENDER="${2:-}"
      shift 2
      ;;
    --scenes)
      SCENES="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry_run)
      DRY_RUN=1
      shift
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

require_dir "--raw_root" "${RAW_ROOT}"
require_file "--nero2blender" "${NERO2BLENDER}"

if [[ "${MODE}" != "copy" && "${MODE}" != "move" ]]; then
  die "--mode must be copy|move (got: ${MODE})"
fi

# Determine scene list
scene_list=()
if [[ -n "${SCENES}" ]]; then
  while IFS= read -r s; do
    [[ -n "${s}" ]] || continue
    scene_list+=("${s}")
  done < <(split_csv_or_space "${SCENES}")
else
  while IFS= read -r d; do
    [[ -n "${d}" ]] || continue
    base="$(basename "${d}")"
    [[ "${base}" != .* ]] || continue
    [[ "${base}" != *_blender ]] || continue
    scene_list+=("${base}")
  done < <(find "${RAW_ROOT}" -mindepth 1 -maxdepth 1 -type d | sort)
fi

[[ "${#scene_list[@]}" -gt 0 ]] || die "No scenes found under ${RAW_ROOT} (or --scenes is empty)"

run_or_echo mkdir -p "${CONVERTED_ROOT}"

echo "[INFO] raw_root       = ${RAW_ROOT}" >&2
echo "[INFO] converted_root = ${CONVERTED_ROOT}" >&2
echo "[INFO] nero2blender   = ${NERO2BLENDER}" >&2
echo "[INFO] conda_env      = ${CONDA_ENV:-<none>}" >&2
echo "[INFO] mode           = ${MODE}" >&2
echo "[INFO] force          = ${FORCE}" >&2
echo "[INFO] scenes         = ${#scene_list[@]}" >&2

# Build python invocation (as an argv array)
PYTHON=(python)
if [[ -n "${CONDA_ENV}" ]]; then
  PYTHON=(conda run -n "${CONDA_ENV}" python)
fi

converted_ok=0
converted_fail=0

for scene in "${scene_list[@]}"; do
  src_scene_dir="${RAW_ROOT}/${scene}"
  [[ -d "${src_scene_dir}" ]] || die "missing scene dir: ${src_scene_dir}"

  raw_out_dir="${RAW_ROOT}/${scene}_blender"
  dst_out_dir="${CONVERTED_ROOT}/${scene}_blender"

  # Convert (writes into RAW_ROOT as <scene>_blender)
  if [[ -d "${raw_out_dir}" && "${FORCE}" -eq 0 ]]; then
    echo "[SKIP] already converted in raw root: ${raw_out_dir}" >&2
  else
    echo "[CONVERT] ${scene}" >&2
    run_or_echo "${PYTHON[@]}" "${NERO2BLENDER}" --path "${RAW_ROOT}" --scene "${scene}"
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[PLAN] dry-run defers converted-output validation: ${raw_out_dir}" >&2
    echo "[COLLECT] ${raw_out_dir} -> ${dst_out_dir}" >&2
    copy_or_move_dir "${raw_out_dir}" "${dst_out_dir}"
    converted_ok=$((converted_ok + 1))
    continue
  fi

  # Validate conversion output
  if [[ ! -f "${raw_out_dir}/transforms_train.json" || ! -f "${raw_out_dir}/transforms_test.json" ]]; then
    echo "[FAIL] missing transforms in ${raw_out_dir}" >&2
    converted_fail=$((converted_fail + 1))
    continue
  fi
  if [[ ! -d "${raw_out_dir}/rgb" ]]; then
    echo "[FAIL] missing rgb/ in ${raw_out_dir}" >&2
    converted_fail=$((converted_fail + 1))
    continue
  fi

  # Collect into converted root
  echo "[COLLECT] ${raw_out_dir} -> ${dst_out_dir}" >&2
  copy_or_move_dir "${raw_out_dir}" "${dst_out_dir}"

  # Post-validate destination
  if [[ -f "${dst_out_dir}/transforms_train.json" && -f "${dst_out_dir}/transforms_test.json" ]]; then
    converted_ok=$((converted_ok + 1))
  else
    echo "[FAIL] destination missing transforms: ${dst_out_dir}" >&2
    converted_fail=$((converted_fail + 1))
  fi

done

echo "[DONE] converted_ok=${converted_ok} converted_fail=${converted_fail}" >&2

if [[ "${converted_fail}" -gt 0 ]]; then
  exit 2
fi
