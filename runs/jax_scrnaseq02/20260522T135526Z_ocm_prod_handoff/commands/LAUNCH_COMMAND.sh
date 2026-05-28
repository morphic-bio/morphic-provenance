#!/usr/bin/env bash
set -uo pipefail
unset SKIP_REMAINING_STAR
cd /mnt/pikachu/STAR-suite
export BATCH_ROOT="/mnt/pikachu/JAX_scRNAseq02_processed/ocm_prod_batch_flex_native_yremove_trace_20260521T034223Z"
export THREADS=16
export FIRST_RUN_ROOT=""
export SKIP_FIRST_POST=1
export SRC_EP="07446cad-33b8-11f0-8c0c-0afffb017b7d"
export DST_EP="61fb8b9a-9b52-456e-928c-30c0fb0140bf"
export DST_PREFIX="/JAX_scRNAseq02_processed/large_files"
export REMOTE_HOST="10.159.4.53"
export REMOTE_ROOT="/home/lhhung/jax_scrnaseq02_remote_downstream"
export DOWNSTREAM_NAME="downstream_genefull_velocyto_cellbender_remote"
set -x
bash -x scripts/run_jax_scrnaseq02_ocm_production_batch.sh
rc=$?
set +x
echo "LAUNCH_EXIT_RC=${rc}"
exit "${rc}"
