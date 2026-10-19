"""Export observed COMSOL/Slurm facts; do not infer physical validity."""
from pathlib import Path
import os,sys,json,re,csv,hashlib,datetime,subprocess,fcntl,statistics
def atomic(path,text):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+".tmp."+str(os.getpid()))
 tmp.write_text(text,encoding="utf-8")
 os.replace(tmp,path)
def read(p):
 return p.read_text(errors="replace") if p.exists() else ""
def solver_tables(log):
 records=[]; header=None; section=None; parameter=None
 for line in log.splitlines():
  s=line.strip()
  if s.startswith("<----"):section=s; header=None
  if s.startswith("Continuation parameter "):parameter=s
  if re.match(r"^(Iter|Step)\s+",s):
   header=s
  if re.match(r"^\d+\s+[-+0-9.eE]+\s+[-+0-9.eE]+(?:\s|$)",s):
   vals=s.split(); cols=header.split() if header else []
   records.append({"section":section,"parameter_context":parameter,"header":header,"raw":line,"values":vals,"columns":dict(zip(cols,vals)) if len(cols)==len(vals) else None})
  elif s.startswith("Group #") and records:
   records[-1].setdefault("subgroup_lines",[]).append(s)
 return records
def duration(s):
 if not s:return None
 try:
  days=0
  if "-" in s:
   d,s=s.split("-",1);days=int(d)
  h,m,sec=s.split(":")
  return days*86400+int(h)*3600+int(m)*60+float(sec)
 except (ValueError,TypeError):return None
