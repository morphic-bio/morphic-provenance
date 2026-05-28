# MSK 40KO packet provenance

Created: 2026-05-28T18:27:08Z

## Source production run

- STAR-suite production output: `/mnt/pikachu/MSK_40KO_processed/msk40ko_prod_20260521T232456Z_setsid`
- Canonical provenance run record: `/mnt/pikachu/morphic-provenance/runs/msk_40ko/20260521T232456Z_star_suite_production`
- STAR-suite commit at packet creation: `7698a7a0660526440662286827b329c745d372c7`
- morphic-recipes commit at packet creation: `c41c2fd11f9bedd0f8b2b6e81a726a9da12b5d0f`
- morphic-provenance commit at packet creation: `e41760a60cbbd260663048b3ac197d5800759c0f`

## Packet layout

The packet mirrors the MSK 30KO revised old-layout Globus packet. For each 40KO sample, `counts.h5ad` is the final downstream AnnData output and the `QC/counts` folder contains the gene quantile QC plots. Feature h5ads are retained under `features/gene` and `features/larry`.

## File mapping

See `STAGED_MANIFEST.tsv` for the exact packet path to processing source mapping.

## Exclusions

FASTQs, BAMs, raw MEX matrices, CellBender raw h5 payloads, CellBender checkpoints, posterior h5 files, runtime caches, and temporary logs are not part of this compact collaborator packet.
