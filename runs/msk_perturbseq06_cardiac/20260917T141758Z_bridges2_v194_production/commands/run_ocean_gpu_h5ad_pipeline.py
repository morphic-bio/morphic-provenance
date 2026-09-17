#!/usr/bin/env python3
"""Move completed Ocean captures through H5AD/QC and CUDA CellBender stages."""

from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


CAPTURES = ("CP_A1", "CP_A2", "CP_A3", "CP_B1", "CP_B2", "CP_B3", "CP_R1", "CP_R2")
BRIDGES_ENDPOINT = "d9e522d3-c51e-4037-b375-55ffd155c715"
PIKACHU_ENDPOINT = "07446cad-33b8-11f0-8c0c-0afffb017b7d"
EXPECTED_RECIPES_COMMIT = "e27f1745bf3d59aaf71cc0301b2f31845c759180"
CELLBENDER_IMAGE = "biodepot/cellbender:0.3.2"
CELLBENDER_IMAGE_ID = "sha256:f31f1e993f3d87659c3dd541a22f505fec7ee4366f6d5da1324061c2c09dcb2a"
TRANSFER_ITEMS = (
    ("UPSTREAM_COMPLETE.txt", False),
    ("RUN_COMMAND.sh", False),
    ("stage.tsv", False),
    ("time.txt", False),
    ("run/outs", True),
    ("run/cr_assign", True),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ocean-run-root",
        type=Path,
        default=Path("/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917"),
    )
    parser.add_argument(
        "--local-root",
        type=Path,
        default=Path("/mnt/pikachu/MSK_Perturbseq06_Cardiac_20260917"),
    )
    parser.add_argument(
        "--recipes-root",
        type=Path,
        default=Path("/mnt/pikachu/morphic-recipes-msk-cardiac-e27f174"),
    )
    parser.add_argument("--bridges-host", default="bridges2")
    parser.add_argument("--gpu-host", default="10.159.4.53")
    parser.add_argument("--gpu-root", default="/tmp/msk_perturbseq06_cardiac_cellbender")
    parser.add_argument("--gpu-slots", default="0,1")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-wait-hours", type=float, default=240.0)
    parser.add_argument("--min-free-gib", type=int, default=1024)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


