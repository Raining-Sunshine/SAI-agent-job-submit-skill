---
name: software-pbs-run
description: Prepare, submit, monitor and finalize software jobs on a confirmed PBS cluster, including multi-node MPI and threaded workloads. Use for OpenPBS or PBS Professional; verify other PBS variants separately. Use software-hpc-run when the scheduler is unknown.
---

# Software jobs on PBS

Use the user's existing SSH alias and software. Generate scripts for the actual task and PBS implementation. Read [PBS command guidance](references/pbs.md) before generating or submitting a job, and [recording guidance](references/recording.md) when implementing monitoring or final records.

## Select the operation and confirm PBS

Identify OpenPBS, PBS Professional or the actual PBS-family variant using the target's client/version output and a read-only server query or authoritative site guidance. The existence of `qsub` or `qstat` alone does not establish PBS.

For an unknown scheduler, use the installed `software-hpc-run` skill. If the router is unavailable, obtain site instructions and establish the implementation before proceeding. If Slurm is confirmed, use the installed `software-slurm-run` skill; if absent, report the missing skill. Never submit a detection job.

This workflow's command examples target OpenPBS/PBS Professional. For Torque or another variant, obtain matching documentation or an approved site script and adapt resource syntax, state interpretation and history queries. If those cannot be established, stop before generating a supposedly runnable script.

Separate the current operation:

- Preparation: inspect inputs, propose resources and generate scripts, without submission.
- Submission: prepare and submit the authorized workload.
- Status: use the full job ID, target and saved records to query the existing job.
- Finalization or retrieval: assess the existing job and locate results, without preparing a new job.

Do not ask status-only users to supply a new set of resources. Preserve existing authorization for submission or retrieval.

## Establish a new job

Obtain the input, output destination, software launch method, execution queue, required account or project, walltime and resource needs from the request, approved configuration or site queries. Ask only for information that cannot reasonably be determined.

PBS queues and site policy are not interchangeable with Slurm partitions or QoS. Distinguish account and project fields according to local policy. Preserve requested organization billing without assuming storage location selects the billing account.

Use the task's selected workspace, without assuming a directory hierarchy, file extension or software-specific API. Use configured authentication without reading private keys, credential stores or license contents. Run computation through the scheduler.

## Prepare

Confirm upload completion and whether the input is local or remote. Transfer only as needed for the task. Preserve originals, prepare a separate input snapshot and output, and verify checksums after copying. A temporary upload filename can be changed when transfer completes; retain the format required by the software.

Use supported input validation and metadata interfaces where available. Preserve model, solver and tolerance settings unless changes are requested. Metadata collection must not launch an unrequested solve or remesh.

Record available software version, input provenance, invocation, required runtime setup and resource request. Keep runtime dependencies accessible for the duration of the job.

Generate the script for the selected PBS variant. Set its intended working directory explicitly, verify it is accessible to participating nodes and direct output/error logs to known writable destinations. Preserve the software exit status through pipelines and finalization handlers.

## Choose resources and launch

Support one or more nodes, MPI, threads or hybrid execution according to the workload and site support. For OpenPBS/PBS Professional, distinguish requested resource chunks from physical hosts, CPUs per chunk, MPI ranks, threads and memory. Determine placement separately when distinct hosts are required.

Ensure requested ranks and threads fit the CPU allocation unless intentional oversubscription is explicitly requested and supported. Confirm the software build and MPI runtime are compatible with the site's launch method. Use PBS-provided allocation information with the approved launcher; never assume a Slurm launcher works here.

## Validate and submit

Check shell syntax with the script's interpreter, directive syntax, resolved values and the software command. Confirm queue limits and permissions using read-only site queries where available. Reject unresolved placeholders and unintended shell expansion.

There is no assumed portable PBS equivalent of Slurm's `sbatch --test-only`. Do not call `qsub`, including `qsub -h`, for prepare-only validation: a held submission is still a real job.

Submit only when requested. Default to one job unless a batch or array is explicitly authorized; preserve its count and scope. Save the exact script, target/server, submission timestamp and full `qsub` response. Preserve server suffixes and array identifiers in job IDs.

A user hold can be used during an authorized submission to persist the job ID before releasing that hold. Inspect any release error against the existing job instead of submitting again. If a submission response is uncertain, compare saved evidence and the user's queue by owner, name and submission time; names alone need not be unique. Resolve uncertainty before any retry. Do not automatically retry failed calculations or cancel unrelated jobs.

Report the actual state and any scheduler comment explaining delay. A queued or held job is not running.

## Monitor and hand back

Use the confirmed implementation's job queries for state, queue, requested/assigned resources and available usage. Capture original software logs, timestamps and exit status. Preserve sources and units when recording CPU and memory. See the recording reference for aggregation across nodes.

Collect model settings, mesh, solved degrees of freedom and convergence evidence when the software exposes them. Preserve solver headers and context; unavailable observations remain unavailable.

If the user explicitly requires a metric and collection cannot be established, explain the gap before launching and obtain a revised requirement. Missing optional metrics may be recorded as unavailable. Never substitute host-wide counters for job counters.

Put requested continuous sampling inside the allocated job, with coverage across participating nodes, so it does not depend on this chat. Keep launch-host-only observations labeled with that scope.

After submission, return the scheduler/target, full job ID, observed state/reason, requested resources, actual result/log locations and how to resume by job ID. Do not promise a future message or background watcher. Status queries should be bounded; use an agreed interval and stopping condition only when the user asks to watch.

## Finalize

Check active state and available history. An unknown job ID or absence from the queue does not establish completion. History availability depends on server configuration and retention; use accessible accounting or saved job evidence if history is unavailable. Never claim scheduler completion without supporting evidence.

Save a provisional record and explain missing evidence when final accounting cannot yet be obtained. Return for a later refresh rather than polling indefinitely. A finished state alone does not establish successful computation: inspect exit status, software errors/completion messages and expected outputs. Physical validity remains a separate assessment.

Save the final structured record and readable report before cleanup. Keep inputs, snapshots, results, nonempty logs, settings, scripts and requested checkpoints. Delete only temporary artifacts created for this run after confirming they are unused. Restore available evidence before cleanup after node failures or forced termination. Report inaccessible scratch or unverified outcomes accurately.

For requested result retrieval, establish the user's local destination, transfer the selected results and logs, and verify transfer completeness with checksums where practical. Preserve existing local files unless replacement is authorized. Downloading does not authorize deleting the remote results.
