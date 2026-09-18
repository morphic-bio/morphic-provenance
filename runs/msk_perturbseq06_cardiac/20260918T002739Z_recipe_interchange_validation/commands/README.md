# Commands

```bash
python3 commands/build_and_validate.py \
  --adapter-repo /mnt/pikachu/bwb-nextflow-utils-staged-recipe-20260918 \
  --prior-run ../20260917T193023Z_temporal_staged_pilot \
  --run-dir .
```

This is a rendering and validation command only. It does not submit the
generated request.

Validate the generated request with the pinned scheduler parser:

```bash
TEMPORAL_ENDPOINT_URL=localhost:7233 \
  /mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917/.venv/bin/python \
  commands/validate_scheduler_payload.py \
  --scheduler-repo /mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917 \
  --request outputs/scheduler-request.dry-run.json \
  --output outputs/scheduler-parser-validation.json
```
