# Environment

- Bridges-2 account: `bio230034p`
- Slurm partition: `RM-shared`
- Pilot: two one-element array submissions on distinct nodes; 64 allocated
  CPUs and 120 GB each; STAR uses 32 threads
- Gather: 8 CPUs and 8 GB
- Prepared production: eight array tasks, 64 CPUs and 120 GB each; STAR uses
  64 threads; maximum concurrency 1
- STAR Suite: v1.9.4 commit
  `1c9ddb9a5a2a3e62748e8e4ef28e553582affeed`
- Bridges binary: clean `WITH_CHROMAP=0` build from the pinned source archive,
  with bundled-HTSlib and duplicate-BGZF portable-link adjustments
- Pikachu binary: independent clean build from the same archive
- Input mode: native gzip, no `--readFilesCommand`, no transcode
- CellBender: not run in this pilot; future production use requires CUDA
- zshard: prohibited and unused

Build manifests are saved as `BRIDGES_BUILD_MANIFEST.txt` and
`PIKACHU_BUILD_MANIFEST.txt` in this directory.
