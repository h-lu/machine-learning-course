# 操作与提交步骤

从学生仓库根目录开始。先确认 Python 3.10 或更高版本，再安装 `requirements.txt` 中的依赖：

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/course.py start 01
python3 scripts/course.py run 01
```

每节课先阅读 `lesson-NN/README.md` 和 `LEARN.md`。在 `contract.json` 写明任务说明、使用者、数据、指标、划分办法和预计结果；在 `report.md` 记录分析、失败案例及修改后的决定；在 `submission.json` 填写运行命令、报告和结果文件。完成后执行：

```bash
python3 scripts/course.py check 01
```

需要发布某课最终版本时，提交后创建标签 `v2-l01-final`（修订用 `v2-l01-revision-1`）。Gitea 工作流会在每次推送时运行格式、单元测试和可复现性检查。
