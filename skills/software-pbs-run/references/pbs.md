# PBS command guidance

These notes target OpenPBS/PBS Professional. Use the target's local manuals and approved scripts to confirm version and site policy; Torque and other implementations require separate adaptation.

## Read-only queries

After confirming the implementation, use `qstat --version` for client identity and `qstat -B` for server status. Query queue settings with `qstat -Qf` when permitted. Successful empty job-list output can mean the user has no visible jobs; transport or scheduler errors do not mean the queue is empty.

Use `qstat -f JOB_ID` for a specific job. Prefer supported structured output, such as `qstat -f -F json JOB_ID`, when available; otherwise preserve wrapped attribute values when parsing text. Handle IDs as quoted strings, including suffixes and array notation.

## Resource selection

For a homogeneous OpenPBS/PBS Professional request, `select=N:ncpus=C:mpiprocs=R:ompthreads=T:mem=M` describes N chunks, each with C CPUs, R MPI processes, T OpenMP threads and memory M. Walltime is a separate resource. Confirm units and site limits before filling values.

Chunks are not necessarily distinct physical hosts. Select the documented `place` policy when distribution matters. For a conventional hybrid allocation, check that R × T does not exceed C. Use the software-supported thread setting as well as the resource request.

The PBS node file may repeat hosts according to MPI process counts; its line count is not a general CPU count. Let the site's compatible launcher use the allocated hosts. Do not deduplicate the node file or pass it blindly to an incompatible MPI launcher.

An older `nodes`/`ppn` example is not sufficient evidence that the same interpretation applies to this server. Verify its variant and supported resource language.

See the [PBS Professional user guide, resource and multiprocessor chapters](https://2021.help.altair.com/2021.1.2/PBS%20Professional/PBSUserGuide2021.1.2.pdf); this is a versioned reference, not a statement about the target's installed version.

## Submission

The script uses `#PBS` directives. Supply the selected queue and the site's required account/project options. Set the working directory explicitly in the script; `PBS_O_WORKDIR` identifies where submission occurred, which must actually be the intended run location before using it. Ensure outputs and logs will be accessible after execution.

Call `qsub` only for an authorized submission. `qsub -h` creates a real held job. For a hold created by this workflow, save its ID and script, then use `qrls -h u JOB_ID` when the authorized submission is ready. Do not release an unrelated hold.

Keep the full returned job identifier and server context. A successful submission means accepted, not running. The submission client's exit status is distinct from the eventual job's exit status.

References: [OpenPBS qsub manual](https://github.com/openpbs/openpbs/blob/master/doc/man1/qsub.1B), [qrls manual](https://github.com/openpbs/openpbs/blob/master/doc/man1/qrls.1B).

## State and history

For ordinary OpenPBS/PBS Professional jobs, Q is queued, H is held, R is running, E is exiting and F is finished. Read scheduler comments and hold/dependency information to explain a delay. Exiting is not a final outcome; finished is not a success label. Array summaries and moved jobs require their own interpretation.

When retained history is available, use `qstat -xf JOB_ID` and inspect `Exit_status` and available usage. History can be disabled or expired. A failed query, moved job or unknown ID is not proof of a successful run. Preserve the full ID and query the appropriate server context.

For another PBS-family implementation, consult its documented state and history semantics before using these mappings. In particular, do not assume every client's `-x` means history.

Reference: [OpenPBS qstat manual](https://github.com/openpbs/openpbs/blob/master/doc/man1/qstat.1B).

## Measurements

Retain available `resources_used` values with their original units and collection source. Requested resources and reported usage are different observations. Use local documentation to establish whether a metric is instantaneous, cumulative or a peak, and whether it covers the entire distributed job. Do not infer missing peaks or sampling histories from a final summary.

For richer collection, use a site-supported job collector on each allocated node. Account for collection overhead within the request and avoid overlapping aggregate and per-node counters.
