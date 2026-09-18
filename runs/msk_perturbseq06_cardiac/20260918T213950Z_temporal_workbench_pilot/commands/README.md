# Commands

Prepare and validate the bundle:

```bash
/mnt/pikachu/.venvs/bwb-workbench-staged/bin/python commands/prepare_workbench.py \
  --adapter-repo /mnt/pikachu/bwb-nextflow-utils-staged-recipe-20260918 \
  --scheduler-repo /mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917 \
  --run-dir "$PWD" \
  --template-run ../20260918T002739Z_recipe_interchange_validation \
  --source-pilot-run ../20260917T193023Z_temporal_staged_pilot
```

Then run `runtime_preflight.sh` once and `start_services.sh`. Starting services
does not submit the workflow. Submission requires explicit approval in the
Workbench. Use `stop_services.sh` when review or execution is complete.
