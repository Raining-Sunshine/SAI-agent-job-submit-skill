import os,time,json,re,signal,datetime,statistics
from pathlib import Path
d=Path(__file__).resolve().parent
cores=int(os.environ.get("SLURM_CPUS_PER_TASK","48"))
cfg=json.loads((d/"run_config.json").read_text())
limit=cfg["memory_gib"]*1024**3
stop=False
def shutdown(*args):
 global stop
 stop=True
signal.signal(signal.SIGTERM,shutdown)
signal.signal(signal.SIGINT,shutdown)
cgtext=Path("/proc/self/cgroup").read_text()
cgpath=next((x.split(":",2)[2] for x in cgtext.splitlines() if x.startswith("0::")),None)
if cgpath is None: raise RuntimeError("Expected cgroup v2; monitoring unavailable")
group=Path("/sys/fs/cgroup"+cgpath)
while group.parent!=group and not group.name.startswith("step_"):
 group=group.parent
if not group.name.startswith("step_"): raise RuntimeError("Slurm step cgroup not found; refusing host-wide metrics")
group=group.parent
def stats(path):
 return {k:int(v) for k,v in (line.split() for line in path.read_text().splitlines())}
def read_sample():
 cpu=stats(group/"cpu.stat")["usage_usec"]/1e6
 mem=int((group/"memory.current").read_text())
 ms=stats(group/"memory.stat")
 return time.monotonic(),cpu,mem,ms.get("anon",0),ms.get("file",0)
samples=[]
prev=read_sample()
f=(d/"resource_usage.txt").open("w",buffering=1)
f.write("# Job "+os.environ["SLURM_JOB_ID"]+"; host "+os.uname().nodename+"; "+str(cores)+" allocated CPU cores; "+str(cfg["memory_gib"])+" GiB allocation\n")
f.write("# CPU_core_percent: 100%=one CPU; CPU_alloc_percent: 100%=all allocated CPUs. Memory cgroup includes page cache; anon primarily process anonymous memory.\n")
f.write("# cgroup="+str(group)+"\n")
f.write("time\tphase\tCPU_core_percent\tCPU_alloc_percent\tcgroup_mem_GiB\tmem_alloc_percent\tanon_GiB\tfile_cache_GiB\n")
def update_report():
 from export_record import solver_tables
 log=(d/"batch.log").read_text(errors="replace") if (d/"batch.log").exists() else ""
 records=solver_tables(log)
 trace=[]; previous=None
 for r in records:
  key=(r["section"],r["parameter_context"],r["header"])
  if key!=previous:
   trace.extend(x for x in key if x)
   previous=key
  trace.append(r["raw"])
  trace.extend(r.get("subgroup_lines",[]))
 (d/"solver_iterations.txt").write_text("\n".join(trace)+"\n")
 meta=(d/"model_metadata.txt").read_text() if (d/"model_metadata.txt").exists() else ""
 mesh=(d/"mesh_statistics.txt").read_text() if (d/"mesh_statistics.txt").exists() else "Mesh statistics not yet available."
 info=[x for x in log.splitlines() if any(t in x for t in ["Number of degrees of freedom","Geometry shape function:","Running on ","Using ","Continuation parameter "])]
 out=["COMSOL batch run record","Updated: "+datetime.datetime.now().astimezone().isoformat(),"Job: "+os.environ["SLURM_JOB_ID"],"Node: "+os.uname().nodename,f"Resources: {cores} CPUs, {cfg['memory_gib']} GiB; sample interval 15 seconds.","Model metadata:",meta,"Saved input mesh:",mesh,"Solver observations:"]+info+["Latest tables (original headers; transient steps are not nonlinear residuals):"]
 previous=None
 for r in records[-10:]:
  key=(r["section"],r["parameter_context"],r["header"])
  if key!=previous:
   out.extend(x for x in key if x);previous=key
  out.append(r["raw"])
 if samples:
  out+=["Allocation CPU utilization sample mean/max: %.2f%% / %.2f%%"%(statistics.mean(s[0] for s in samples)/cores,max(s[0] for s in samples)/cores),"Sampled cgroup memory peak: %.3f GiB"%(max(s[1] for s in samples)/1024**3),"Sampled anonymous memory peak: %.3f GiB"%(max(s[2] for s in samples)/1024**3)]
 if (d/"exit_code").exists():out.append("Script exit code: "+(d/"exit_code").read_text().strip())
 (d/"run_report.txt").write_text("\n".join(out)+"\n")

update_report()
while not stop and not (d/"monitor.stop").exists():
 for _ in range(15):
  if stop or (d/"monitor.stop").exists():break
  time.sleep(1)
 cur=read_sample()
 dt=cur[0]-prev[0]
 pct=max(0,(cur[1]-prev[1])/dt*100) if dt else 0
 samples.append((pct,cur[2],cur[3]))
 phase=(d/"phase.txt").read_text().strip() if (d/"phase.txt").exists() else "starting"
 f.write("%s\t%s\t%.2f\t%.2f\t%.4f\t%.2f\t%.4f\t%.4f\n"%(datetime.datetime.now().isoformat(),phase,pct,pct/cores,cur[2]/1024**3,cur[2]/limit*100,cur[3]/1024**3,cur[4]/1024**3))
 prev=cur
 update_report()
f.close()
update_report()
