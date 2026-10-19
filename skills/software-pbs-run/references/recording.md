# Resource and solver records

Use this guidance when generating monitoring and finalization scripts for a software job.

## Resource coverage

Prefer the site's scheduler-supported accounting and monitoring interfaces. Optional cgroup collectors must identify the job's actual cgroup on each participating node; a readable host-wide counter is not an acceptable substitute.

Record timestamps, node identity, job or step identity, source and sampling interval alongside measurements. Keep collection failures visible.

For a time interval:

- One-core CPU percentage is `100 × delta CPU seconds / delta wall seconds`.
- Allocation CPU percentage divides that value by the allocated CPU count over the same measured scope.
- For distributed execution, combine non-overlapping CPU time increments across nodes over a common interval, then normalize by the CPUs allocated across those nodes.
- If allocation size changes, calculate utilization using the allocation applicable to each interval.

Document whether CPU counts represent physical cores or logical CPUs according to the cluster configuration.

Memory observations require a scope and definition. Cgroup memory can include page cache; anonymous memory is a separate observation. PBS usage fields depend on the implementation and collection configuration. Preserve their units and documented scope; do not interpret an allocation value as measured usage or an undocumented memory value as a distributed peak. See [PBS measurements](pbs.md#measurements).

For a distributed memory peak, sum samples across nodes at aligned times, then take the peak of that sum. The sum of individual node peaks is a different statistic because those peaks may occur at different times. Report partial coverage when a node or sample is unavailable. Sampling can miss short peaks.

## Solver evidence

Use the software's supported metadata and log interfaces. Preserve original table headings, units, solver sections, study or parameter context and raw lines when extracting data.

Keep saved input mesh statistics separate from the mesh used during the solve. Adaptation or remeshing may change it. Record discretization only when explicitly observed. Record solved degrees of freedom from an appropriate software report; do not substitute an estimate from mesh counts.

Distinguish linear residuals, nonlinear error estimates, damping, transient steps and convergence criteria. Do not map arbitrary numeric columns to a generic residual. If no supported parser exists, retain raw logs and state which metrics were unavailable.

## Timing and outcomes

Keep submission time, queue wait, allocated runtime, solve-step elapsed time and software-reported time separate. Preserve time zones or use a consistent timestamp convention.

Assess outcomes using independent evidence:

- Scheduler terminal state and exit status.
- Software exit status and error or completion messages.
- Presence and integrity of expected outputs.
- Relevant convergence evidence.

Allow failed, cancelled, timed-out, incomplete and unknown outcomes. Scientific validity is a separate assessment from execution success.

## Final record

Use a schema appropriate to the task. Useful fields include:

| Field | Observation |
|---|---|
| Input provenance | Input checksum and snapshot identity |
| Software | Version, invocation and relevant settings |
| Allocation | Account/project when used, queue, chunks, placement, MPI ranks, threads, CPUs and memory semantics |
| Scheduler | Full job ID and server, observed states, array subjobs when relevant and final accounting |
| Timing | Queue, allocation and solve intervals with sources |
| Resources | Per-node or per-step measurements, aggregation method and coverage |
| Solver | Explicit settings, mesh, degrees of freedom and convergence evidence when available |
| Result | Exit codes, completion evidence and expected output checks |
| Artifacts | Submitted script, logs, results and retained checkpoints |
| Cleanup | Temporary artifacts removed and unresolved items |

Store records with the task's results at the selected destination. A shared index is optional; update it atomically if used.

If an exit handler saves provisional observations while the scheduler still reports a running or completing state, refresh the final record after confirmed termination. Do not label provisional accounting as final.
