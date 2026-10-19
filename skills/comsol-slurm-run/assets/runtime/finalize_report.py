"""Consolidate timing and final observations before scratch cleanup."""
from pathlib import Path
import datetime, json, os
from export_record import export

d = Path(__file__).resolve().parent
log = (d/'batch.log').read_text(errors='replace') if (d/'batch.log').exists() else ''
cfg = json.loads((d/'run_config.json').read_text())
failed = '/*****Error********/' in log or 'Returned solution is not converged.' in log
rc = (d/'exit_code').read_text().strip() if (d/'exit_code').exists() else 'unknown'
if failed:
    status = 'Solver reported failure or nonconvergence.'
elif rc == '0' and 'Saving model:' in log and (d/cfg['output_model']).exists():
    status = 'Output saved without observed solver error; physical validity unassessed.'
else:
    status = 'Run stopped; solver completion not confirmed.'
(d/'final_status.txt').write_text(
    f'Status: {status}\nUpdated: {datetime.datetime.now().astimezone().isoformat()}\n'
    f'Job: {os.environ.get("SLURM_JOB_ID", cfg.get("job_id", ""))}\n'
    f'Script exit code: {rc}\n\n{log[-2500:]}\n')

def epoch(name):
    try: return float((d/name).read_text())
    except (OSError, ValueError): return None

a, b = epoch('job_start_epoch'), epoch('job_end_epoch')
s, e = epoch('solve_start_epoch'), epoch('solve_end_epoch')
timing = {
    'observed_job_start': datetime.datetime.fromtimestamp(a).astimezone().isoformat() if a else None,
    'observed_job_end': datetime.datetime.fromtimestamp(b).astimezone().isoformat() if b else None,
    'observed_job_elapsed_seconds': b-a if a is not None and b is not None else None,
    'solve_step_elapsed_seconds': e-s if s is not None and e is not None else None,
}
(d/'run_timing.json').write_text(json.dumps(timing, indent=2)+'\n')
export(d)
