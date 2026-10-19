---
name: software-slurm-run
description: Prepare, submit, monitor and finalize software jobs on a confirmed Slurm cluster, including multi-node MPI and threaded workloads. Use when Slurm is specified or verified; use software-hpc-run to identify an unknown scheduler.
---

# Software jobs on Slurm

Use the user's existing SSH alias and available software. Generate task-specific submission and recording scripts using the supported software interface and cluster configuration. Read [recording guidance](references/recording.md) when implementing monitoring or final records.

## Select the operation

Confirm that the target is Slurm using the existing job context or a recognizable Slurm client and successful read-only query on the intended remote host. If the scheduler is unknown, use the installed `software-hpc-run` skill. If that router is unavailable, ask for site instructions and confirm Slurm before proceeding. When PBS is confirmed, use the installed `software-pbs-run` skill instead; if missing, report the missing skill. Never submit a probe job or apply Slurm directives to a PBS target.

Preserve the requested operation and existing authorization:

- Preparation: inspect inputs, propose resources and generate scripts; do not submit.
- Submission: prepare and submit the authorized workload.
- Status: query the identified job and existing logs; do not recreate inputs or ask for new resource settings.
- Finalization or retrieval: use the full job ID, target and existing records to assess completion and locate results.

## Establish a new job

Obtain the input, intended output location, software launch method, billing account, partition, applicable QoS, time limit and resource requirements from the request, existing approved job configuration or permitted read-only site queries. Ask only for material missing information. Explain missing administrator-provided values in plain language.

Use the workspace selected for this task. Do not assume a storage root, directory hierarchy, file extension, model format, study tag or software-specific command syntax. Storage location and billing account are separate choices. Preserve organization billing when requested.

Use configured authentication without reading private keys, credential stores or license contents. Run computation through the scheduler.

## Prepare

- Determine whether inputs are local or remote, establish the intended remote destination and transfer files as needed for the task. Confirm upload completion before copying or inspecting the input. A temporary upload name may be changed after transfer; preserve any format required by the software.
- Preserve originals. Create a distinct run and separate outputs within the selected destination. Record input checksums and verify that inputs did not change during preparation.
- Use the software's supported validation or metadata interface where available. Do not assume the input is an archive or that a particular API exists.
- Preserve model, solver and tolerance settings unless changes are requested. Reading metadata must not trigger an unrequested solve, remesh or settings change.
- Record the software version when available, input provenance, launch command, environment setup needed for reproduction and requested resources. Do not collect authentication material.
- Generate the scripts needed for the current task. Keep their runtime dependencies available throughout the job, even if temporary transfer files are removed.

## Choose parallel execution

Support single-node, multi-node, MPI, threaded and hybrid jobs according to the request, software capabilities and cluster support.

Match nodes, tasks or tasks per node, CPUs per task, memory and time to the workload. Distinguish per-node memory from per-CPU memory. Set thread counts consistently when threading is used.

For MPI, verify the runtime is compatible with the software build and the cluster's supported launcher. Use the approved launch mechanism; do not blindly nest launchers or assume every MPI implementation accepts the same options. Ensure the executable, inputs and required environment are available on every participating node.

Do not constrain all jobs to one node or one task. Do not promise linear scaling.

## Validate and submit

Generate Slurm directives using the site's supported options: account, partition, applicable QoS, nodes, tasks, CPUs per task, memory and walltime. Use the approved launcher for the software. Check shell syntax, generated directive values and the launch command. Reject unresolved placeholders and unintended shell expansion. Use `sbatch --test-only` for scheduler validation where supported; scheduler validation does not run or validate the scientific calculation.

Preparation is separate from submission. Submit only when the user requests it. Default to one job unless the user explicitly requests a batch or array; honor the authorized count and scope. Do not automatically retry failed calculations.

Submit with `sbatch --parsable` where supported. Save its full response, the job ID, cluster identity and exact submitted script before reporting success. A held submission may be used to persist the ID before release when supported. If submission or release returns an uncertain response, inspect the queue and saved evidence before any retry. A held job must be inspected or released, not replaced with another submission.

Verify the observed queue state and initial logs. PENDING means execution has not started; report the actual reason from `squeue` or `scontrol show job` rather than assuming resource shortage. Do not cancel unrelated jobs or install persistent background watchers without a request.

## Monitor

Collect scheduler state, raw software output, measured timing, exit codes, CPU and memory observations. Use available software interfaces or logs for mesh, discretization, degrees of freedom and convergence evidence.

For distributed jobs, collect across participating nodes or use scheduler-supported accounting with documented coverage. Do not report launch-node metrics as job-wide metrics. Keep per-node and per-step observations when aggregating; avoid double-counting overlapping job and step counters.

Treat an explicitly required measurement as a launch prerequisite; if unavailable, explain the gap before launching and obtain a revised requirement. For optional metrics, keep the available observations and report omissions. Never substitute whole-host measurements for job measurements.

Preserve solver headers, sections and parameter context. Distinguish observed completion, convergence evidence and physical validity. A zero native exit code alone is insufficient to establish success.

Put continuous collection inside the allocated job when requested, so it does not depend on this chat staying open. Keep the software's exit status even when logs are piped or an exit handler runs. After submission, return the target, job ID, state/reason, resource summary and actual result/log locations. Explain that the user can resume with the job ID and target. Do not promise future messages or unattended final accounting.

For a status request, make bounded queries and report observations as of a timestamp. For a user-requested watch, use a site-appropriate interval and the requested stopping condition. Read `squeue`/`scontrol` for active jobs and `sacct` for accounting when available; retain job and step scopes.

## Finalize

Confirm a terminal scheduler state and refresh accounting, allowing for accounting lag. Queue absence alone does not prove completion. If accounting is delayed or unavailable, save a provisional record with unknown scheduler outcome, explain the gap and return for a later refresh rather than waiting indefinitely.

Save a structured final record and a readable status with input provenance, allocation, software invocation, observed solver metrics, timings, resource coverage, exit codes, scheduler state and output evidence. Preserve failed and incomplete runs with accurate outcomes; leave unavailable fields missing or null.

Save records before cleaning temporary files. Keep originals, snapshots, results, nonempty logs, settings, scripts and requested checkpoints. Clean only temporary artifacts created for this run, after confirming they are unused. Do not apply broad filename-based cleanup to an existing workspace.

Forced termination or node failure may bypass exit handlers. Recover observations from logs and accounting before cleanup. Report inaccessible node scratch or missing records without claiming successful cleanup.

For requested result retrieval, establish the user's local destination, transfer the selected results and logs, and verify transfer completeness with checksums where practical. Preserve existing local files unless replacement is authorized. Downloading does not authorize deleting the remote results.

## Command references

Use the target installation's documentation for version-specific behavior. See [sbatch](https://slurm.schedmd.com/sbatch.html), [squeue](https://slurm.schedmd.com/squeue.html) and [job states](https://slurm.schedmd.com/job_state_codes.html).
