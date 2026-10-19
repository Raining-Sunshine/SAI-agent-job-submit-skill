# COMSOL organization Slurm skill

[中文说明](README.zh-CN.md)

An English agent skill plus executable Python/Bash helpers for organization COMSOL batch jobs. All examples are parameterized. The repository contains no actual cluster host, user, account, concrete site path, credential, license, model, test file, or run record. Generated records remain on organization storage.

## Requirements and installation

WSL/Linux OpenSSH; Python 3.9+ on remote hosts; Slurm (`sbatch`, `scontrol`, `squeue`, `sacct`, `sstat`, `srun`); an existing licensed COMSOL installation with its Java API; writable organization storage; readable job-level cgroup v2 on compute nodes. Python helpers use only the standard library.

Authenticate to GitHub outside the agent. Never embed a token in a clone URL. Install just the skill, removing the disposable clone:

```bash
workdir=$(mktemp -d)
git clone <REPOSITORY_URL> "$workdir/repo"
mkdir -p "$HOME/.codex/skills"
cp -a "$workdir/repo/skills/comsol-slurm-run" "$HOME/.codex/skills/"
rm -rf -- "$workdir"
```

Invoke `$comsol-slurm-run` or ask to run and record a COMSOL study in organization storage. An explicitly requested installed skill is intentional persistent content; a disposable clone is not. This repository does not include tests or example scientific data.

## SSH config and keeping credentials outside the agent

The **user**, outside the agent, edits `~/.ssh/config` and replaces the placeholders locally. Do not commit the resulting configuration:

```sshconfig
Host hpc-org
    HostName <CLUSTER_LOGIN_HOST>
    User <CLUSTER_USER>
    Port <SSH_PORT>
    IdentityFile ~/.ssh/id_ed25519_hpc
    IdentitiesOnly yes
    BatchMode yes
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    StrictHostKeyChecking yes
    ForwardAgent no
    ConnectTimeout 20
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

`IdentityFile` is a **location**, not key contents. Use a WSL/Linux absolute path or `~/.ssh/...`, not a Windows drive path. The user sets `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/config ~/.ssh/id_ed25519_hpc`, verifies the host fingerprint through the provider, and establishes the first connection manually. Never disable host verification or blindly trust an unknown host.

For a passphrase-protected key, the user runs `ssh-add ~/.ssh/id_ed25519_hpc` and enters its passphrase in their own terminal, outside the agent. Subsequent automation uses only the alias:

```bash
ssh -F "$HOME/.ssh/config" hpc-org 'squeue -u "$USER"'
scp -F "$HOME/.ssh/config" model.mph hpc-org:<ORG_UPLOAD_DIRECTORY>/
```

Never read, print or copy private keys, passwords, tokens or license contents. Do not dump environments, use `sshpass`, put credentials in arguments, or forward the SSH agent to the cluster. A local SSH client can use a local signing agent while `ForwardAgent no` remains set.

For **strong isolation**, keep the private key outside the agent-readable filesystem: an OS credential agent, hardware key or separately sandboxed signing service. The user exposes a supported signing socket; `IdentityAgent SSH_AUTH_SOCK` plus `IdentityFile ~/.ssh/id_ed25519_hpc.pub` can identify the corresponding key in that agent. Confirm client support manually. File permissions alone do not isolate files from a process running as the same OS user. An alias reduces accidental disclosure; filesystem isolation or a protected signing service creates the real access boundary. The workflow needs signing capability, never key material.

## Organization storage and billing

All persistent inputs, submissions and outputs belong to an existing organization workspace beneath `/org`:

```text
<ORG_ROOT>/
├── models/comsol/uploads/        # original uploads
└── run_records/comsol/
    ├── <unique-run-id>/          # snapshot, result, logs, metadata, source scripts
    ├── script_backups/           # annotated sbatch snapshots
    └── agent_training/
        ├── records/<run-id>.json
        └── runs.jsonl
