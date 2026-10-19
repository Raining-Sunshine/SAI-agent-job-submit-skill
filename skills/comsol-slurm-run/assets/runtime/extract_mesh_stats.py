from pathlib import Path
import sys
d=Path(__file__).resolve().parent
texts="\n".join(p.read_text(errors="replace") for p in [d/"metadata_batch.log",*d.glob("slurm-*.out")] if p.exists())
if "MESH_STATISTICS_BEGIN" not in texts or "MESH_STATISTICS_END" not in texts:
 (d/"metadata_exit_code").write_text("1\n")
 raise SystemExit("Mesh statistics markers missing; inspect metadata_batch.log")
out=texts.split("MESH_STATISTICS_BEGIN",1)[1].split("MESH_STATISTICS_END",1)[0].strip()
(d/"mesh_statistics.txt").write_text(out+"\n")
(d/"metadata_exit_code").write_text("0\n")
