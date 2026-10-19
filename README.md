# Cluster software job skills: Slurm and PBS

[中文说明](README.zh-CN.md)

Describe the calculation you want in ordinary language. The agent helps prepare it for a remote cluster, submit it, check progress and collect results. Think of the cluster as shared computers, and Slurm or PBS as the service that queues work and assigns resources.

This repository contains three cooperating instruction-based skills. The agent generates scripts for the actual software and task. The repository does not supply a ready-to-run scientific application, a cluster account or the software installation.

| Skill | Purpose |
|---|---|
| `software-hpc-run` | General entry point: identify the target scheduler and select a backend |
| `software-slurm-run` | Prepare, submit, inspect and finalize jobs on a confirmed Slurm cluster |
| `software-pbs-run` | Perform the same workflow on a confirmed PBS cluster |

Install all three for automatic selection. The PBS workflow targets OpenPBS/PBS Professional; other PBS variants require site-specific verification. Single-node, multi-node, MPI, threaded and hybrid execution depend on software and cluster support.

## First-time user guide

### 1. Gather the essentials

- Codex CLI installed and signed in. Start with the [official Codex CLI guide](https://learn.chatgpt.com/docs/codex/cli) if needed.
- A cluster account, connection instructions and permission to use computing resources from your provider or administrator.
- Software available on the cluster, with any required license.
- Your calculation's input files and an intended result destination.

You can ask the agent to discover available accounts, queues, partitions and resource settings. If it cannot determine something, it should explain what to ask the administrator. You do not need to learn MPI before your first task.

### 2. Install all three skills in Codex

**In your local terminal:**

```bash
codex
```

If the command is missing, complete the installation in the previous section. Once Codex opens, send the following to the **Codex conversation**, not to the shell:

```text
$skill-installer
Install these three skills from https://github.com/Raining-Sunshine/SAI-agent-job-submit-skill:
skills/software-hpc-run
skills/software-slurm-run
skills/software-pbs-run
If a skill is already installed, inspect local changes before updating it to the repository version.
```

Use `/skills` in Codex to check that all three are available. Restart Codex if they do not appear. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills) for installation and invocation behavior.

### 3. Set up and test the cluster connection

Use an existing working SSH alias when available. For a new connection, add a minimal entry to **your local OpenSSH user configuration file**, commonly `~/.ssh/config` on Linux/macOS/WSL. This block is configuration text, not shell commands.

```sshconfig
Host cluster
    HostName <HOST>
    User <USER>
    Port <PORT>
    IdentityFile <KEY_FILE>
    IdentitiesOnly yes
```

| Value | What to enter |
|---|---|
| `cluster` | A short name you choose for this connection and give to the agent |
| `<HOST>` | Login server address supplied by the provider |
| `<USER>` | Your cluster login name |
| `<PORT>` | SSH port supplied by the provider |
| `<KEY_FILE>` | The location of your local key file, not its contents |

Replace each placeholder including its angle brackets. Verify the initial host identity using the provider's instructions and unlock a protected key in your own terminal. Follow the provider's configuration if it uses a different authentication method.

**Test from the same local environment where you run Codex:**

```bash
ssh cluster exit
```

A successful return without an error confirms SSH connectivity, not job-submission permission. Resolve host lookup, timeout or authentication errors using the provider's connection instructions. The agent uses the connection alias without reading key material or license contents.

### 4. Ask for an environment check and a first job plan

Send this request in the **Codex conversation**, filling in your information:

```text
I am using these cluster job skills for the first time.
Please identify whether the target uses Slurm or PBS.

Cluster connection alias: ...
Software to run: ...
Input files are on: my computer / the server, at ...
Calculation I want to perform: ...
Where I want the results saved: ...

Check the connection, software and execution requirements first.
Do not submit a job yet.
Discover available resource settings and suggest a plan.
For anything you cannot determine, tell me what to ask the administrator.
```

Ordinary language can activate the installed skills. If selection does not occur, prefix the request with `$software-hpc-run`.

The agent performs read-only checks on the target and chooses the Slurm or PBS skill. If both systems are present, access fails or evidence is insufficient, it explains the uncertainty and asks for the missing context. It does not submit a test job to identify the scheduler. Experienced users can also invoke `$software-slurm-run` or `$software-pbs-run` directly.