```

The helper rejects organization roots outside `/org`. `--account` explicitly chooses organization billing; storage location alone does not select an account. Supply site-approved partition/QoS values. Selecting a CPU partition does not pin a physical node. The existing COMSOL executable/license can remain at their installation location and are never copied to the repository. Do not save remote file-tree reports unless requested.

## Upload and submit

Do not relocate a file still being uploaded. Prefer transferring to `.uploading`, then renaming to `.mph` after successful transfer. CRC checks, stable size/mtime and snapshot hashes protect against incomplete/changed uploads. Do not clean unrelated upload directories.

Stage the installed skill temporarily on the login host. Replace all angle-bracket values deliberately with local site values; no credential is a parameter. This example keeps persistent files in organization storage and removes transfer/staging artifacts:

```bash
skill_dir="$HOME/.codex/skills/comsol-slurm-run"
archive=$(mktemp --suffix=.tgz)
trap 'rm -f -- "$archive"' EXIT
tar -czf "$archive" -C "$skill_dir/.." comsol-slurm-run
remote_stage=$(ssh hpc-org 'mktemp -d /tmp/comsol-skill-XXXXXXXX')
scp "$archive" "hpc-org:$remote_stage/skill.tgz"
ssh hpc-org "bash -s -- '$remote_stage'" <<'REMOTE'
set -eu
stage=$1
trap 'rm -rf -- "$stage"' EXIT
tar -xzf "$stage/skill.tgz" -C "$stage"
PYTHONDONTWRITEBYTECODE=1 python3 "$stage/comsol-slurm-run/scripts/prepare_run.py" \
  --source '<ORG_ROOT>/models/comsol/uploads/<MODEL>.mph' \
  --org-root '<ORG_ROOT>' --comsol '<COMSOL_EXECUTABLE>' \
  --account '<ORGANIZATION_ACCOUNT>' \
  --partition '<CPU_PARTITION>' --qos '<CPU_QOS>' \
  --cpus 48 --memory-gib 64 --walltime 24:00:00 --study std1 --submit
