---
name: software-slurm-run
description: Prepare, submit, monitor and finalize software jobs on Slurm, with resource and solver records. Use for requested cluster batch jobs, including multi-node MPI and threaded workloads.
---

# Software jobs on Slurm

Use the user's existing SSH alias and available software. Generate task-specific submission and recording scripts using the supported software interface and cluster configuration. Read [recording guidance](references/recording.md) when implementing monitoring or final records.

## Establish the job

Obtain the input, intended output location, software launch method, billing account, partition, applicable QoS, time limit and resource requirements from the request or existing approved job configuration. Ask only for material missing information.

Use the workspace selected for this task. Do not assume a storage root, directory hierarchy, file extension, model format, study tag or software-specific command syntax. Storage location and billing account are separate choices. Preserve organization billing when requested.

Use configured authentication without reading private keys, credential stores or license contents. Run computation through the scheduler.

## Prepare

- Confirm upload completion before copying or inspecting the input. A temporary upload name may be changed after transfer; preserve any format required by the software.
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

Check shell syntax, generated directive values and the launch command. Reject unresolved placeholders and unintended shell expansion. Validate the scheduler request where supported; scheduler validation does not run or validate the scientific calculation.

Preparation is separate from submission. Submit only when the user requests it. One submission request authorizes one job; do not automatically retry failed calculations.

Save the exact submitted script and job ID. A held submission may be used to persist the ID before release when supported. If submission or release returns an uncertain response, inspect the queue and saved evidence before any retry. A held job must be inspected or released, not replaced with another submission.

Verify the observed queue state and initial logs. Pending means waiting for resources, not running. Do not cancel unrelated jobs or install persistent background watchers without a request.

## Monitor

Collect scheduler state, raw software output, measured timing, exit codes, CPU and memory observations. Use available software interfaces or logs for mesh, discretization, degrees of freedom and convergence evidence.

For distributed jobs, collect across participating nodes or use scheduler-supported accounting with documented coverage. Do not report launch-node metrics as job-wide metrics. Keep per-node and per-step observations when aggregating; avoid double-counting overlapping job and step counters.

If requested monitoring cannot be established, resolve the gap before launching when it is a prerequisite. Otherwise report the limitation explicitly and keep the available observations. Never substitute whole-host measurements for job measurements.

Preserve solver headers, sections and parameter context. Distinguish observed completion, convergence evidence and physical validity. A zero native exit code alone is insufficient to establish success.

## Finalize

Confirm a terminal scheduler state and refresh accounting, allowing for accounting lag. Queue absence alone does not prove completion.

Save a structured final record and a readable status with input provenance, allocation, software invocation, observed solver metrics, timings, resource coverage, exit codes, scheduler state and output evidence. Preserve failed and incomplete runs with accurate outcomes; leave unavailable fields missing or null.

Save records before cleaning temporary files. Keep originals, snapshots, results, nonempty logs, settings, scripts and requested checkpoints. Clean only temporary artifacts created for this run, after confirming they are unused. Do not apply broad filename-based cleanup to an existing workspace.

Forced termination or node failure may bypass exit handlers. Recover observations from logs and accounting before cleanup. Report inaccessible node scratch or missing records without claiming successful cleanup.
