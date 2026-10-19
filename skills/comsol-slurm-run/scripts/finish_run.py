#!/usr/bin/env python3
"""Refresh final scheduler observations and clean a confirmed terminal run."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    run = args.run.resolve(strict=True)
    cfg = json.loads((run / 'run_config.json').read_text())
    job = str(cfg['job_id'])
    if not job.isdigit():
        raise ValueError('Invalid job ID')
    queue = subprocess.run(['squeue', '-h', '-j', job], capture_output=True, text=True)
    # Some Slurm releases return an error for expired IDs: use terminal sacct evidence.
    if queue.stdout.strip():
        raise RuntimeError('Job is still in the queue; do not finalize or delete files')
    acct = subprocess.run(['sacct', '-n', '-X', '-j', job, '-o', 'State', '-P'],
                          capture_output=True, text=True, check=True)
    states = [line.strip().split('|')[0].split()[0].rstrip('+')
              for line in acct.stdout.splitlines() if line.strip()]
    terminal = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY',
                'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}
    if not states or any(state not in terminal for state in states):
        raise RuntimeError('No unambiguous terminal accounting state; cleanup refused')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(run))
    from export_record import export
    export(run)
    from clean_intermediates import clean
    # Queue emptiness plus terminal accounting verified above.
    print(json.dumps({'removed': clean(run, inside_job=True)}))


if __name__ == '__main__':
    main()
