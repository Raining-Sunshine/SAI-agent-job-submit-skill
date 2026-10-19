"""Delete only this run's known intermediates, after its observations are saved."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def clean(run, inside_job=False):
    run = Path(run).resolve()
    cfg = json.loads((run / 'run_config.json').read_text())
    if not run.is_relative_to(Path(cfg['records_root']).resolve()):
        raise ValueError('Run is outside the configured records root')
    if not inside_job:
        active = subprocess.run(['squeue', '-h', '-j', cfg['job_id']],
                                capture_output=True, text=True)
        if active.returncode or active.stdout.strip():
            raise RuntimeError('Cannot confirm job is absent from queue; cleanup refused')
    for name in ('run_record.json', 'run_timing.json'):
        json.loads((run / name).read_text())
    # Model files, nonempty logs, scripts, metadata, and training data are retained.
    fixed = {'monitor.stop', 'phase.txt', 'metadata_exit_code',
             'job_start_epoch', 'job_end_epoch', 'solve_start_epoch', 'solve_end_epoch',
             'InspectModel.class', 'InspectModel.class.status'}
    model_names = [cfg['input_model'], cfg['output_model']]
    fixed.update(n + suffix for n in model_names
                 for suffix in ('.status', '.recovery', '.lock'))
    removed = []
    for path in list(run.iterdir()):
        empty_log = (path.name in {'monitor.log', 'metadata_compile.log'}
                     or (path.name.startswith('slurm-') and path.suffix == '.err'))
        eligible = path.name in fixed or path.name in {'recovery', '__pycache__'}
        eligible |= empty_log and path.is_file() and path.stat().st_size == 0
        if not eligible or path.is_symlink():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(path.name)
    (run / 'cleanup_summary.json').write_text(json.dumps(
        {'removed_intermediates': removed}, indent=2) + '\n')
    return removed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inside-job', action='store_true')
    parser.add_argument('--run', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if args.inside_job:
        import os
        cfg = json.loads((args.run / 'run_config.json').read_text())
        if os.environ.get('SLURM_JOB_ID') != str(cfg.get('job_id')):
            raise RuntimeError('Inside-job cleanup requires the matching Slurm job')
    print(json.dumps(clean(args.run, args.inside_job)))
