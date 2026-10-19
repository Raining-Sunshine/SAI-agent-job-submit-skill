# COMSOL 组织目录 Slurm 提交与记录 skill

[English](README.md)

仓库提供英文 skill 和 Python/Bash 通用脚本。示例全部参数化，不含真实服务器、账户、用户名、具体个人/组织路径、凭据、许可证、模型、测试文件或运行记录。实际计算与训练数据只保存在组织存储，不进入本仓库。

## 环境与安装

需要 WSL/Linux OpenSSH、远端 Python 3.9+、HPC作业管理系统为Slurm、已有许可证的软件 和匹配的 Java API、可写组织空间，以及计算节点上可读的 Slurm 作业 cgroup v2。Python 仅依赖标准库。

用户先在代理之外完成 GitHub 身份验证。私有仓库使用已有登录或 SSH agent，不把 token 写到 clone URL。只安装 skill 子目录，随后删除临时仓库副本：

```bash
workdir=$(mktemp -d)
git clone <REPOSITORY_URL> "$workdir/repo"
mkdir -p "$HOME/.codex/skills"
cp -a "$workdir/repo/skills/comsol-slurm-run" "$HOME/.codex/skills/"
rm -rf -- "$workdir"
```

通过 `$comsol-slurm-run` 调用，或要求代理在组织目录运行并记录研究细节。用户明确安装的 skill 是保留工具；临时 clone 是应删除的工作副本。本仓库没有测试文件或示例科学数据。

## SSH config：用户配置，代理只调用别名

**由用户在代理以外的终端**编辑 `~/.ssh/config`，在本地替换占位符，实际配置不得提交到仓库：

