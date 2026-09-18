#!/usr/bin/env bash
set -euo pipefail

readonly prefix="msk-cardiac-workbench-20260918T213950Z"
systemctl --user stop \
  "${prefix}-workbench.service" \
  "${prefix}-scheduler-api.service" \
  "${prefix}-gpu.service" \
  "${prefix}-slurm.service" \
  "${prefix}-control.service"
