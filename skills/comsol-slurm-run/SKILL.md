---
name: comsol-slurm-run
description: Submit COMSOL batch studies to Slurm from organization storage, collect discretization, mesh, convergence, timing and resource records, and clean run intermediates. Use for organization CPU jobs and their monitoring or finalization.
---

# COMSOL organization jobs

Use the user's existing SSH host alias and site-approved COMSOL installation. Obtain missing scheduler parameters from approved scripts or the user. Never read private keys, passwords, token stores, environment dumps or license contents. The user configures SSH and unlocks keys outside the agent. This skill includes all runtime assets. The source repository README provides optional manual setup and metric background.

## Scope and storage

- Submit from an organization workspace beneath `/org`, with organization billing. `--org-root` and `--account` are mandatory. Do not put persistent jobs/results in personal home storage.
- Preserve originals in `models/comsol/uploads/`. Create a unique snapshot and separate result inside `run_records/comsol/<run-id>/`.
- Store annotated sbatch backups in `run_records/comsol/script_backups/`, and per-run JSON plus the training index in `run_records/comsol/agent_training/`.
- Never overwrite an input, modify study settings, automatically retry a failed solve, or kill existing jobs without authorization. A run request authorizes one submission. For an uncertain response, inspect the queue and submission file before retrying.
- Never publish models, tests, runtime records, site configurations, keys, licenses or raw logs. Publish only explicitly requested sanitized sources/documentation.

## Prepare and submit

1. Check the queue and approved CPU configuration. Verify the upload is complete: stable size/mtime and valid MPH ZIP CRC. Do not move a file still being uploaded.
2. Stage this skill temporarily on the login host through the SSH alias. Remove the transfer archive and staging directory using a trap after preparation. Do not create an unsolicited permanent remote tool installation.
3. Run `scripts/prepare_run.py` on the login host with `--source`, `--org-root`, `--comsol`, `--account`, `--partition`, `--qos` and requested CPU/memory/time/study options. Default is prepare-only. `--submit` runs scheduler validation, submits exactly once on hold, records the ID and backups, then releases the hold. If release fails, inspect the existing held job instead of resubmitting.
4. Verify queue state, organization working directory, monitor startup and stdout/stderr. Report actual state; pending is not running. One node, one task, 48 threads, 64 GiB and `std1` are configurable examples, not universal requirements.

The helper preserves ZIP settings, input hash and provenance. Its Java helper reads the saved mesh without remeshing or modifying COMSOL security preferences. COMSOL batch writes a separate result and full raw solver log.

## Monitor and interpret

- Read `resource_usage.txt`, `monitor.log`, `batch.log`, `run_report.txt` and scheduler state. Sample the entire Slurm job cgroup, not just the batch shell. Monitoring requires cgroup v2 and a readable Slurm `step_*` ancestor. Monitor startup failure stops the run before solving.
- Distinguish one-core CPU percentage from allocation-normalized percentage. Cgroup memory includes page cache; anonymous memory and Slurm MaxRSS differ. Sampling can miss short peaks.
- Keep solver table headers, sections and continuation parameter context. A transient step or linear residual is not automatically a nonlinear convergence measure. Report the named column and its trend.
- Discretization, saved input mesh and solved DOFs are separate observations. Do not infer one from another. Adaptation/remeshing may change the solve mesh.
- Native exit code 0 alone does not establish success. Check error markers, completion evidence, output presence and scheduler status independently. Physical validity remains unassessed.

## Finish and clean

The job exit handler saves timing/records before deleting known run intermediates: recovery/checkpoint directories, model status/lock files, compiled Java, Python caches, phase/timestamp scratch and empty diagnostic logs. It removes only the exact node-local temporary directory it created. Retain models, nonempty logs, source scripts, exit codes, metadata and training data.

After terminal completion, temporarily stage the skill again and run `scripts/finish_run.py RUN_DIRECTORY`. It refreshes accounting and the training index. Never clean active jobs. SIGKILL, node loss and hard limits may bypass traps: recover missing timing/records from scratch/log/accounting evidence before deletion. Unreachable node scratch may need site cleanup; do not claim deletion without verification. Do not install background/cross-session watchers unless requested.

Before publication, scan the exact file set for site identifiers and secret patterns. Use generic examples, no tests or private artifacts. Verify uploaded file hashes, then delete the local repository/work copy and packaging files when requested. Do not delete an explicitly requested installed skill or unrelated user files.
