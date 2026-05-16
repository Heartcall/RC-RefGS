#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data/liuly/dataset/3DGS/refnerf}"
OUT_ROOT="${OUT_ROOT:-output/rc_refgs}"
ENV_NAME="${ENV_NAME:-ref_gs}"
ITERATIONS="${ITERATIONS:-31000}"
LAMBDA_RC="${LAMBDA_RC:-0.02}"
RC_START="${RC_START:-3000}"
CUDA_DEVICE="${CUDA_DEVICE:-${CUDA_VISIBLE_DEVICES:-2}}"
SCENES=(teapot toaster car)

mkdir -p "${OUT_ROOT}"

for scene in "${SCENES[@]}"; do
  src_path="${DATA_ROOT}/${scene}"
  base_model="${OUT_ROOT}/${scene}_base"
  rc_model="${OUT_ROOT}/${scene}_rc"

  echo "[${scene}] baseline run -> ${base_model}"
  conda run -n "${ENV_NAME}" python train.py \
    --cuda_device "${CUDA_DEVICE}" \
    -s "${src_path}" \
    -m "${base_model}" \
    --iterations "${ITERATIONS}"

  echo "[${scene}] RC run -> ${rc_model}"
  conda run -n "${ENV_NAME}" python train.py \
    --cuda_device "${CUDA_DEVICE}" \
    -s "${src_path}" \
    -m "${rc_model}" \
    --iterations "${ITERATIONS}" \
    --lambda_ref_consistency "${LAMBDA_RC}" \
    --ref_consistency_start "${RC_START}"

  echo "[${scene}] evaluate baseline"
  conda run -n "${ENV_NAME}" python metrics/reflection_consistency_eval.py \
    --cuda_device "${CUDA_DEVICE}" \
    --model_path "${base_model}" \
    --source_path "${src_path}" \
    --iteration "${ITERATIONS}" \
    --split test \
    --output_json "${base_model}/reflection_metrics.json"

  echo "[${scene}] evaluate RC"
  conda run -n "${ENV_NAME}" python metrics/reflection_consistency_eval.py \
    --cuda_device "${CUDA_DEVICE}" \
    --model_path "${rc_model}" \
    --source_path "${src_path}" \
    --iteration "${ITERATIONS}" \
    --split test \
    --output_json "${rc_model}/reflection_metrics.json"
done