```sshconfig
Host hpc-org
    HostName <CLUSTER_LOGIN_HOST>
    User <CLUSTER_USER>
    Port <SSH_PORT>
    IdentityFile <FILE_PATH>
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

`IdentityFile` 填写密钥文件的**位置**，不写密钥内容。WSL 中使用 Linux 绝对路径或 `~/.ssh/...`，不能直接使用 Windows 盘符路径。用户设置 `chmod 700 ~/.ssh` 和 `chmod 600 ~/.ssh/config ~/.ssh/id_ed25519_hpc`，通过服务商可信渠道核对服务器主机指纹，再手动建立首次连接。不关闭主机验证，不盲目信任未知主机。

有口令的密钥由用户在自己的终端执行 `ssh-add ~/.ssh/id_ed25519_hpc` 并输入口令，代理不参与。之后代理只执行：

```bash
ssh -F "$HOME/.ssh/config" hpc-org 'squeue -u "$USER"'
scp -F "$HOME/.ssh/config" FILE_PATH hpc-org:<ORG_UPLOAD_DIRECTORY>/
```

代理不得读取、打印或复制私钥、密码、token 或许可证内容；不得转储环境变量、使用 `sshpass`、把凭据写入命令行，或把 SSH agent 转发到集群。`ForwardAgent no` 不影响本地 SSH 客户端使用本地签名代理。

如需**强隔离**，私钥应位于代理不可读的位置，例如操作系统凭据代理、硬件密钥或独立沙箱签名服务。用户提供客户端支持的签名 socket，并可配置 `IdentityAgent SSH_AUTH_SOCK` 和 `IdentityFile ~/.ssh/id_ed25519_hpc.pub`，用公钥选择签名代理中的对应身份；先由用户核对支持情况。仅靠 chmod 无法阻止以同一操作系统用户运行的程序读取该用户的文件。SSH 别名减少误泄露；真正权限边界来自文件系统隔离或受保护的签名服务。工作流只需要签名能力，不需要密钥内容。

## 组织目录与组织计费

所有持久输入、作业提交和结果都放在 `/org` 下已存在的组织工作空间：

```text
+
```

个人 home 不作为提交和持久结果目录。COMSOL 程序和许可证继续引用原有安装位置，不复制到仓库。脚本拒绝 `/org` 外的组织根目录；必须同时通过 `--account` 指定组织计费，文件存放位置本身不代表计费账户。分区和 QoS 来自站点批准配置；指定 CPU 分区不等于锁定某台物理节点。文件树默认只在聊天中输出，不额外保存到服务器。

## 上传和提交命令

不移动仍在上传的文件。建议先上传为 `.uploading`，传输成功后再改为 `.mph`。准备阶段结合 ZIP CRC、大小/修改时间及快照哈希检查完整性和文件变化。不批量清理上传目录。

将安装的 skill 临时传到登录节点，替换以下占位符。真实站点配置不进入仓库，凭据不作为命令行参数：

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

`<ORG_ROOT>` 必须替换成 `/org` 下的实际组织空间。48 核、64 GiB、24 小时和 `std1` 是示例，不是通用固定要求。采用单节点、单 Slurm task 的共享内存多线程计算，`-np` 和 `OMP_NUM_THREADS` 对应申请核数，`srun --cpu-bind=cores` 绑定分配的核心。效率受求解器、内存、带宽与许可证影响，不能假定增加核心会等比例提速。

不加 `--submit` 只准备和验证文件。加上后先 `sbatch --test-only` 验证调度请求，再以 hold 创建一次作业，写入作业号、配置和脚本备份后释放。验证不是正式求解，也不保证马上分配资源。提交响应或 release 不确定时先查 `submission.txt` 和队列，避免重复提交已经存在的作业。

远端 stage 删除前，运行源码已复制到组织运行目录；本地打包文件由 trap 删除。若传输在远端 trap 启动前中断，确认无进程使用后，仅删除本次创建的确切 stage 目录。

## 记录原理

1. **来源可复核。** 上传原件留在 models，唯一运行目录保存输入快照及 SHA256。输出为 `<input-stem>_result.mph`，不覆盖输入。
2. **离散化来自显式设置。** 支持的 MPH 格式是包含 `smodel.json`、`model.xml`、`fileversion` 的 ZIP。保留完整设置，提取 `order_displacement`、`order_temperature`、`discType` 等显式属性。缺失表示未观测，不能当作一阶。格式变化需要适配，不猜默认值。
3. **网格通过 Java API 读取。** 辅助程序只读保存的输入网格，不重划、不求解。记录顶点和每种单元数，单独累计四面体、六面体、棱柱、棱锥等三维体单元。二维/一维模型应看对应单元类型，三维体单元为零不代表没网格。求解时若重建或自适应网格，实际求解网格可能不同，应保留来源区分。
4. **研究沿用模型设置。** `batch -study <tag>` 不擅自更改容差和求解器。自由度从实际求解日志记录，不能从单元数或阶次反推替代。
5. **资源按整个作业采集。** 每 15 秒读取 Slurm 作业 cgroup v2，覆盖 `srun` 中的 COMSOL，避免只看 shell PID 漏掉计算。找不到可读 `step_*` 祖先时拒绝记录全机数据；监控启动失败会在求解前终止。其他集群 cgroup 布局需要适配。
6. **记录先于清理。** EXIT trap 停止监控、固化时间与结构化记录，再删临时文件。trap 内查询账单可能仍显示 RUNNING/COMPLETING，真正结束后再刷新终态。

CPU 计算为 `100 × CPU累计秒数增量 / 墙钟秒数增量`，一个核心满载是 100%；除以申请核数才是整份 CPU 配额的利用率。cgroup 总内存包含页缓存，匿名内存另列；Slurm MaxRSS 是 task/step 观测，未必等于整份作业内存峰值。15 秒采样可能漏掉短峰，不能宣称准确捕获瞬时最大值。

## 文件与收敛语义

| 文件 | 记录含义 |
|---|---|
| `batch.log` | 原始求解输出、DOF、错误和迭代表格 |
| `model_metadata.txt`、`model_settings.json`、`model_info.xml` | 来源、阶次和完整模型元数据 |
| `mesh_statistics.txt` | 保存输入网格的 Java API 统计 |
| `resource_usage.txt` | 带时间戳的 CPU、作业内存、匿名内存与页缓存 |
| `solver_iterations.txt`、`solver_trace.jsonl` | 原始表头、区段和参数上下文 |
| `run_report.txt`、`final_status.txt` | 可读进度与终态观测 |
| `run_timing.json` | 实测作业/求解步骤耗时，与求解器自报时间区分 |
| `run_record.json` | 模型、网格、DOF、资源、时间与结果结构化记录 |
| `slurm_accounting.txt`、`slurm_resources.txt` | 调度及 step 资源统计 |
| 配置、sbatch、源码、退出码 | 可复现调用和来源证据 |
| `cleanup_summary.json` | 本次删除的中间文件名称 |

保留 `Iter` 与 `Step`、原始列名、求解器区段、延续参数及分组信息。线性残差、非线性误差估计、阻尼、瞬态时间步是不同指标，不能把任意数字列都说成残差。缺失证据保持缺失，不补造。COMSOL 返回 0 不足以证明收敛，还需结合错误标记、完成证据、输出文件和调度状态。记录不代表物理正确性已经验证；失败运行也作为观察数据保留，不能把所有输出都打成功标签。

## 检查、完成和清理

```bash
ssh hpc-org 'squeue -j <JOB_ID>'
ssh hpc-org 'tail -n 40 "<RUN_DIRECTORY>/batch.log"'
ssh hpc-org 'tail -n 10 "<RUN_DIRECTORY>/resource_usage.txt"'
# 完成后重新临时传入 skill，在登录节点执行：
python3 '<STAGED_SKILL>/scripts/finish_run.py' '<RUN_DIRECTORY>'
```

`finish_run.py` 要求作业已离开队列且 `sacct` 为明确终态，再刷新账单、通过文件锁更新训练汇总、执行定点清理。汇总记录必须已存在。

**保留：** 原件、输入快照、结果、非空日志、设置、网格/阶次/DOF/资源/时间记录、源码、带说明的 sbatch 和训练数据。这些是用户要求的科研与复现资料。**删除：** 上传包、stage、确切节点临时目录、恢复/断点目录、状态/锁文件、编译 class、Python 缓存、阶段/epoch 中间文件、空诊断日志。不清理运行中任务或无关路径。若用户明确要求保留断点，提交前调整清理策略。

正常完成、求解失败和可捕获终止会执行清理。SIGKILL、节点故障或硬限制可能跳过 trap；汇总记录/时间缺失时，先从 epoch、日志、账单恢复证据，辅助程序不会直接删掉未固化证据。不可访问节点的临时目录可能需要平台清理，未核实不能声称已删除。本流程不安装后台或跨会话监控守护。

## 脱敏与发布

只发布英文 skill、通用源码和中英文说明。不发布测试/夹具、模型、日志、运行记录、训练数据、实际主机/账户/用户/作业号、具体站点路径、SSH 配置、许可证或秘密。检查所有待上传文件，不能只看 Git tracked。运行生成记录可能含真实站点信息，一直保存在私有组织存储。上传后对比文件哈希，确认完整后删除本地临时仓库与打包文件；不删除无关资料或用户另行要求安装的 skill。
