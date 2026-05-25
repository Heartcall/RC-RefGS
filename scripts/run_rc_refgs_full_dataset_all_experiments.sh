#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=1
CONFIRM_FULL_DATASET_EXECUTE=""
SHINY_BLENDER_SYNTHETIC_ROOT=""
SHINY_BLENDER_REAL_ROOT=""
GLOSSY_SYNTHETIC_ROOT=""
OUTPUT_ROOT=""
DEVICES=""
SEEDS="0"
ITERATIONS=31000
MAX_PAIRS=10
VARIANTS="base,rc,wo_ref,wo_conf,rough_only"
JOBS_PER_GPU=1
FORCE_RERUN=0
RERUN_FAILED=0
SKIP_TRAIN=0
SKIP_COMPLETED=1

usage() {
  cat <<'EOF'
Run the complete RC-RefGS full-dataset experiment matrix.

Default mode is dry-run. Real training is refused unless both flags are present:
  --execute --confirm_full_dataset_execute YES

Required roots:
  --shiny_blender_synthetic_root PATH
  --shiny_blender_real_root PATH
  --glossy_synthetic_root PATH

Required runtime args:
  --output_root PATH
  --devices DEVICES

Options:
  --seeds LIST                         default: 0
  --iterations N                       default: 31000
  --max_pairs N                        default: 10
  --variants LIST                      default: base,rc,wo_ref,wo_conf,rough_only
  --jobs_per_gpu N                     default: 1; sequential scheduling is used unless raised
  --force_rerun                        overwrite completed jobs
  --rerun_failed                       run incomplete/failed jobs only
  --resume_existing                    alias for default skip-complete behavior
  --skip_train                         if point_cloud exists, regenerate only missing metrics
  --execute                            disable dry-run, requires confirmation
  --confirm_full_dataset_execute YES   required with --execute
  --help

Safety policy:
  - Covers Shiny Blender Synthetic, Shiny Blender Real, and Glossy Synthetic.
  - Prior teapot/toaster/car results remain subset evidence only.
  - Glossy Synthetic must already be converted with nero2blender.py; raw NeRO-style scenes fail.
  - Runtime commands use scripts/run_rc_refgs_ablation_direct.py only.
  - Commands use --cuda_device and never set CUDA_VISIBLE_DEVICES.
  - Status is written to full_dataset_run_status.json and full_dataset_run_status.md.
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

require_value() {
  local name="$1"
  local value="${2:-}"
  [[ -n "${value}" ]] || die "${name} is required"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      usage
      exit 0
      ;;
    --execute)
      DRY_RUN=0
      shift
      ;;
    --confirm_full_dataset_execute)
      CONFIRM_FULL_DATASET_EXECUTE="${2:-}"
      shift 2
      ;;
    --shiny_blender_synthetic_root)
      SHINY_BLENDER_SYNTHETIC_ROOT="${2:-}"
      shift 2
      ;;
    --shiny_blender_real_root)
      SHINY_BLENDER_REAL_ROOT="${2:-}"
      shift 2
      ;;
    --glossy_synthetic_root)
      GLOSSY_SYNTHETIC_ROOT="${2:-}"
      shift 2
      ;;
    --output_root)
      OUTPUT_ROOT="${2:-}"
      shift 2
      ;;
    --devices)
      DEVICES="${2:-}"
      shift 2
      ;;
    --seeds)
      SEEDS="${2:-}"
      shift 2
      ;;
    --iterations)
      ITERATIONS="${2:-}"
      shift 2
      ;;
    --max_pairs)
      MAX_PAIRS="${2:-}"
      shift 2
      ;;
    --variants)
      VARIANTS="${2:-}"
      shift 2
      ;;
    --jobs_per_gpu)
      JOBS_PER_GPU="${2:-}"
      shift 2
      ;;
    --force_rerun)
      FORCE_RERUN=1
      shift
      ;;
    --rerun_failed)
      RERUN_FAILED=1
      shift
      ;;
    --resume_existing)
      SKIP_COMPLETED=1
      shift
      ;;
    --skip_train)
      SKIP_TRAIN=1
      shift
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

require_value "--shiny_blender_synthetic_root" "${SHINY_BLENDER_SYNTHETIC_ROOT}"
require_value "--shiny_blender_real_root" "${SHINY_BLENDER_REAL_ROOT}"
require_value "--glossy_synthetic_root" "${GLOSSY_SYNTHETIC_ROOT}"
require_value "--output_root" "${OUTPUT_ROOT}"
require_value "--devices" "${DEVICES}"