If inputs are local, the agent first establishes a remote destination and transfers them as needed. If they are already remote, it uses those files. Preparation starts after upload completion. A temporary upload name can be changed when transfer finishes while retaining the format required by the software. Originals are preserved and results are saved separately.

You should receive the detected scheduler, software availability, input checks, proposed resources and maximum runtime, plus any missing information. The plan should explain nodes, processes/threads, total memory and how memory is allocated.

### 5. Submit the agreed plan

In the **Codex conversation**:

```text
Submit this job using the plan we just agreed on.
Tell me the full job ID and its current state.
```

Submission may consume your allocation or incur charges under the provider's rules. Save the returned **cluster alias, scheduler and full job ID**. Check the requested resources, observed state and actual result/log locations.

Accepted does not mean running. Queued, held, running and finished are different states; the agent should explain the scheduler's reported waiting reason. If the submission response is uncertain, check for the existing job before requesting another submission.

### 6. Check progress and retrieve results

**Check progress:**

```text
Check job ... on cluster ...
Explain any waiting reason or error. Do not resubmit it.
```

**Check results:**

```text
Check whether job ... has finished, consolidate its records,
and tell me where the results and logs are.
```

**Download results:**

```text
Download this job's results to this location on my computer: ...
```

A formally submitted batch job is normally managed by the scheduler independently of your local terminal; interactive allocations differ. Closing the conversation does not arrange future progress messages. Requested continuous collection runs inside the job. You can later resume checking and finalization using the target and full job ID.

History may be delayed or no longer retained. An absent job does not prove successful completion: the agent uses available logs and outputs and reports missing evidence. Verify downloaded files; downloading results does not automatically delete the remote copies.

### Common sticking points

| Situation | Next step |
|---|---|
| A skill cannot be found | Check that all three installed; restart Codex if necessary and explicitly invoke the general entry point |
| SSH works but scheduler commands are missing | Check the provider's login host and environment; local scheduler installation does not configure the remote cluster |
| A queue query succeeds with no jobs | There may be no visible jobs; distinguish this from a connection or query error |
| Account, partition or queue is unknown | Ask the agent to inspect available settings, then ask the administrator for anything requiring permission information |
| A job keeps waiting | Inspect its scheduling reason instead of repeatedly submitting it |
| A finished PBS job cannot be queried | History may be disabled or expired; inspect retained records and logs |
| Skills installed, but no input files exist | Skill installation does not create scientific inputs; prepare the files required by the software |

## A few useful terms

| Term | Meaning |
|---|---|
| Cluster / node | Shared computers / a computer or resource unit used for computation |
| Scheduler | Service that queues jobs and assigns resources, such as Slurm or PBS |
| Partition / queue | Resource or scheduling destination; options are not interchangeable between systems |
| Account / project | Allocation or project charged for the work, not necessarily the login username |
| QoS | A priority and resource-limit policy used at some sites |
| CPU / memory / walltime | Processing resources / runtime storage / maximum permitted runtime; walltime is not a completion estimate |
| MPI / threads | Cooperation between processes / parallel work within a process |
| Job ID / logs | Scheduler-issued task identifier / recorded program output |

## Records and cleanup

Keep raw software output, scheduler state, timing, exit status and available CPU/memory observations. Record settings, mesh, degrees of freedom and convergence when the software exposes them; unavailable metrics remain unavailable. Distributed measurements must state their coverage and aggregation method.

Neither a zero exit code nor an output file alone proves successful computation. Assess software completion, scheduler outcome and expected outputs together. Scientific validity requires separate assessment.

Save records before removing this run's unused temporary artifacts. Retain inputs, results, nonempty logs, submitted scripts and requested checkpoints.

Skill instructions: [automatic selection](skills/software-hpc-run/SKILL.md), [Slurm](skills/software-slurm-run/SKILL.md), [PBS](skills/software-pbs-run/SKILL.md). Advanced recording: [Slurm](skills/software-slurm-run/references/recording.md), [PBS](skills/software-pbs-run/references/recording.md).