REMOTE
```

The organization root must resolve below `/org`. Resource values are configurable examples, not universal site limits. One node, one Slurm task and multiple shared-memory COMSOL threads are used. `-np` and `OMP_NUM_THREADS` match allocated CPUs; `srun --cpu-bind=cores` binds work to the allocation. Scaling depends on solver, bandwidth, memory and licenses; more cores do not guarantee proportional speedup.

Without `--submit`, preparation validates the MPH/study, copies a hash-verified snapshot, and checks Python/Bash syntax. With it, `sbatch --test-only` validates resources; one held job is created, its ID/config/backups are saved, then it is released. Validation is not computation or a guarantee of immediate allocation. On an uncertain response or release error, inspect `submission.txt` and the queue before retrying: the job may already exist.

Runtime sources are copied into the organization run directory before the temporary stage disappears. If transport is interrupted before the remote trap starts, remove only the exact stage created by this invocation after confirming it is unused. The local archive trap removes its packaging file.

## How recording works

1. **Input provenance:** originals stay in models; a unique run receives an input snapshot and SHA256. Output is `<input-stem>_result.mph`, never the input.
2. **Discretization:** supported MPH files are ZIP archives containing `smodel.json`, `model.xml` and `fileversion`. The collector preserves full settings and extracts explicitly saved values such as `order_displacement`, `order_temperature` and `discType`. Missing means unobserved, not first order. A format change requires adapting the collector rather than guessing.
3. **Mesh:** a Java helper calls COMSOL mesh APIs without remeshing/solving. It records vertices and each element type, separately summing tetrahedra, hexahedra, prisms and pyramids as 3D volume elements. For 2D/1D use the corresponding element-type counts; a zero 3D total does not mean no mesh. Saved input counts may differ from a mesh regenerated/adapted during solving.
4. **Study:** `batch -study <tag>` uses stored settings without changing tolerances or solvers. Raw output retains solved DOFs and solver tables. DOFs must not be inferred from mesh counts or polynomial order.
5. **Resources:** every 15 seconds the monitor reads the entire job's Slurm cgroup v2, including `srun` solver steps. Sampling only the batch shell PID misses solver work. If no readable Slurm `step_*` cgroup ancestor exists, the collector refuses host-wide statistics. Monitor startup failure stops the run before solving. Different site cgroup layouts require an adapted collector.
6. **Finalization:** an EXIT trap stops sampling, saves measured intervals and records, then cleans known scratch. In-trap `sacct` may still say RUNNING/COMPLETING, so refresh after terminal completion.

CPU is `100 × ΔCPU_seconds / Δwall_seconds`: 100% means one full core. Divide by allocated CPUs for allocation utilization; 100% there means the whole allocation. Sampling can miss short spikes. Cgroup memory includes file/page cache; anonymous memory is separate. Slurm MaxRSS is a task/step observation and not necessarily the job's aggregate peak.

## Artifacts and convergence semantics

| Artifact | Evidence |
|---|---|
| `batch.log` | Raw solve output, DOFs, errors and iteration tables |
| `model_metadata.txt`, `model_settings.json`, `model_info.xml` | Input provenance, explicit discretization, saved metadata |
| `mesh_statistics.txt` | Saved input mesh counts from Java API |
| `resource_usage.txt` | Timestamped CPU, memory, anonymous memory and page cache |
| `solver_iterations.txt`, `solver_trace.jsonl` | Original headers, sections and parameter context |
| `run_report.txt`, `final_status.txt` | Human-readable progress/final observations |
| `run_timing.json` | Measured job/solve-step intervals, distinct from solver-reported time |
| `run_record.json` | Structured model, mesh, DOF, resources, timing and result |
| `slurm_accounting.txt`, `slurm_resources.txt` | Scheduler and step observations |
| Config, sbatch, runtime source, exit codes | Reproducible invocation/provenance |
| `cleanup_summary.json` | Names of removed intermediates |

Preserve `Iter` vs `Step`, column names, sections, continuation parameters and subgroup lines. Linear residual, nonlinear error estimate, damping and transient step size are different quantities; never label an arbitrary column a residual. Missing evidence remains missing. Native return code 0 does not prove convergence: also inspect error markers, completion evidence, saved output and scheduler state. Physical validity remains unassessed. Failed runs remain observations in the training index; an output file is not automatically a success label.

## Check, finalize and clean

```bash
ssh hpc-org 'squeue -j <JOB_ID>'
ssh hpc-org 'tail -n 40 "<RUN_DIRECTORY>/batch.log"'
ssh hpc-org 'tail -n 10 "<RUN_DIRECTORY>/resource_usage.txt"'
# After completion, stage the skill again; execute on the login host:
python3 '<STAGED_SKILL>/scripts/finish_run.py' '<RUN_DIRECTORY>'
```

`finish_run.py` requires queue absence plus explicit terminal `sacct` state. It refreshes accounting and the file-locked training index, and cleans only after consolidated records exist.

**Keep:** originals, input snapshots, results, nonempty logs, settings, mesh/discretization/DOF/resource/timing observations, source and annotated sbatch scripts, training data. These are intentional scientific/reproducibility outputs. **Remove:** transfer/staging files, exact node-local scratch directory, recovery/checkpoint folders, model status/lock files, compiled Java output, Python caches, phase/epoch scratch, empty diagnostic logs. Never clean an active run or unrelated paths. Adapt policy before submission if checkpoints are explicitly requested.

Normal completion, solver failure and handled termination run cleanup. SIGKILL, node failure or hard limits can bypass traps. If consolidated timing/records are missing, recover evidence from epoch files/logs/accounting first; the helper refuses destructive cleanup without it. Unreachable node scratch may need provider cleanup. Do not claim unverified cleanup or install unsolicited background/cross-session watchers.

## Privacy and publication

Publish only the English skill, generic runtime sources and bilingual documentation. No tests/fixtures, scientific models, raw logs, records, actual host/account/user/job identifiers, concrete site paths, SSH configs, licenses or secrets. Scan the exact upload set, not just tracked files. Runtime records contain site metadata and remain private. Compare uploaded content with local hashes, then delete the disposable local repository and archives when requested. Do not delete unrelated user files or a separately requested installed skill.