def digest(p):
 if not p.exists():return None
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def export(d):
 import zipfile
 d=Path(d).resolve()
 cfg=json.loads(read(d/"run_config.json")) if (d/"run_config.json").exists() else {}
 DATA=Path(cfg["records_root"])/"agent_training"
 script=d/"run_study1.sbatch"
 if not script.exists():script=d/"run_study1.sbatch"
 script_text=read(script)
 def directive(k):
  m=re.search(r"^#SBATCH --"+re.escape(k)+r"=(.*)$",script_text,re.M)
  return m.group(1).strip() if m else None
 inp=d/cfg.get("input_model","")
 if not inp.is_file():
  candidates=[p for p in d.glob("*.mph") if not p.stem.endswith("_study1")]
  inp=candidates[0] if len(candidates)==1 else None
 model={"path":str(inp) if inp else None,"sha256":digest(inp) if inp else None,"file_version":None,"physics":[],"studies":[]}
 if inp:
  with zipfile.ZipFile(inp) as z:
   model["file_version"]=z.read("fileversion").decode(errors="replace")
   j=json.loads(z.read("smodel.json"))
  def walk(n):
   if not isinstance(n,dict):return
   cls=n.get("apiClass")
   if cls=="Physics":
    model["physics"].append({"tag":n.get("tag"),"label":n.get("label"),"settings":n.get("settings",[]),"discretization":[s for s in n.get("settings",[]) if any(k in s.get("name","").lower() for k in ["order_","disctype","shape"]) ]})
   if cls in ("Study","StudyFeature"):
    model["studies"].append({"class":cls,"tag":n.get("tag"),"label":n.get("label"),"settings":n.get("settings",[])})
   for n2 in n.get("nodes",[]):walk(n2)
  walk(j)
 job=cfg.get("job_id")
 if not job:
  m=re.search(r"JOBID=(\d+)",read(d/"submission.txt"))
  if m:job=m.group(1)
 if not job:
  matches=list(d.glob("slurm-*.out"))
  if matches:job=matches[0].stem.split("-")[-1]
 acct=[]; acct_error=None
 if job:
  r=subprocess.run(["sacct","-j",str(job),"--format=JobID,State,ExitCode,Start,End,Elapsed,AllocCPUS,MaxRSS,TotalCPU,NodeList","-P"],capture_output=True,text=True,timeout=40)
  atomic(d/"slurm_accounting.txt",r.stdout)
  if r.returncode:acct_error=r.stderr
  else:acct=list(csv.DictReader(r.stdout.splitlines(),delimiter="|"))
 log=read(d/"batch.log")
 errors=[]
 if "/*****Error********/" in log:errors.append(log.split("/*****Error********/",1)[1].split("Saving model:",1)[0].strip())
 failed=bool(errors) or "Returned solution is not converged." in log
 output=d/cfg.get("output_model",((inp.stem if inp else "unknown")+"_study1.mph"))
 complete=(not failed and "Saving model:" in log and output.exists() and ("Total time:" in log or "Time-stepping completed." in log))
 dofs=[{"solved":int(a),"internal":int(b) if b else 0,"source":"batch.log"} for a,b in re.findall(r"Number of degrees of freedom solved for:\s*(\d+)(?:\s*\(plus\s*(\d+)\s*internal DOFs\))?",log)]
 mesh=[]; current=None
 for line in read(d/"mesh_statistics.txt").splitlines():
  m=re.match(r"Component=(\S+) Mesh=(\S+)",line)
  if m:
   current={"component":m[1],"mesh":m[2],"element_counts_by_type":{},"source":"COMSOL Java API, saved input mesh"};mesh.append(current)
  elif current:
   m=re.match(r"Element type (\S+)=(\d+)",line)
   if m:current["element_counts_by_type"][m[1]]=int(m[2])
   for label,key in [("Vertex count=","vertex_count"),("3D volume element count=","volume_element_count"),("COMSOL getNumElem() count=","api_getNumElem_count")]:
    if line.startswith(label):current[key]=int(line[len(label):])
 samples=[]
 sample_text=read(d/"resource_usage.txt")
 data_lines=[s for s in sample_text.splitlines() if not s.startswith("#")]
 if data_lines:
  for s in csv.DictReader(data_lines,delimiter="\t"):
   try:
    s["cpu_alloc_percent"]=float(s["CPU_alloc_percent"]);s["memory_gib"]=float(s["cgroup_mem_GiB"]);samples.append(s)
   except (ValueError,KeyError,TypeError):pass
 root=next((a for a in acct if a.get("JobID")==str(job)),{})
 state=root.get("State")
 if failed:outcome="solver_reported_failure"
 elif complete:outcome="solver_completed_output_saved"
 elif state and any(x in state for x in ["CANCELLED","FAILED","TIMEOUT","OUT_OF_MEMORY"]):outcome="scheduler_stopped_without_confirmed_solution"
 else:outcome="pending_or_running_or_unknown"
 record={"schema_version":"1.0","run_id":d.name,"exported_at":datetime.datetime.now().astimezone().isoformat(),"run_directory":str(d),
 "provenance":{"script_path":str(script),"script_sha256":digest(script),"source_model_path":cfg.get("source_model"),"input_metadata_source":"MPH ZIP: smodel.json / fileversion"},
 "model":model,"requested_resources":{"cpus":int(directive("cpus-per-task")) if directive("cpus-per-task") else None,"memory":directive("mem"),"partition":directive("partition"),"qos":directive("qos"),"account":directive("account"),"study_tag":cfg.get("study_tag","std1")},
 "mesh":mesh,"degrees_of_freedom_observations":dofs,
 "timing":{"measured_intervals":json.loads(read(d/"run_timing.json")) if (d/"run_timing.json").exists() else None,"allocated_elapsed_seconds":duration(root.get("Elapsed")),"comsol_solution_seconds":[float(x) for x in re.findall(r"Solution time:\s*([0-9.]+)\s*s",log)],"comsol_total_seconds":[float(x) for x in re.findall(r"Total time:\s*([0-9.]+)\s*s",log)],"job_start":root.get("Start"),"job_end":root.get("End"),"total_cpu_seconds":duration(root.get("TotalCPU"))},
 "resource_observations":{"source":"resource_usage.txt; job cgroup v2, includes metadata stage and page cache","sample_interval_target_seconds":15,"sample_count":len(samples),"cpu_alloc_percent_sample_mean":statistics.mean(s["cpu_alloc_percent"] for s in samples) if samples else None,"cpu_alloc_percent_sample_max":max((s["cpu_alloc_percent"] for s in samples),default=None),"cgroup_memory_peak_gib":max((s["memory_gib"] for s in samples),default=None)},
 "result":{"outcome":outcome,"physical_validity":"not_assessed","comsol_native_exit_code":read(d/"comsol_exit_code").strip() or None,"script_exit_code":read(d/"exit_code").strip() or None,"time_stepping_completed":"Time-stepping completed." in log,"errors":errors,"output_model":str(output) if output.exists() else None,"output_size_bytes":output.stat().st_size if output.exists() else None},
 "scheduler":{"job_id":job,"accounting_rows":acct,"accounting_error":acct_error},
 "artifacts":{"batch_log":str(d/"batch.log"),"resource_samples":str(d/"resource_usage.txt"),"mesh_statistics":str(d/"mesh_statistics.txt"),"solver_trace_jsonl":str(d/"solver_trace.jsonl"),"input_settings_json":str(d/"model_settings.json")}}
 traces=solver_tables(log)
 atomic(d/"solver_trace.jsonl","".join(json.dumps(t,ensure_ascii=False)+"\n" for t in traces))
 encoded=json.dumps(record,ensure_ascii=False,indent=2)+"\n"
 atomic(d/"run_record.json",encoded)
 atomic(DATA/"records"/(d.name+".json"),encoded)
 DATA.mkdir(parents=True,exist_ok=True)
 with (DATA/".index.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  entries=[json.loads(p.read_text()) for p in sorted((DATA/"records").glob("*.json"))]
  atomic(DATA/"runs.jsonl","".join(json.dumps(v,ensure_ascii=False)+"\n" for v in entries))
 print(json.dumps({"run_id":d.name,"job_id":job,"outcome":outcome,"mesh":mesh,"dofs":dofs,"record":str(d/"run_record.json")},ensure_ascii=False),flush=True)
 return record
if __name__=="__main__":export(sys.argv[1])
