#!/usr/bin/env python3
"""Prepare a COMSOL run on a Slurm login host; submit only with --submit."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect_model(source, study):
    before = source.stat()
    with zipfile.ZipFile(source) as archive:
        if archive.testzip():
            raise ValueError('MPH archive failed CRC validation; upload may be incomplete')
        settings = archive.read('smodel.json')
        info = archive.read('model.xml')
        version = archive.read('fileversion').decode(errors='replace')
    metadata, studies = [], []

    def walk(node):
        if not isinstance(node, dict):
            return
        kind = node.get('apiClass')
        if kind in ('Physics', 'MeshSequence', 'Study', 'StudyFeature'):
            metadata.append(f"{kind} {node.get('tag')} {node.get('label')}")
            if kind == 'Study':
                studies.append(node.get('tag'))
            for item in node.get('settings', []):
                if any(key in item.get('name', '').lower()
                       for key in ('order_', 'disctype', 'shape')):
                    metadata.append(json.dumps(item, ensure_ascii=False))
        for child in node.get('nodes', []):
            walk(child)

    walk(json.loads(settings))
    if study not in studies:
        raise ValueError(f'Requested study {study} missing; available: {studies}')
    sha = digest(source)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Upload changed during validation; do not submit')
    return settings, info, version, metadata, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--org-root', type=Path, required=True)
    parser.add_argument('--comsol', type=Path, required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--partition', required=True)
    parser.add_argument('--qos', required=True)
    parser.add_argument('--cpus', type=int, default=48)
    parser.add_argument('--memory-gib', type=int, default=64)
    parser.add_argument('--walltime', default='24:00:00')
    parser.add_argument('--study', default='std1')
    parser.add_argument('--submit', action='store_true')
    args = parser.parse_args()
    org = args.org_root.resolve(strict=True)
    if not org.is_relative_to(Path('/org')) or org == Path('/org'):
        raise ValueError('--org-root must be an existing organization workspace under /org')
    source = args.source.resolve(strict=True)
    if not args.comsol.is_file():
        raise ValueError('COMSOL executable not found')
    if args.cpus < 1 or args.memory_gib < 1:
        raise ValueError('CPU and memory allocations must be positive')
    # Directive values cannot contain line breaks, quoting, or shell constructs.
    for value in (args.account, args.partition, args.qos, args.study, args.walltime):
        if not re.fullmatch(r'[A-Za-z0-9_.:+-]+', value):
            raise ValueError('Unsupported scheduler/study parameter')
    if any(c in str(p) for p in (org, source, args.comsol) for c in ('\n', '\r', '"', '`', '$', '\\')):
        raise ValueError('Unsupported path characters')
    settings, info, version, metadata, sha = inspect_model(source, args.study)
    records = org / 'run_records' / 'comsol'
    records.mkdir(parents=True, exist_ok=True)
    if not records.resolve().is_relative_to(org):
        raise ValueError('Run directory resolves outside the organization workspace')
    stamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    safe_stem = re.sub(r'[^A-Za-z0-9_.-]', '_', source.stem)
    run = records / f'{safe_stem}_{args.study}_{args.cpus}cpu_{stamp}'
    run.mkdir(exist_ok=False)
    model = run / source.name
    shutil.copy2(source, model)
    if digest(model) != sha or digest(source) != sha:
        raise ValueError('Source changed while copying; prepared run retained, NOT submitted')
    runtime = Path(__file__).resolve().parent.parent / 'assets' / 'runtime'
    for path in runtime.iterdir():
        if path.is_file() and path.suffix == '.py':
            shutil.copy2(path, run / path.name)
    (run / 'InspectModel.java').write_text(
        (runtime / 'InspectModel.java.in').read_text().replace(
            '__JAVA_MODEL_PATH__', json.dumps(str(model), ensure_ascii=True)))
    output = source.stem + '_result.mph'
    cfg = dict(input_model=model.name, output_model=output,
               source_model=str(source), input_sha256=sha, records_root=str(records),
               study_tag=args.study, memory_gib=args.memory_gib,
               cpus=args.cpus, created_at=dt.datetime.now().astimezone().isoformat())
    (run / 'model_settings.json').write_bytes(settings)
    (run / 'model_info.xml').write_bytes(info)
    (run / 'model_metadata.txt').write_text('\n'.join([
        'Source: ' + str(source), 'Input snapshot: ' + str(model),
        'SHA256: ' + sha, 'COMSOL file version: ' + version, *metadata]) + '\n')
    config_path = run / 'run_config.json'
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
    values = dict(RUNDIR=str(run), COMSOL=str(args.comsol), INPUT=model.name,
                  OUTPUT=output, STUDY=args.study, JOBNAME=f'comsol-{safe_stem[:40]}',
                  ACCOUNT=args.account, PARTITION=args.partition, QOS=args.qos,
                  CPUS=str(args.cpus), MEM=str(args.memory_gib), WALLTIME=args.walltime)
    text = (runtime / 'run.sbatch.in').read_text()
    for key, value in values.items():
        text = text.replace('__' + key + '__', value)
    if re.search(r'__[A-Z_]+__', text):
        raise ValueError('Unrendered template parameter')
    script = run / 'run_study1.sbatch'
    script.write_text(text)
    for path in run.glob('*.py'):
        compile(path.read_text(), str(path), 'exec')
    subprocess.run(['bash', '-n', str(script)], check=True)
    backups = records / 'script_backups'
    backups.mkdir(exist_ok=True)
    shutil.copy2(script, backups / f'{run.name}.sbatch')
    print('PREPARED ' + str(run), flush=True)
    if not args.submit:
        return
    subprocess.run(['sbatch', '--test-only', str(script)], check=True)
    # Hold until the job ID and its immutable script backup are recorded.
    result = subprocess.run(['sbatch', '--hold', '--parsable', str(script)],
                            capture_output=True, text=True, check=True)
    job = result.stdout.strip().split(';')[0]
    if not job.isdigit():
        raise RuntimeError('Unrecognized submission response; inspect queue, DO NOT retry')
    cfg['job_id'] = job
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
    (run / 'submission.txt').write_text(f'JOBID={job}\nRUNDIR={run}\nINPUT_SHA256={sha}\n')
    shutil.copy2(script, run / f'submitted_{job}.sbatch')
    shutil.copy2(script, backups / f'submitted_{job}.sbatch')
    subprocess.run(['scontrol', 'release', job], check=True)
    print('SUBMITTED ' + json.dumps(dict(job_id=job, run_directory=str(run))), flush=True)
    subprocess.run(['python3', str(run / 'export_record.py'), str(run)], check=True)


if __name__ == '__main__':
    main()