class Pipeline:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.local_root = args.local_root.resolve()
        self.samples_root = self.local_root / "samples"
        self.logs_root = self.local_root / "logs"
        self.transfers_root = self.local_root / "transfers"
        self.ocean_production = args.ocean_run_root / "results/production"
        self.ocean_downstream = args.ocean_run_root / "results/downstream"
        self.validator = Path(__file__).with_name("validate_cardiac_h5ads.py").resolve()
        self.globus = Path("/home/lhhung/.local/bin/globus")
        self.ledger = self.local_root / "PIPELINE_STATUS.tsv"
        self.lock_handle = None
        self.write_lock = threading.Lock()

    def acquire_lock(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        lock_path = self.local_root / "pipeline.lock"
        self.lock_handle = lock_path.open("w")
        try:
            fcntl.flock(self.lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"another Cardiac downstream orchestrator holds {lock_path}") from exc
        self.lock_handle.write(f"pid={os.getpid()}\nstarted_utc={utc_now()}\n")
        self.lock_handle.flush()

    def record(self, capture: str, stage: str, status: str, detail: str = "") -> None:
        clean_detail = detail.replace("\t", " ").replace("\n", " ")
        with self.write_lock:
            new_file = not self.ledger.exists()
            with self.ledger.open("a") as handle:
                if new_file:
                    handle.write("timestamp_utc\tcapture\tstage\tstatus\tdetail\n")
                handle.write(f"{utc_now()}\t{capture}\t{stage}\t{status}\t{clean_detail}\n")

    @staticmethod
    def run(
        argv: list[str],
        *,
        check: bool = True,
        capture_output: bool = False,
        log_path: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as handle:
                handle.write(f"\n[{utc_now()}] COMMAND {json.dumps(argv)}\n")
                handle.flush()
                return subprocess.run(argv, check=check, text=True, stdout=handle, stderr=subprocess.STDOUT)
        return subprocess.run(
            argv,
            check=check,
            text=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
        )

    def ssh(self, host: str, *remote_argv: str, **kwargs) -> subprocess.CompletedProcess[str]:
        remote_command = shlex.join(remote_argv)
        return self.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=20",
                "-o",
                "StrictHostKeyChecking=accept-new",
                host,
                remote_command,
            ],
            **kwargs,
        )

    def preflight(self) -> None:
        self.acquire_lock()
        self.samples_root.mkdir(parents=True, exist_ok=True)
        self.logs_root.mkdir(parents=True, exist_ok=True)
        self.transfers_root.mkdir(parents=True, exist_ok=True)
        required = [
            self.globus,
            self.validator,
            self.args.recipes_root / "scripts/run_scrna_downstream_gene_full_velocyto.sh",
            self.args.recipes_root / "scripts/run_remote_cellbender_rsync.sh",
            Path("/mnt/pikachu/scRNA-seq/utilities/inspect_anndata.py"),
        ]
        for path in required:
            if not path.exists():
                raise RuntimeError(f"missing required path: {path}")
        for executable in ("ssh", "docker", "python3", "rsync"):
            if shutil.which(executable) is None:
                raise RuntimeError(f"missing required executable: {executable}")

        commit = self.run(
            ["git", "-C", str(self.args.recipes_root), "rev-parse", "HEAD"],
            capture_output=True,
        ).stdout.strip()
        if commit != EXPECTED_RECIPES_COMMIT:
            raise RuntimeError(f"recipe checkout is {commit}, expected {EXPECTED_RECIPES_COMMIT}")
        dirty = self.run(
            ["git", "-C", str(self.args.recipes_root), "status", "--porcelain"],
            capture_output=True,
        ).stdout.strip()
        if dirty:
            raise RuntimeError(f"recipe checkout is dirty: {dirty}")

        local_endpoint = self.run(
            [str(self.globus), "endpoint", "local-id"], capture_output=True
        ).stdout.strip()
        if local_endpoint != PIKACHU_ENDPOINT:
            raise RuntimeError(f"wrong local Globus endpoint: {local_endpoint}")
        self.run(
            [str(self.globus), "ls", f"{BRIDGES_ENDPOINT}:{self.args.ocean_run_root}/"],
            capture_output=True,
        )
        self.run(
            [str(self.globus), "ls", f"{PIKACHU_ENDPOINT}:{self.local_root}/"],
            capture_output=True,
        )

        free_gib = shutil.disk_usage(self.local_root).free // (1024**3)
        if free_gib < self.args.min_free_gib:
            raise RuntimeError(f"only {free_gib} GiB free under {self.local_root}")

        image_ids = {}
        for image in (
            "biodepot/scrna-matrices:latest",
            "biodepot/gather_features:latest",
            CELLBENDER_IMAGE,
        ):
            image_id = self.run(
                ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
                capture_output=True,
            ).stdout.strip()
            image_ids[image] = image_id
        if image_ids[CELLBENDER_IMAGE] != CELLBENDER_IMAGE_ID:
            raise RuntimeError(f"unexpected local CellBender image: {image_ids[CELLBENDER_IMAGE]}")

        gpu_audit = self.ssh(
            self.args.gpu_host,
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            CELLBENDER_IMAGE,
            "python",
            "-c",
            "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.device_count())",
            capture_output=True,
        )
        gpu_lines = gpu_audit.stdout.strip().splitlines()
        if len(gpu_lines) < 3 or gpu_lines[-2:] != ["True", "2"]:
            raise RuntimeError(f"remote CUDA preflight failed: {gpu_audit.stdout} {gpu_audit.stderr}")

        report = {
            "status": "PASS",
            "timestamp_utc": utc_now(),
            "recipes_commit": commit,
            "globus": {
                "bridges_endpoint": BRIDGES_ENDPOINT,
                "pikachu_endpoint": PIKACHU_ENDPOINT,
            },
            "local_free_gib": free_gib,
            "docker_images": image_ids,
            "gpu_host": self.args.gpu_host,
            "gpu_cuda_probe": gpu_lines,
            "scimilarity_run": False,
        }
        (self.local_root / "PREFLIGHT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        self.record("PROJECT", "preflight", "PASS", f"free_gib={free_gib}")

    def remote_upstream_complete(self, capture: str) -> bool:
        marker = self.ocean_production / capture / "UPSTREAM_COMPLETE.txt"
        result = self.ssh(self.args.bridges_host, "test", "-s", str(marker), check=False)
        return result.returncode == 0

    def remote_downstream_complete(self, capture: str) -> bool:
        marker = self.ocean_downstream / capture / "DOWNSTREAM_COMPLETE.json"
        result = self.ssh(self.args.bridges_host, "test", "-s", str(marker), check=False)
        return result.returncode == 0

    def submit_globus(
        self,
        capture: str,
        direction: str,
        source_endpoint: str,
        destination_endpoint: str,
        batch_lines: list[str],
    ) -> str:
        transfer_dir = self.transfers_root / capture
        transfer_dir.mkdir(parents=True, exist_ok=True)
        batch_path = transfer_dir / f"{direction}_batch.tsv"
        submission_path = transfer_dir / f"{direction}_submission.json"
        final_path = transfer_dir / f"{direction}_final.json"
        batch_path.write_text("".join(f"{line}\n" for line in batch_lines))
        command = [
            str(self.globus),
            "transfer",
            source_endpoint,
            destination_endpoint,
            "--batch",
            str(batch_path),
            "--sync-level",
            "checksum",
            "--verify-checksum",
            "--preserve-mtime",
            "--notify",
            "off",
            "--label",
            f"MSK Cardiac {direction} {capture}",
            "--format",
            "json",
        ]
        result = self.run(command, capture_output=True)
        submission_path.write_text(result.stdout)
        task_id = json.loads(result.stdout)["task_id"]
        self.record(capture, direction, "SUBMITTED", task_id)
        self.run(
            [str(self.globus), "task", "wait", "--polling-interval", "30", task_id],
        )
        final = self.run(
            [str(self.globus), "task", "show", task_id, "--format", "json"],
            capture_output=True,
        )
        final_path.write_text(final.stdout)
        status = json.loads(final.stdout).get("status")
        if status != "SUCCEEDED":
            raise RuntimeError(f"Globus task {task_id} ended with status {status}")
        self.record(capture, direction, "PASS", task_id)
        return task_id

    def pull_upstream(self, capture: str) -> Path:
        sample_root = self.samples_root / capture
        pull_marker = sample_root / "OCEAN_PULL_COMPLETE.json"
        if pull_marker.is_file():
            return sample_root
        if sample_root.exists():
            raise RuntimeError(f"incomplete local sample directory requires review: {sample_root}")

        partial = self.samples_root / f".{capture}.incoming"
        if partial.exists():
            shutil.rmtree(partial)
        partial.mkdir(parents=True)
        source_root = self.ocean_production / capture
        batch_lines = []
        for relative, recursive in TRANSFER_ITEMS:
            source = source_root / relative
            destination = partial / relative
            prefix = "--recursive " if recursive else ""
            batch_lines.append(f"{prefix}{source}\t{destination}")
        task_id = self.submit_globus(
            capture,
            "ocean_to_pikachu",
            BRIDGES_ENDPOINT,
            PIKACHU_ENDPOINT,
            batch_lines,
        )
        required = [
            partial / "UPSTREAM_COMPLETE.txt",
            partial / "RUN_COMMAND.sh",
            partial / "run/outs/filtered_feature_bc_matrix/matrix.mtx.gz",
            partial / "run/outs/raw_feature_bc_matrix/matrix.mtx.gz",
            partial / "run/outs/raw_velocyto_feature_bc_matrix/matrix.mtx.gz",
            partial / "run/outs/crispr_analysis/protospacer_calls_per_cell.csv",
        ]
        for path in required:
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"download task {task_id} omitted required file: {path}")
        marker = {
            "status": "PASS",
            "capture": capture,
            "completed_utc": utc_now(),
            "globus_task_id": task_id,
            "source": str(source_root),
            "destination": str(sample_root),
        }
        (partial / "OCEAN_PULL_COMPLETE.json").write_text(json.dumps(marker, indent=2) + "\n")
        partial.rename(sample_root)
        return sample_root

    def prepare_h5ads(self, capture: str, sample_root: Path) -> Path:
        downstream = sample_root / "downstream_genefull_velocyto_cellbender"
        marker = downstream / "PREP_COMPLETE.json"
        if marker.is_file():
            return downstream
        log_path = sample_root / "downstream_prepare.log"
        command = [
            str(self.args.recipes_root / "scripts/run_scrna_downstream_gene_full_velocyto.sh"),
            "--run-dir",
            str(sample_root / "run"),
            "--output-dir",
            str(downstream),
            "--adaptive-filter",
            "--min-genes",
            "200",
            "--mt-pct-cutoff",
            "5",
            "--n-mad",
            "3",
        ]
        self.record(capture, "h5ad_prepare", "START")
        self.run(command, log_path=log_path)
        required = (
            "counts.h5ad",
            "unfiltered_counts.h5ad",
            "filtered_counts.h5ad",
            "default_singlet_filtered_counts.h5ad",
            "adaptive_qc_threshold.json",
        )
        for name in required:
            path = downstream / name
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"downstream preparation omitted {path}")
        marker.write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "capture": capture,
                    "completed_utc": utc_now(),
                    "adaptive_filter": True,
                    "n_mad": 3,
                    "mt_pct_floor": 5,
                    "min_genes": 200,
                    "scimilarity_run": False,
                },
                indent=2,
            )
            + "\n"
        )
        self.record(capture, "h5ad_prepare", "PASS")
        return downstream

    def run_cellbender(self, capture: str, downstream: Path, gpu_slot: str) -> None:
        marker = downstream / "CELLBENDER_CUDA_COMPLETE.json"
        if marker.is_file():
            return
        driver_log = downstream / "remote_cellbender_driver.log"
        gpu_audit = downstream / "cellbender_gpu_audit.log"
        command = [
            str(self.args.recipes_root / "scripts/run_remote_cellbender_rsync.sh"),
            "--downstream-dir",
            str(downstream),
            "--remote-host",
            self.args.gpu_host,
            "--remote-root",
            self.args.gpu_root,
            "--cellbender-image",
            CELLBENDER_IMAGE,
            "--cellbender-gpu",
            "--cellbender-gpu-device",
            gpu_slot,
            "--cellbender-cpu-cores",
            "8",
            "--cellbender-layer",
            "denoised",
            "--no-sync-image",
        ]
        (downstream / "CELLBENDER_COMMAND.json").write_text(json.dumps(command, indent=2) + "\n")
        self.record(capture, "cellbender_cuda", "START", f"gpu={gpu_slot}")
        observed_gpu = False
        with driver_log.open("a") as log:
            log.write(f"[{utc_now()}] COMMAND {json.dumps(command)}\n")
            log.flush()
            process = subprocess.Popen(command, text=True, stdout=log, stderr=subprocess.STDOUT)
            while process.poll() is None:
                query = self.ssh(
                    self.args.gpu_host,
                    "nvidia-smi",
                    "-i",
                    gpu_slot,
                    "--query-compute-apps=pid,process_name,used_memory",
                    "--format=csv,noheader,nounits",
                    check=False,
                    capture_output=True,
                )
                line = query.stdout.strip()
                with gpu_audit.open("a") as audit:
                    audit.write(f"{utc_now()}\tGPU={gpu_slot}\t{line or 'no_compute_process'}\n")
                if line and "python" in line.lower():
                    observed_gpu = True
                time.sleep(30)
            return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"CellBender helper failed for {capture} with rc={return_code}")
        cb_h5 = downstream / "cellbender/cellbender_counts.h5"
        failure = downstream / "cellbender/CELLBENDER_FAILED.txt"
        if failure.exists() or not cb_h5.is_file() or cb_h5.stat().st_size == 0:
            raise RuntimeError(f"CellBender did not produce a valid CUDA output for {capture}")
        if not observed_gpu:
            raise RuntimeError(f"nvidia-smi did not observe CellBender on GPU {gpu_slot}")
        marker.write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "capture": capture,
                    "completed_utc": utc_now(),
                    "gpu_host": self.args.gpu_host,
                    "gpu_device": gpu_slot,
                    "cuda": True,
                    "nvidia_smi_process_observed": observed_gpu,
                    "image": CELLBENDER_IMAGE,
                    "image_id": CELLBENDER_IMAGE_ID,
                    "layer": "denoised",
                },
                indent=2,
            )
            + "\n"
        )
        self.record(capture, "cellbender_cuda", "PASS", f"gpu={gpu_slot}")

    def validate_h5ads(self, capture: str, downstream: Path) -> None:
        report = downstream / "DOWNSTREAM_VALIDATION.json"
        self.record(capture, "h5ad_validation", "START")
        self.run(
            [
                sys.executable,
                str(self.validator),
                "--downstream-dir",
                str(downstream),
                "--capture",
                capture,
                "--output",
                str(report),
            ],
            log_path=downstream / "downstream_validation.log",
        )
        result = json.loads(report.read_text())
        if result.get("status") != "PASS":
            raise RuntimeError(f"downstream validation failed for {capture}")
        self.record(capture, "h5ad_validation", "PASS")

    @staticmethod
    def write_checksums(downstream: Path) -> Path:
        output = downstream / "CHECKSUMS.sha256"
        paths = sorted(
            path for path in downstream.rglob("*") if path.is_file() and path != output
        )
        with output.open("w") as handle:
            for path in paths:
                digest = hashlib.sha256()
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(16 * 1024 * 1024), b""):
                        digest.update(chunk)
                handle.write(f"{digest.hexdigest()}  {path.relative_to(downstream)}\n")
        return output

    def upload_downstream(self, capture: str, downstream: Path) -> str:
        if self.remote_downstream_complete(capture):
            return "existing"
        self.record(capture, "checksums", "START")
        self.write_checksums(downstream)
        self.record(capture, "checksums", "PASS")
        remote_partial = self.ocean_downstream / f".{capture}.partial"
        remote_final = self.ocean_downstream / capture
        exists = self.ssh(self.args.bridges_host, "test", "-e", str(remote_final), check=False)
        if exists.returncode == 0:
            raise RuntimeError(f"Ocean destination exists without completion marker: {remote_final}")
        self.ssh(self.args.bridges_host, "rm", "-rf", str(remote_partial))
        batch_lines = [f"--recursive {downstream}/\t{remote_partial}/"]
        task_id = self.submit_globus(
            capture,
            "pikachu_to_ocean",
            PIKACHU_ENDPOINT,
            BRIDGES_ENDPOINT,
            batch_lines,
        )
        finalize_script = r'''
set -euo pipefail
partial="$1"
final="$2"
capture="$3"
task_id="$4"
test -s "${partial}/DOWNSTREAM_VALIDATION.json"
test -s "${partial}/CHECKSUMS.sha256"
test -s "${partial}/counts.h5ad"
test -s "${partial}/filtered_counts.h5ad"
test -s "${partial}/final_counts.h5ad"
test ! -e "${final}"
python3.11 - "${partial}/DOWNSTREAM_COMPLETE.json" "${capture}" "${task_id}" <<'PY'
import json, sys
from datetime import datetime, timezone
path, capture, task_id = sys.argv[1:]
payload = {
    "status": "PASS",
    "capture": capture,
    "completed_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "globus_task_id": task_id,
    "cellbender_cuda": True,
    "adaptive_mt_filter": True,
    "scimilarity_run": False,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
mv "${partial}" "${final}"
'''
        finalized = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=20",
                self.args.bridges_host,
                "bash",
                "-s",
                "--",
                str(remote_partial),
                str(remote_final),
                capture,
                task_id,
            ],
            input=finalize_script,
            text=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if finalized.returncode != 0:
            raise RuntimeError(f"Ocean finalize failed: {finalized.stderr}")
        if not self.remote_downstream_complete(capture):
            raise RuntimeError(f"Ocean completion marker is missing for {capture}")
        return task_id

    def process_capture(self, capture: str, gpu_slot: str) -> str:
        try:
            if self.remote_downstream_complete(capture):
                self.record(capture, "pipeline", "SKIP", "Ocean output already complete")
                return "existing"
            self.record(capture, "pipeline", "START", f"gpu={gpu_slot}")
            sample_root = self.pull_upstream(capture)
            downstream = self.prepare_h5ads(capture, sample_root)
            self.run_cellbender(capture, downstream, gpu_slot)
            self.validate_h5ads(capture, downstream)
            task_id = self.upload_downstream(capture, downstream)
            run_dir = sample_root / "run"
            if run_dir.exists():
                shutil.rmtree(run_dir)
                (sample_root / "STAGED_UPSTREAM_INPUTS_REMOVED.txt").write_text(
                    f"removed_utc={utc_now()}\nreason=verified Ocean source retained and downstream returned to Ocean\n"
                )
            state = {
                "status": "PASS",
                "capture": capture,
                "completed_utc": utc_now(),
                "gpu_device": gpu_slot,
                "ocean_transfer_task_id": task_id,
                "ocean_output": str(self.ocean_downstream / capture),
                "local_output": str(downstream),
                "scimilarity_run": False,
            }
            (sample_root / "PIPELINE_COMPLETE.json").write_text(
                json.dumps(state, indent=2, sort_keys=True) + "\n"
            )
            self.record(capture, "pipeline", "PASS", f"ocean_task={task_id}")
            return task_id
        except Exception as exc:
            self.record(capture, "pipeline", "FAIL", repr(exc))
            raise

    def wait_for_upstream(self, capture: str, deadline: float) -> None:
        while not self.remote_upstream_complete(capture):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for upstream capture {capture}")
            time.sleep(self.args.poll_seconds)

    def execute(self) -> None:
        deadline = time.monotonic() + self.args.max_wait_hours * 3600

        # Gate the remaining set on one complete full-data H5AD/CellBender pass.
        first = CAPTURES[0]
        if not self.remote_downstream_complete(first):
            self.record(first, "upstream_wait", "START")
            self.wait_for_upstream(first, deadline)
            self.record(first, "upstream_wait", "PASS")
            self.process_capture(first, "0")

        remaining = list(CAPTURES[1:])
        done = {first}
        failed: dict[str, str] = {}
        slots = [slot.strip() for slot in self.args.gpu_slots.split(",") if slot.strip()]
        if not slots:
            raise ValueError("--gpu-slots must contain at least one GPU device")
        available_slots = set(slots)
        active: dict[concurrent.futures.Future[str], tuple[str, str]] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(slots)) as executor:
            while len(done) + len(failed) < len(CAPTURES):
                for future in list(active):
                    if not future.done():
                        continue
                    capture, slot = active.pop(future)
                    available_slots.add(slot)
                    try:
                        future.result()
                        done.add(capture)
                    except Exception as exc:
                        failed[capture] = repr(exc)

                for capture in list(remaining):
                    if not available_slots:
                        break
                    if self.remote_downstream_complete(capture):
                        remaining.remove(capture)
                        done.add(capture)
                        self.record(capture, "pipeline", "SKIP", "Ocean output already complete")
                        continue
                    if not self.remote_upstream_complete(capture):
                        continue
                    slot = sorted(available_slots)[0]
                    available_slots.remove(slot)
                    remaining.remove(capture)
                    active[executor.submit(self.process_capture, capture, slot)] = (capture, slot)

                if len(done) + len(failed) == len(CAPTURES):
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out with pending captures: {remaining}")
                time.sleep(self.args.poll_seconds)

        summary = {
            "status": "PASS" if not failed else "FAIL",
            "completed_utc": utc_now(),
            "captures_complete": sorted(done),
            "captures_failed": failed,
            "ocean_output_root": str(self.ocean_downstream),
            "local_output_root": str(self.samples_root),
            "cellbender_cuda": True,
            "adaptive_mt_filter": True,
            "scimilarity_run": False,
        }
        (self.local_root / "PIPELINE_COMPLETE.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        if failed:
            raise RuntimeError(f"downstream failures: {failed}")


def main() -> int:
    args = parse_args()
    pipeline = Pipeline(args)
    pipeline.preflight()
    if args.preflight_only:
        print(f"PASS: preflight recorded at {pipeline.local_root / 'PREFLIGHT.json'}")
        return 0
    pipeline.execute()
    print(f"PASS: all Cardiac downstream outputs are complete under {pipeline.ocean_downstream}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
