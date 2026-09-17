# Logs

Slurm logs remain outside Git at:

```text
/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/
```

The failed first array logs are named
`msk-cardiac-prod-46249747_<task>.{out,err}`. Corrected production logs use
`46251625` for CP_A1 and `46251626` for the remaining captures. Node-local
cleanup logs are `cleanup-r225-46251631.out` and
`cleanup-r203-46251632.out`.

The downstream orchestrator log is local at:

```text
/mnt/pikachu/MSK_Perturbseq06_Cardiac_20260917/logs/downstream_orchestrator.log
```