if [[ "${DRY_RUN}" -eq 0 ]]; then
  if [[ "${CONFIRM_FULL_DATASET_EXECUTE}" == "YES" ]]; then
    :
  else
    die "Refusing execution: --execute requires --confirm_full_dataset_execute YES"
  fi
fi

if [[ "${JOBS_PER_GPU}" -lt 1 ]]; then
  die "--jobs_per_gpu must be >= 1"
fi

if [[ "${FORCE_RERUN}" -eq 1 && "${RERUN_FAILED}" -eq 1 ]]; then
  die "--force_rerun and --rerun_failed are mutually exclusive"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIRECT_LAUNCHER="${REPO_ROOT}/scripts/run_rc_refgs_ablation_direct.py"
[[ -f "${DIRECT_LAUNCHER}" ]] || die "missing direct launcher: ${DIRECT_LAUNCHER}"

mapfile -t DEVICE_LIST < <(split_csv_or_space "${DEVICES}")
mapfile -t SEED_LIST < <(split_csv_or_space "${SEEDS}")
mapfile -t VARIANT_LIST < <(split_csv_or_space "${VARIANTS}")

[[ "${#DEVICE_LIST[@]}" -gt 0 ]] || die "--devices is empty"
[[ "${#SEED_LIST[@]}" -gt 0 ]] || die "--seeds is empty"
[[ "${#VARIANT_LIST[@]}" -gt 0 ]] || die "--variants is empty"

validate_variant() {
  case "$1" in
    base|rc|wo_ref|wo_conf|rough_only) ;;
    *) die "unknown variant: $1" ;;
  esac
}
for variant in "${VARIANT_LIST[@]}"; do
  validate_variant "${variant}"
done

scene_type() {
  local dir="$1"
  if [[ -d "${dir}/sparse" ]]; then
    echo "colmap"
  elif [[ -f "${dir}/transforms_train.json" && -f "${dir}/transforms_test.json" ]]; then
    echo "blender"
  else
    echo "invalid"
  fi
}

has_raw_nero_markers() {
  local dir="$1"
  compgen -G "${dir}/*-camera.pkl" >/dev/null || return 1
  compgen -G "${dir}/*-depth.png" >/dev/null || return 1
  return 0
}

discover_dataset() {
  local dataset_name="$1"
  local dataset_label="$2"
  local root="$3"
  local out_file="$4"

  [[ -d "${root}" ]] || die "${dataset_label} root missing: ${root}"
  : > "${out_file}"

  local child
  local valid_count=0
  local raw_count=0
  local seen_labels=" "

  while IFS= read -r child; do
    [[ -n "${child}" ]] || continue
    local base
    base="$(basename "${child}")"
    [[ "${base}" != .* ]] || continue

    local type
    type="$(scene_type "${child}")"
    if [[ "${type}" == "invalid" ]]; then
      if [[ "${dataset_name}" == "glossy_synthetic" ]] && has_raw_nero_markers "${child}"; then
        raw_count=$((raw_count + 1))
      fi
      continue
    fi

    local scene="${base}"
    if [[ "${dataset_name}" == "glossy_synthetic" && "${scene}" == *_blender ]]; then
      scene="${scene%_blender}"
    fi
    if [[ "${seen_labels}" == *" ${scene} "* ]]; then
      die "${dataset_label} scene discovery is ambiguous: duplicate scene label ${scene}"
    fi
    seen_labels="${seen_labels}${scene} "
    printf '%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${child}" "${type}" >> "${out_file}"
    valid_count=$((valid_count + 1))
  done < <(find "${root}" -mindepth 1 -maxdepth 1 -type d | sort)

  if [[ "${dataset_name}" == "glossy_synthetic" && "${raw_count}" -gt 0 ]]; then
    die "Glossy Synthetic needs conversion with nero2blender.py before training: found ${raw_count} raw NeRO-style scene directories under ${root}"
  fi
  [[ "${valid_count}" -gt 0 ]] || die "${dataset_label} root is empty or has no valid scene directories: ${root}"
}

