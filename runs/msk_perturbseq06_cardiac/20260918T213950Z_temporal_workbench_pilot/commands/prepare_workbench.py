#!/usr/bin/env python3
"""Prepare a collision-free Workbench bundle for the CP_R1 Temporal pilot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


RUN_STAMP = "20260918T213950Z"
OLD_LOCAL_ROOT = "/mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_20260917T193023Z"
OLD_OCEAN_ROOT = "/ocean/projects/bio230034p/lhung2/temporal-cardiac-pilot-20260917T193023Z"
OLD_QUEUE = "cardiac-staged-pilot-20260917T193023Z"
NEW_LOCAL_ROOT = f"/mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_workbench_{RUN_STAMP}"
NEW_OCEAN_ROOT = f"/ocean/projects/bio230034p/lhung2/temporal-cardiac-workbench-{RUN_STAMP}"
NEW_QUEUE = f"cardiac-workbench-pilot-{RUN_STAMP}"
WORKFLOW_RUN_ID = f"msk-cardiac-cp-r1-workbench-{RUN_STAMP}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replace_roots(value: Any) -> Any:
    if isinstance(value, str):
        return (
            value.replace(OLD_LOCAL_ROOT, NEW_LOCAL_ROOT)
            .replace(OLD_OCEAN_ROOT, NEW_OCEAN_ROOT)
            .replace(OLD_QUEUE, NEW_QUEUE)
        )
    if isinstance(value, list):
        return [replace_roots(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_roots(item) for key, item in value.items()}
    return value


def checksum_manifest(paths: list[Path], root: Path) -> str:
    rows = ["path\tsha256\tbytes"]
    for path in sorted(paths):
        rows.append(f"{path.relative_to(root)}\t{sha256(path)}\t{path.stat().st_size}")
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-repo", type=Path, required=True)
    parser.add_argument("--scheduler-repo", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--template-run", type=Path, required=True)
    parser.add_argument("--source-pilot-run", type=Path, required=True)
    args = parser.parse_args()

    adapter_repo = args.adapter_repo.resolve()
    scheduler_repo = args.scheduler_repo.resolve()
    run_dir = args.run_dir.resolve()
    template_run = args.template_run.resolve()
    source_pilot_run = args.source_pilot_run.resolve()
    inputs_dir = run_dir / "inputs"
    commands_dir = run_dir / "commands"
    outputs_dir = run_dir / "outputs"
    for directory in (inputs_dir, commands_dir, outputs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(adapter_repo))
    sys.path.insert(0, str(adapter_repo / "tools"))
    from staged_execution_plan import build_staged_recipe_workbench_bundle
    from workbench_bundle import preflight_bundle
    from workbench_temporal_adapter import build_submission_payload

    recipe = replace_roots(read_json(template_run / "inputs/recipe.json"))
    align_ir = replace_roots(read_json(template_run / "inputs/align.ir.json"))
    cellbender_ir = replace_roots(read_json(template_run / "inputs/cellbender.ir.json"))
    executor_profile = replace_roots(read_json(template_run / "inputs/executor-profile.json"))
    recipe_inputs = replace_roots(read_json(template_run / "inputs/recipe-inputs.json"))
    stage_outputs = replace_roots(read_json(template_run / "inputs/stage-outputs.json"))

    source_wrapper = source_pilot_run / "commands/slurm_cardiac_subsample.sh"
    wrapper = commands_dir / "slurm_cardiac_subsample.sh"
    wrapper.write_text(source_wrapper.read_text().replace(OLD_OCEAN_ROOT, NEW_OCEAN_ROOT))
    wrapper.chmod(0o755)
    ocean_wrapper = f"{NEW_OCEAN_ROOT}/input/slurm_cardiac_subsample.sh"

    recipe["metadata"] = {
        **(recipe.get("metadata") or {}),
        "source_template_run": str(template_run),
        "source_execution_evidence": str(source_pilot_run),
        "prepared_run": str(run_dir),
    }
    align_ir.setdefault("annotations", {}).setdefault("provenance", {})[
        "wrapper_sha256"
    ] = sha256(wrapper)
    recipe_inputs["launch_script"] = ocean_wrapper
    stage_outputs["star"]["raw_mex"] = f"{NEW_LOCAL_ROOT}/slurm/raw_feature_bc_matrix"
    stage_outputs["cellbender"]["filtered_h5"] = (
        f"{NEW_LOCAL_ROOT}/gpu/cellbender_counts_filtered.h5"
    )

    executor_profile["name"] = f"pikachu-bridges2-cardiac-workbench-{RUN_STAMP}"
    executor_profile["orchestration"]["task_queue"] = NEW_QUEUE
    executor_profile["globus"]["task_queue"] = NEW_QUEUE
    executor_profile["gpu"]["local_output_dir"] = f"{NEW_LOCAL_ROOT}/gpu"
    for item in executor_profile["transfers"]["stage_in"]["items"]:
        if str(item.get("destination_path", "")).endswith("/slurm_cardiac_subsample.sh"):
            item["source_path"] = str(wrapper)
            item["destination_path"] = ocean_wrapper

    ir_by_id = {
        align_ir["metadata"]["id"]: align_ir,
        cellbender_ir["metadata"]["id"]: cellbender_ir,
    }
    bundle = build_staged_recipe_workbench_bundle(
        recipe,
        workflow_ir_by_id=ir_by_id,
        executor_profile=executor_profile,
        recipe_input_values=recipe_inputs,
        stage_output_values=stage_outputs,
    )
    bundle["form_data"]["execution"]["run_id"] = WORKFLOW_RUN_ID
    bundle["submission_request"]["approval"]["confirmed_by_user"] = False

    preflight = preflight_bundle(bundle)
    approved_copy = copy.deepcopy(bundle)
    approved_copy["submission_request"]["approval"]["confirmed_by_user"] = True
    scheduler_request = build_submission_payload(approved_copy)
    parser_code = (
        "import json,sys; "
        "from bwb.scheduling_service.main import _staged_slurm_gpu_params; "
        "_staged_slurm_gpu_params(json.load(sys.stdin)); print('PASS')"
    )
    parser_env = os.environ.copy()
    parser_env["PYTHONPATH"] = str(scheduler_repo)
    parser_env["TEMPORAL_ENDPOINT_URL"] = "localhost:7233"
    parser_result = subprocess.run(
        [str(scheduler_repo / ".venv/bin/python"), "-c", parser_code],
        input=json.dumps(scheduler_request),
        text=True,
        capture_output=True,
        env=parser_env,
    )
    if parser_result.returncode != 0:
        raise RuntimeError(
            "Scheduler parser rejected request: "
            f"stdout={parser_result.stdout!r} stderr={parser_result.stderr!r}"
        )
    if parser_result.stdout.strip() != "PASS":
        raise RuntimeError(f"Unexpected scheduler parser result: {parser_result.stdout!r}")

    worker_config = {
        "pipeline": {"task_queue": NEW_QUEUE},
        "executors": {
            "globus": {
                "allowed_endpoint_ids": [
                    "07446cad-33b8-11f0-8c0c-0afffb017b7d",
                    "d9e522d3-c51e-4037-b375-55ffd155c715",
                ],
                "cli_path": "/home/lhhung/.local/bin/globus",
            }
        },
    }
    site_config = {
        "executors": {
            "slurm": {
                "ip_addr": "bridges2.psc.edu",
                "port": 22,
                "storage_dir": f"{NEW_OCEAN_ROOT}/scheduler",
                "transfer_addr": "bridges2.psc.edu",
                "transfer_port": 22,
                "user": "lhung2",
            },
            "ssh_docker": {
                "gpu_device": "0",
                "ip_addr": "localhost",
                "port": 22,
                "storage_dir": f"/storage/temporal-scheduler-gpu-cardiac-{RUN_STAMP}",
                "user": "lhhung",
            },
        }
    }

    write_json(inputs_dir / "recipe.json", recipe)
    write_json(inputs_dir / "align.ir.json", align_ir)
    write_json(inputs_dir / "cellbender.ir.json", cellbender_ir)
    write_json(inputs_dir / "executor-profile.json", executor_profile)
    write_json(inputs_dir / "recipe-inputs.json", recipe_inputs)
    write_json(inputs_dir / "stage-outputs.json", stage_outputs)
    write_json(commands_dir / "worker-config.json", worker_config)
    write_json(commands_dir / "site-config.json", site_config)
    write_json(outputs_dir / "workbench-bundle.json", bundle)
    write_json(outputs_dir / "preflight.json", preflight)
    write_json(outputs_dir / "scheduler-request.dry-run.json", scheduler_request)
    wrapper_text = wrapper.read_text()
    validation = {
        "approval_confirmed_in_canonical_bundle": bundle["submission_request"]["approval"]["confirmed_by_user"],
        "cellbender_cuda": "--cuda" in json.dumps(scheduler_request["gpu"]["job"]),
        "execution_path": bundle["submission_request"]["execution_path"],
        "gex_chemistry_tru": "Gene Expression,TRU" in wrapper_text,
        "guide_input_chemistry_nxt": "CRISPR Guide Capture,NXT" in wrapper_text,
        "guide_output_chemistry_tru": "--crOutputChemistry TRU" in wrapper_text,
        "native_gzip": "--readFilesBgzfMode auto" in wrapper_text and "zshard" not in wrapper_text.lower(),
        "pilot_read_limit": "--readMapNumber 1000000" in wrapper_text,
        "preflight_status": preflight["status"],
        "scheduler_parser": "PASS",
        "slurm_cpus": scheduler_request["slurm"]["job"]["resources"]["cpus"],
        "status": "PASS",
        "workflow_id": scheduler_request["workflow_id"],
    }
    required_true = (
        "cellbender_cuda",
        "gex_chemistry_tru",
        "guide_input_chemistry_nxt",
        "guide_output_chemistry_tru",
        "native_gzip",
        "pilot_read_limit",
    )
    if any(not validation[key] for key in required_true):
        raise RuntimeError(f"Generated pilot failed semantic validation: {validation}")
    write_json(outputs_dir / "validation.json", validation)

    tracked_inputs = [
        inputs_dir / name
        for name in (
            "recipe.json",
            "align.ir.json",
            "cellbender.ir.json",
            "executor-profile.json",
            "recipe-inputs.json",
            "stage-outputs.json",
        )
    ]
    (inputs_dir / "checksums.tsv").write_text(checksum_manifest(tracked_inputs, inputs_dir))
    output_files = [
        outputs_dir / name
        for name in (
            "workbench-bundle.json",
            "preflight.json",
            "scheduler-request.dry-run.json",
            "validation.json",
        )
    ]
    live_validation = outputs_dir / "workbench-live-validation.json"
    if live_validation.exists():
        output_files.append(live_validation)
    (outputs_dir / "checksums.tsv").write_text(checksum_manifest(output_files, outputs_dir))
    input_rows = [
        "name\tpath\tbytes\tnotes",
        f"source_pilot\t{source_pilot_run}\t\tCompleted staged Temporal execution evidence",
        f"template_run\t{template_run}\t\tValidated recipe/interchange template",
    ]
    input_notes = {
        "recipe.json": "Two-stage STAR Suite to CellBender recipe",
        "align.ir.json": "STAR Suite wrapper Workflow IR",
        "cellbender.ir.json": "CellBender Workflow IR with CUDA",
        "executor-profile.json": "Reviewable Pikachu and Bridges-2 deployment values",
        "recipe-inputs.json": "Fresh Ocean wrapper path",
        "stage-outputs.json": "Fresh Slurm-to-GPU handoff and output paths",
    }
    for path in tracked_inputs:
        input_rows.append(
            f"{path.stem}\t{path.name}\t{path.stat().st_size}\t{input_notes[path.name]}"
        )
    (inputs_dir / "manifest.tsv").write_text("\n".join(input_rows) + "\n")
    output_notes = {
        "workbench-bundle.json": "Schema-driven review and approval artifact",
        "preflight.json": "Workbench bundle preflight",
        "scheduler-request.dry-run.json": "Exact staged Temporal request; not submitted",
        "validation.json": "Machine-readable semantic and parser checks",
        "workbench-live-validation.json": "Live UI preflight and no-submit dry-run validation",
    }
    output_rows = ["name\tpath\tbytes\tnotes"]
    for path in output_files:
        output_rows.append(
            f"{path.stem}\t{path.name}\t{path.stat().st_size}\t{output_notes[path.name]}"
        )
    (outputs_dir / "manifest.tsv").write_text("\n".join(output_rows) + "\n")
    if preflight["status"] != "ready":
        raise SystemExit(f"Bundle preflight is not ready: {preflight}")
    print(json.dumps(read_json(outputs_dir / "validation.json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
