#!/usr/bin/env python3
"""Render the staged-recipe adapter against the completed CP_R1 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


RUN_ID = "msk-cardiac-cp-r1-recipe-adapter-dry-run-20260918"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-repo", type=Path, required=True)
    parser.add_argument("--prior-run", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    adapter_repo = args.adapter_repo.resolve()
    prior_run = args.prior_run.resolve()
    run_dir = args.run_dir.resolve()
    sys.path.insert(0, str(adapter_repo))
    sys.path.insert(0, str(adapter_repo / "tools"))

    from staged_execution_plan import build_staged_recipe_workbench_bundle
    from workbench_bundle import preflight_bundle
    from workbench_temporal_adapter import build_submission_payload

    initial = json.loads((prior_run / "outputs/runtime/request.json").read_text())
    successful = json.loads((prior_run / "outputs/runtime/request_attempt3.json").read_text())
    wrapper_source = prior_run / "commands/slurm_cardiac_subsample.sh"
    ocean_wrapper = (
        "/ocean/projects/bio230034p/lhung2/"
        "temporal-cardiac-pilot-20260917T193023Z/input/slurm_cardiac_subsample.sh"
    )

    align_ir = {
        "schema": "biodepot.workflow-ir/v0",
        "metadata": {
            "id": "msk_cardiac_cp_r1_star_wrapper",
            "name": "MSK Cardiac CP_R1 STAR Suite wrapper",
            "source_language": "star-suite",
        },
        "workflow": {
            "inputs": {"launch_script": {"type": "file", "required": True}},
            "outputs": {"raw_mex": {"type": "directory"}},
            "nodes": [{
                "id": "launch",
                "name": "Launch STAR Suite CP_R1 wrapper",
                "kind": "x-command",
                "inputs": {"launch_script": {"type": "file", "required": True}},
                "outputs": {"raw_mex": {"type": "directory"}},
                "extensions": {
                    "command_profile": {
                        "program": "/bin/bash",
                        "args": [{"input_ref": "launch_script"}],
                    }
                },
            }],
            "edges": [],
            "subworkflows": [],
            "conditions": [],
        },
        "annotations": {
            "provenance": {
                "wrapper_sha256": sha256(wrapper_source),
                "star_suite_version": "1.9.4",
                "reference": "refdata-gex-GRCh38-2024-A",
                "gex_chemistry": "TRU",
                "guide_input_chemistry": "NXT",
                "guide_output_chemistry": "TRU",
            }
        },
        "execution_hints": {},
        "optional_specs": {},
    }
    cellbender_ir = {
        "schema": "biodepot.workflow-ir/v0",
        "metadata": {
            "id": "cellbender_0_3_2_cp_r1",
            "name": "CellBender CP_R1",
            "source_language": "star-suite",
        },
        "workflow": {
            "inputs": {"raw_mex": {"type": "directory", "required": True}},
            "outputs": {"filtered_h5": {"type": "file"}},
            "nodes": [{
                "id": "cellbender",
                "name": "CellBender remove-background",
                "kind": "x-command",
                "inputs": {"raw_mex": {"type": "directory", "required": True}},
                "outputs": {"filtered_h5": {"type": "file"}},
                "extensions": {
                    "command_profile": {
                        "program": "cellbender",
                        "args": [
                            "remove-background",
                            "--input", {"input_ref": "raw_mex"},
                            "--output", "output/cellbender_counts.h5",
                            "--checkpoint", "output/ckpt.tar.gz",
                            "--cuda",
                            "--expected-cells", "300",
                            "--total-droplets-included", "3000",
                            "--epochs", "10",
                            "--low-count-threshold", "2",
                            "--exclude-feature-types", "CRISPR Guide Capture"
                        ],
                    }
                },
            }],
            "edges": [],
            "subworkflows": [],
            "conditions": [],
        },
        "annotations": {"provenance": {"cellbender_version": "0.3.2", "cuda": True}},
        "execution_hints": {},
        "optional_specs": {},
    }
    recipe = {
        "schema": "biodepot.execution-recipe/v0",
        "id": "msk_cardiac_cp_r1_star_cellbender",
        "title": "MSK Cardiac CP_R1 STAR Suite and CellBender",
        "strategy": "scheduler_chained",
        "inputs": {"launch_script": {"kind": "path", "required": True}},
        "steps": [
            {
                "id": "star",
                "workflow_id": align_ir["metadata"]["id"],
                "inputs": {"launch_script": {"from": "recipe.inputs.launch_script"}},
                "exports": {"raw_mex": {"kind": "path", "checkpoint": True}},
            },
            {
                "id": "cellbender",
                "workflow_id": cellbender_ir["metadata"]["id"],
                "depends_on": ["star"],
                "inputs": {"raw_mex": {"from": "steps.star.outputs.raw_mex"}},
                "exports": {"filtered_h5": {"kind": "path"}},
            },
        ],
        "outputs": {"filtered_h5": {"from": "steps.cellbender.outputs.filtered_h5"}},
        "metadata": {"source_run": str(prior_run)},
    }

    stage_in_items = list(initial["stage_in"]["items"])
    stage_in_items.append({
        "source_path": str(wrapper_source),
        "destination_path": ocean_wrapper,
        "recursive": False,
    })
    executor_profile = {
        "schema": "biodepot.staged-executor-profile/v1",
        "name": "pikachu-bridges2-cardiac-pilot",
        "orchestration": {"task_queue": successful["task_queue"]},
        "globus": {"task_queue": successful["task_queue"]},
        "slurm": {
            "task_queue": successful["slurm"]["task_queue"],
            "partition": successful["slurm"]["job"]["config"]["partition"],
            "time": successful["slurm"]["job"]["config"]["time"],
            "cpus": successful["slurm"]["job"]["resources"]["cpus"],
            "mem_mb": successful["slurm"]["job"]["resources"]["mem_mb"],
            "timeout_seconds": successful["slurm"]["timeout_seconds"],
            "config": successful["slurm"]["job"]["config"],
        },
        "gpu": {
            "task_queue": successful["gpu"]["task_queue"],
            "image": successful["gpu"]["job"]["image"],
            "device": successful["gpu"]["job"]["gpu_device"],
            "min_free_mb": successful["gpu"]["job"]["min_gpu_free_mb"],
            "timeout_seconds": successful["gpu"]["job"]["timeout_seconds"],
            "wait_timeout_seconds": successful["gpu"]["job"]["gpu_wait_timeout_seconds"],
            "local_output_dir": successful["gpu"]["job"]["local_output_dir"],
        },
        "transfers": {
            "stage_in": {
                "source_endpoint_id": initial["stage_in"]["source_endpoint_id"],
                "destination_endpoint_id": initial["stage_in"]["destination_endpoint_id"],
                "items": stage_in_items,
                "timeout_seconds": initial["stage_in"]["timeout_seconds"],
                "poll_interval_seconds": initial["stage_in"]["poll_interval_seconds"],
            },
            "stage_back": {
                "source_endpoint_id": successful["stage_back"]["source_endpoint_id"],
                "destination_endpoint_id": successful["stage_back"]["destination_endpoint_id"],
                "items": successful["stage_back"]["items"],
                "timeout_seconds": successful["stage_back"]["timeout_seconds"],
                "poll_interval_seconds": successful["stage_back"]["poll_interval_seconds"],
            },
            "publish": {
                "source_endpoint_id": successful["publish"]["source_endpoint_id"],
                "destination_endpoint_id": successful["publish"]["destination_endpoint_id"],
                "items": successful["publish"]["items"],
                "timeout_seconds": successful["publish"]["timeout_seconds"],
                "poll_interval_seconds": successful["publish"]["poll_interval_seconds"],
            },
        },
    }
    recipe_inputs = {"launch_script": ocean_wrapper}
    stage_outputs = {
        "star": {
            "raw_mex": str(
                Path(successful["gpu"]["job"]["local_output_dir"]).parent
                / "slurm/raw_feature_bc_matrix"
            )
        },
        "cellbender": {
            "filtered_h5": str(
                Path(successful["gpu"]["job"]["local_output_dir"])
                / "cellbender_counts_filtered.h5"
            )
        },
    }
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
    bundle["form_data"]["execution"]["run_id"] = RUN_ID
    payload = build_submission_payload(bundle)
    preflight = preflight_bundle(bundle)
    plan_text = json.dumps(bundle["staged_execution_plan"], sort_keys=True)
    wrapper_text = wrapper_source.read_text()
    checks = {
        "preflight_ready": preflight["status"] == "ready",
        "plan_schema": bundle["staged_execution_plan"]["schema"] == "biodepot.staged-execution-plan/v1",
        "plan_has_no_endpoint_ids": "endpoint_id" not in plan_text,
        "plan_has_no_task_queues": "task_queue" not in plan_text,
        "stage_in_has_four_fastqs_plus_wrapper": len(payload["stage_in"]["items"]) == 5,
        "stage_back_preserves_five_items": len(payload["stage_back"]["items"]) == 5,
        "native_gzip_preserved": sum(
            item["source_path"].endswith(".fastq.gz") for item in payload["stage_in"]["items"]
        ) == 4,
        "slurm_uses_32_cpus": payload["slurm"]["job"]["resources"]["cpus"] == 32,
        "slurm_wrapper_hash_recorded": bool(align_ir["annotations"]["provenance"]["wrapper_sha256"]),
        "gex_chemistry_is_tru": "Gene Expression,TRU" in wrapper_text,
        "guide_input_chemistry_is_nxt": "CRISPR Guide Capture,NXT" in wrapper_text,
        "guide_output_chemistry_is_tru": "--crOutputChemistry TRU" in wrapper_text,
        "pilot_is_one_million_reads": "--readMapNumber 1000000" in wrapper_text,
        "gpu_uses_cuda": "--cuda" in payload["gpu"]["job"]["cmd"],
        "gpu_input_is_raw_mex": payload["gpu"]["job"]["input_files"] == {
            stage_outputs["star"]["raw_mex"]: "raw_feature_bc_matrix"
        },
        "publish_preserved": payload["publish"]["items"] == successful["publish"]["items"],
        "approval_still_unconfirmed": not bundle["submission_request"]["approval"]["confirmed_by_user"],
    }
    validation = {
        "schema": "morphic.recipe-interchange-validation/v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "adapter_commit": "577c27f39e1dc3c83cf133eaf489dde37d85752e",
        "scheduler_commit": "2e35bcc",
        "source_pilot": str(prior_run),
        "submitted": False,
    }

    inputs = run_dir / "inputs"
    outputs = run_dir / "outputs"
    write_json(inputs / "recipe.json", recipe)
    write_json(inputs / "align.ir.json", align_ir)
    write_json(inputs / "cellbender.ir.json", cellbender_ir)
    write_json(inputs / "executor-profile.json", executor_profile)
    write_json(inputs / "recipe-inputs.json", recipe_inputs)
    write_json(inputs / "stage-outputs.json", stage_outputs)
    write_json(outputs / "staged-plan.json", bundle["staged_execution_plan"])
    write_json(outputs / "workbench-bundle.json", bundle)
    write_json(outputs / "scheduler-request.dry-run.json", payload)
    write_json(outputs / "preflight.json", preflight)
    write_json(outputs / "validation.json", validation)
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0 if validation["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