job_complete() {
  local model_path="$1"
  [[ -f "${model_path}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply" ]] || return 1
  [[ -f "${model_path}/reflection_consistency_train.json" ]] || return 1
  [[ -f "${model_path}/reflection_consistency_test.json" ]] || return 1
  [[ -f "${model_path}/launcher_summary.json" ]] || return 1
  return 0
}

point_cloud_exists() {
  local model_path="$1"
  [[ -f "${model_path}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply" ]]
}

missing_artifacts() {
  local model_path="$1"
  local missing=()
  [[ -f "${model_path}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply" ]] || missing+=("point_cloud/iteration_${ITERATIONS}/point_cloud.ply")
  [[ -f "${model_path}/reflection_consistency_train.json" ]] || missing+=("reflection_consistency_train.json")
  [[ -f "${model_path}/reflection_consistency_test.json" ]] || missing+=("reflection_consistency_test.json")
  [[ -f "${model_path}/launcher_summary.json" ]] || missing+=("launcher_summary.json")
  local IFS=';'
  echo "${missing[*]}"
}

write_status() {
  local rows_file="$1"
  local status_json="${OUTPUT_ROOT}/full_dataset_run_status.json"
  local status_md="${OUTPUT_ROOT}/full_dataset_run_status.md"
  mkdir -p "${OUTPUT_ROOT}"

  python - "$rows_file" "$status_json" "$status_md" <<'PY'
import csv
import json
import sys
from collections import Counter
from pathlib import Path

rows_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])
md_path = Path(sys.argv[3])

rows = []
if rows_path.exists():
    with rows_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)

counts = Counter(row["status"] for row in rows)
missing_count = 0
for row in rows:
    missing = [item for item in row.get("missing_artifacts", "").split(";") if item]
    missing_count += len(missing)

summary = {
    "mode": "rc_refgs_full_dataset_all_experiments",
    "planned_count": counts.get("planned", 0),
    "completed_count": counts.get("completed", 0),
    "skipped_count": counts.get("skipped_complete", 0),
    "failed_count": counts.get("failed", 0),
    "missing_artifact_count": missing_count,
    "jobs": rows,
}
json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

lines = [
    "# RC-RefGS Full-Dataset Run Status",
    "",
    f"- Planned: {summary['planned_count']}",
    f"- Completed: {summary['completed_count']}",
    f"- Skipped: {summary['skipped_count']}",
    f"- Failed: {summary['failed_count']}",
    f"- Missing artifacts: {summary['missing_artifact_count']}",
    "",
    "| Dataset | Scene | Variant | Seed | Status | Device | Missing artifacts |",
    "| --- | --- | --- | --- | --- | --- | --- |",
]
for row in rows:
    lines.append(
        "| {dataset} | {scene} | {variant} | {seed} | {status} | {device} | {missing} |".format(
            dataset=row["dataset"],
            scene=row["scene"],
            variant=row["variant"],
            seed=row["seed"],
            status=row["status"],
            device=row["device"],
            missing=row.get("missing_artifacts") or "-",
        )
    )
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

