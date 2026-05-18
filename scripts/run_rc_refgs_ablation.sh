#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data/liuly/dataset/3DGS/refnerf}"
OUT_ROOT="${OUT_ROOT:-output/rc_refgs}"
ENV_NAME="${ENV_NAME:-ref_gs}"
ITERATIONS="${ITERATIONS:-31000}"
LAMBDA_RC="${LAMBDA_RC:-0.02}"
RC_START="${RC_START:-3000}"
RC_EVERY="${RC_EVERY:-4}"
RC_MAX_ANGLE="${RC_MAX_ANGLE:-20.0}"
RC_GAMMA="${RC_GAMMA:-2.0}"
WO_CONF_GAMMA="${WO_CONF_GAMMA:-0.0}"
ROUGHNESS_SMOOTH_LAMBDA="${ROUGHNESS_SMOOTH_LAMBDA:-0.02}"
ROUGHNESS_SMOOTH_START="${ROUGHNESS_SMOOTH_START:-3000}"
MAX_PAIRS="${MAX_PAIRS:-10}"
CUDA_DEVICE="${CUDA_DEVICE:-${CUDA_VISIBLE_DEVICES:-2}}"
export -n CUDA_DEVICE
SCENES=(teapot toaster car)
VARIANTS=(base rc wo_ref wo_conf rough_only)
SCENE_LIST="${SCENE_LIST:-}"

mkdir -p "${OUT_ROOT}"

if [[ -n "${SCENE_LIST}" ]]; then
  read -r -a scenes <<< "${SCENE_LIST}"
else
  scenes=("${SCENES[@]}")
fi

for scene in "${scenes[@]}"; do
  src_path="${DATA_ROOT}/${scene}"
  base_model="${OUT_ROOT}/${scene}_base"
  rc_model="${OUT_ROOT}/${scene}_rc"
  for variant in "${VARIANTS[@]}"; do
    model="${OUT_ROOT}/${scene}_${variant}"
    train_args=(
      --cuda_device "${CUDA_DEVICE}"
      -s "${src_path}"
      -m "${model}"
      --eval
      --iterations "${ITERATIONS}"
    )
    eval_gamma="${RC_GAMMA}"

    case "${variant}" in
      base)
        eval_gamma="${RC_GAMMA}"
        ;;
      rc)
        train_args+=(
          --lambda_ref_consistency "${LAMBDA_RC}"
          --ref_consistency_start "${RC_START}"
          --ref_consistency_every "${RC_EVERY}"
          --ref_consistency_max_angle "${RC_MAX_ANGLE}"
          --ref_consistency_gamma "${RC_GAMMA}"
        )
        ;;
      wo_ref)
        train_args+=(
          --lambda_ref_consistency 0.0
          --ref_consistency_start "${RC_START}"
          --ref_consistency_every "${RC_EVERY}"
          --ref_consistency_max_angle "${RC_MAX_ANGLE}"
          --ref_consistency_gamma "${RC_GAMMA}"
        )
        ;;
      wo_conf)
        eval_gamma="${WO_CONF_GAMMA}"
        train_args+=(
          --lambda_ref_consistency "${LAMBDA_RC}"
          --ref_consistency_start "${RC_START}"
          --ref_consistency_every "${RC_EVERY}"
          --ref_consistency_max_angle "${RC_MAX_ANGLE}"
          --ref_consistency_gamma "${WO_CONF_GAMMA}"
        )
        ;;
      rough_only)
        train_args+=(
          --lambda_ref_consistency 0.0
          --lambda_roughness_smoothness "${ROUGHNESS_SMOOTH_LAMBDA}"
          --roughness_smoothness_start "${ROUGHNESS_SMOOTH_START}"
        )
        ;;
      *)
        echo "Unknown variant: ${variant}" >&2
        exit 1
        ;;
    esac

    echo "[${scene}] ${variant} run -> ${model}"
    conda run -n "${ENV_NAME}" python train.py "${train_args[@]}"

    for split in train test; do
      echo "[${scene}] evaluate ${variant} ${split}"
      conda run -n "${ENV_NAME}" python metrics/reflection_consistency_eval.py \
        --cuda_device "${CUDA_DEVICE}" \
        --model_path "${model}" \
        --source_path "${src_path}" \
        --iteration "${ITERATIONS}" \
        --split "${split}" \
        --max_pairs "${MAX_PAIRS}" \
        --max_angle_deg "${RC_MAX_ANGLE}" \
        --gamma "${eval_gamma}" \
        --output_json "${model}/reflection_consistency_${split}.json"
    done
  done
done
