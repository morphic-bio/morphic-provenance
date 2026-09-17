# Handoff

No release packet is created until both upstream and downstream validation
pass. Accepted upstream outputs are written to Ocean under
`results/production/<capture>/`; downstream H5AD/QC outputs are checksum-returned
to `results/downstream/<capture>/`.

The H5AD pipeline includes CellBender and Velocyto but intentionally omits
Scimilarity/cell-type labels. CellBender must run with CUDA; the orchestrator
records the rendered `--cellbender-gpu`/`--cuda` command and `nvidia-smi` audit.