run_job() {
  local dataset_name="$1"
  local scene="$2"
  local source_dir="$3"
  local variant="$4"
  local seed="$5"
  local device="$6"
  local desired_model_path="$7"

  local source_parent
  local source_basename
  source_parent="$(dirname "${source_dir}")"
  source_basename="$(basename "${source_dir}")"
  local actual_parent="${OUTPUT_ROOT}/.direct_launcher_work/${dataset_name}/${scene}/${variant}/seed_${seed}"
  local actual_model_path="${actual_parent}/${source_basename}_${variant}"
  local launcher_summary_path="${actual_model_path}/launcher_summary.json"
  if [[ "${SKIP_TRAIN}" -eq 1 ]]; then
    launcher_summary_path="${desired_model_path}/launcher_summary.json"
  fi

  local command=(
    python "${DIRECT_LAUNCHER}"
    --data_root "${source_parent}"
    --scenes "${source_basename}"
    --variants "${variant}"
    --seeds "${seed}"
    --iterations "${ITERATIONS}"
    --max_pairs "${MAX_PAIRS}"
    --cuda_device "${device}"
    --output_root "${actual_parent}"
    --summary_json "${launcher_summary_path}"
  )

  if [[ "${SKIP_TRAIN}" -eq 1 ]]; then
    command+=(--skip_train)
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    command+=(--dry_run)
    printf 'DRY-RUN would run:'
    printf ' %q' "${command[@]}"
    printf '\n'
    return 0
  fi

  mkdir -p "$(dirname "${desired_model_path}")"

  rm -rf "${actual_model_path}"
  mkdir -p "${actual_parent}"

  if [[ "${SKIP_TRAIN}" -eq 1 ]]; then
    point_cloud_exists "${desired_model_path}" || return 1
    ln -sfn "${desired_model_path}" "${actual_model_path}"
  fi

  if ! "${command[@]}"; then
    return 1
  fi

  if [[ "${SKIP_TRAIN}" -eq 0 ]]; then
    rm -rf "${desired_model_path}"
    if ! mv "${actual_model_path}" "${desired_model_path}"; then
      return 1
    fi
  fi
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT
SCENES_TSV="${TMP_DIR}/scenes.tsv"
ROWS_TSV="${TMP_DIR}/rows.tsv"

{
  discover_dataset "shiny_blender_synthetic" "Shiny Blender Synthetic" "${SHINY_BLENDER_SYNTHETIC_ROOT}" "${TMP_DIR}/shiny_syn.tsv"
  discover_dataset "shiny_blender_real" "Shiny Blender Real" "${SHINY_BLENDER_REAL_ROOT}" "${TMP_DIR}/shiny_real.tsv"
  discover_dataset "glossy_synthetic" "Glossy Synthetic" "${GLOSSY_SYNTHETIC_ROOT}" "${TMP_DIR}/glossy_syn.tsv"
} >&2

cat "${TMP_DIR}/shiny_syn.tsv" "${TMP_DIR}/shiny_real.tsv" "${TMP_DIR}/glossy_syn.tsv" > "${SCENES_TSV}"

echo "dataset	scene	variant	seed	status	device	model_path	missing_artifacts" > "${ROWS_TSV}"

job_index=0
while IFS=$'\t' read -r dataset_name scene source_dir scene_kind; do
  [[ -n "${dataset_name}" ]] || continue
  for seed in "${SEED_LIST[@]}"; do
    for variant in "${VARIANT_LIST[@]}"; do
      device="${DEVICE_LIST[$((job_index % ${#DEVICE_LIST[@]}))]}"
      desired_model_path="${OUTPUT_ROOT}/${dataset_name}/${scene}/${variant}/seed_${seed}"
      missing="$(missing_artifacts "${desired_model_path}")"

      if job_complete "${desired_model_path}" && [[ "${FORCE_RERUN}" -eq 0 ]]; then
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "skipped_complete" "${device}" "${desired_model_path}" "" >> "${ROWS_TSV}"
        job_index=$((job_index + 1))
        continue
      fi

      if [[ "${RERUN_FAILED}" -eq 1 && -z "${missing}" ]]; then
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "skipped_complete" "${device}" "${desired_model_path}" "" >> "${ROWS_TSV}"
        job_index=$((job_index + 1))
        continue
      fi

      if [[ "${SKIP_TRAIN}" -eq 1 ]] && ! point_cloud_exists "${desired_model_path}"; then
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "failed" "${device}" "${desired_model_path}" "${missing}" >> "${ROWS_TSV}"
        job_index=$((job_index + 1))
        continue
      fi

      if run_job "${dataset_name}" "${scene}" "${source_dir}" "${variant}" "${seed}" "${device}" "${desired_model_path}"; then
        if [[ "${DRY_RUN}" -eq 1 ]]; then
          printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "planned" "${device}" "${desired_model_path}" "${missing}" >> "${ROWS_TSV}"
        elif job_complete "${desired_model_path}"; then
          printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "completed" "${device}" "${desired_model_path}" "" >> "${ROWS_TSV}"
        else
          printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "failed" "${device}" "${desired_model_path}" "$(missing_artifacts "${desired_model_path}")" >> "${ROWS_TSV}"
        fi
      else
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset_name}" "${scene}" "${variant}" "${seed}" "failed" "${device}" "${desired_model_path}" "$(missing_artifacts "${desired_model_path}")" >> "${ROWS_TSV}"
      fi
      job_index=$((job_index + 1))
    done
  done
done < "${SCENES_TSV}"

write_status "${ROWS_TSV}"

echo "Status JSON: ${OUTPUT_ROOT}/full_dataset_run_status.json"
echo "Status MD: ${OUTPUT_ROOT}/full_dataset_run_status.md"
echo "Note: teapot/toaster/car remain subset evidence only unless all required datasets are completed."
