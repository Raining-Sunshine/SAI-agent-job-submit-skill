---
name: software-hpc-run
description: Identify the scheduler for a remote cluster software job and select the installed Slurm or PBS skill. Use for HPC preparation, submission, status or result requests when the scheduler is unknown, including first-time users asking to run software on a cluster.
---

# Select the cluster job workflow

Route the current task to `software-slurm-run` or `software-pbs-run`. These companion skills must be installed for the complete workflow. Use their locations from the active skill catalog; do not assume a local installation path. If the selected companion is unavailable, report its name and installation requirement without claiming to have run its workflow.

## Understand the request

Identify whether the user wants preparation, submission, status, finalization or result retrieval. Preserve any existing authorization: a request to submit includes submission, while a request to inspect or prepare does not. Pass this intent to the selected skill.

Use the user's chosen cluster and existing SSH alias. If no connection is identified, ask for the alias or platform connection instructions. Do not ask a beginner to identify Slurm or PBS. For an existing job, start with its full job ID and recorded cluster context, not a new list of resource requests.

## Identify the scheduler with read-only evidence

Perform checks on the intended remote login host in its normal job-submission environment. Local workstation commands do not establish what the remote cluster uses.

1. Inspect a relevant existing run record or a user-provided approved submission example. Record any declared scheduler, endpoint and version; an old script or a directive alone is only a clue.
2. Check command availability, for example `command -v sbatch squeue sinfo qsub qstat`. Partial availability is useful even if the overall command returns nonzero.
3. For a Slurm candidate, inspect `squeue --version` and make a read-only query such as `sinfo -h` or the user's job queue. For a PBS candidate, inspect `qstat --version` where supported and query `qstat -B`. Use documented equivalents if the site's client differs.
4. Combine recognizable implementation/version output with a successful scheduler query, or with authoritative site instructions and matching existing job evidence. A version flag rejected by a client is inconclusive. Neither a command name nor a job-ID shape is sufficient by itself.

Use bounded command timeouts. Do not run `sbatch`, `qsub`, a held submission, or an interactive allocation as a detection test. Do not install scheduler clients or change cluster configuration to make a probe succeed.

`qsub` and `qstat` can belong to other schedulers or compatibility wrappers. Confirm PBS implementation before selecting the PBS workflow. Distinguish OpenPBS/PBS Professional from Torque and other variants; unsupported variants need matching site guidance before script generation.

| Evidence | Action |
|---|---|
| Slurm confirmed for the target | Read and follow the installed `software-slurm-run/SKILL.md`. |
| OpenPBS/PBS Professional confirmed | Read and follow the installed `software-pbs-run/SKILL.md`. |
| A different PBS-family variant is confirmed | Use the PBS skill only after its variant requirements can be met. |
| Both systems are usable | Use the scheduler recorded for the existing job or specified for the selected target. If no task-specific choice resolves it, ask which target service to use. |
| Clients missing, query blocked, or evidence conflicting | Explain the concrete missing evidence and ask for the platform instructions or administrator guidance. Do not guess or submit. |
| Another scheduler is identified | Report that neither backend covers it; do not generate PBS syntax just because `qsub` exists. |

Report the detected system and the evidence briefly. Carry the endpoint, implementation, version, intent and existing job context into the chosen workflow. Once a backend is confirmed, continue there without bouncing between skills. If a requested scheduler conflicts with the target, explain the conflict and resolve it before submission.

## Help a first-time user

Explain only the next necessary action in plain language. Separate the local terminal, the Codex conversation and operations performed on the remote cluster.

Determine whether input files are local or already remote. Ask about missing software/input information and the intended destination; let the backend discover approved scheduler settings where possible. When a parameter cannot be inferred, explain what to ask the administrator.

Before submission, explain the proposed resources and time limit in ordinary terms. Do not ask again when that plan is already authorized. After submission, return the scheduler, target, full job ID, observed state and how to resume checking it. Refer output paths only to locations actually used by this task.
