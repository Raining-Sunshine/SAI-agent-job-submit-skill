# Software jobs on Slurm

[中文说明](README.zh-CN.md)

An agent skill for preparing, submitting, monitoring and recording software jobs on a Slurm cluster. It guides the agent to generate scripts for the current software and task, using the cluster's supported launch method.

## Setup

Install the `skills/software-slurm-run` folder as a skill in your agent environment. Invoke `$software-slurm-run`, or ask the agent to submit a software job and record its progress.

Requirements:

- An SSH client and an established cluster connection.
- Slurm access and an approved billing account, partition and, where applicable, QoS.
- Software available on the compute nodes, with any required license.
- Writable storage selected for the task.
- A compatible MPI runtime when distributed execution is requested.

Use the software's supported batch interface. Additional interpreters or APIs are needed only when the chosen workflow requires them.

## SSH connection

Configure the connection in your own terminal. A minimal SSH config entry is:

```sshconfig
Host cluster
    HostName <HOST>
    User <USER>
    Port <PORT>
    IdentityFile <KEY_FILE>
    IdentitiesOnly yes
```

Use the key location appropriate to your setup. Complete the initial connection and unlock any protected key in your own terminal. The agent uses the configured alias:

```bash
ssh cluster 'squeue -u "$USER"'
```

The agent does not need to read key material or license contents.

## Prepare and submit

Provide the input, destination, software launch method, billing account and resource needs for the current task. Storage follows the location you select; the skill does not prescribe a directory layout.

Finish uploading before preparing the job. A temporary upload name can be changed after transfer completes. Preserve the original input and create a separate output. Where the software requires a filename extension, retain its required format.

The agent checks the input, prepares a separate run, and generates a submission script using the software's supported options. It records input checksums, the submitted script, software version when available, and requested resources. It preserves model settings unless you request changes.

Parallel execution can use one or more nodes, MPI, threads, or a hybrid arrangement. Node count, task count, CPUs per task and memory follow the workload and cluster configuration. The launch command must match the allocation and the software's MPI compatibility; increasing resources does not guarantee proportional speedup.

Preparation alone does not submit a job. A submission request authorizes one job. The agent validates the script and scheduler request, submits once, saves the job ID, and checks its state. If the submission response is uncertain, it checks the queue and existing evidence before trying again.

## Monitor and record

The agent records scheduler state, raw software output, elapsed time, exit status, CPU and memory observations. Where available, it also records model settings, mesh statistics, degrees of freedom and convergence history.

For multiple nodes, collect observations across the allocation. A measurement from the launch node alone does not represent the whole job. Keep node and step context when combining samples. Distinguish per-core CPU usage from allocation utilization, and per-task memory from aggregate memory.

Preserve original solver table headings and parameter context. Linear residuals, nonlinear errors and time steps have different meanings. Missing observations remain unavailable.

A zero exit code is one piece of evidence. Check the scheduler's terminal state, software completion messages and expected output before reporting success. Physical validity requires separate scientific assessment.

## Finish

After the job reaches a confirmed terminal state, refresh accounting and save the final record. Keep inputs, results, nonempty logs, the submitted script and reproducibility information. Clean only temporary files created for this run after the records are saved; retain requested checkpoints.

Node failures or forced termination can interrupt finalization. Recover available observations before cleanup and report anything that could not be verified.

The [skill instructions](skills/software-slurm-run/SKILL.md) describe the workflow; [recording guidance](skills/software-slurm-run/references/recording.md) covers parallel resource measurements and final records.
