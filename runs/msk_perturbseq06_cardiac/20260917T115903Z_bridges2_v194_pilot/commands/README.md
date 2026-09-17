# Commands

Run order:

1. `prepare_inputs.sh`
2. `build_star_v194.sbatch`
3. `run_two_capture_pilot.sbatch` as two one-element submissions (`0` and `1`)
4. `gather_two_node_pilot.sbatch` with `afterok` dependencies on both tasks
5. `run_pikachu_control.sh` on Pikachu
6. `guide_mex_semantic_digest.py` on each host
7. `compare_pilot_hosts.py` after retrieving the Bridges reports

`submit_pilot.sh` submits steps 1-4 and records the Slurm job IDs. It does not
submit `run_cardiac_production_array.sbatch`.

Accepted jobs: build `46246773`, CP_R1 `46246783` on `r039`, CP_R2
`46246784` on `r067`, and gather `46246785`. Production was not submitted.
