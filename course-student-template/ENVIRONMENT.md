# 离线环境与第一次运行

先打开完整学生目录：应能看到scripts、mlcourse、data/bike和lesson-01至lesson-08。只复制某一课的analysis.py会缺少共享代码和数据。数据随包提供，课堂无需下载。

需要已准备的Python3.10或以上与NumPy。不同电脑启动命令可能是python、python3或Windows的py；沿用教师已验证的环境。本机2026-10-09使用python3（Python3.14.4、NumPy2.5.2），没有python命令；本次没有安装软件。先在终端运行：

```bash
python3 --version
python3 -c "import numpy; print(numpy.__version__)"
```

若你的电脑使用python或py，把下面命令开头替换成该命令；不要在Python的>>>提示符输入这些终端命令。若未装NumPy，保留报错给教师处理，先做手算；不能将手算写成实验已运行。

所有课程命令从学生目录根运行。例如：

```bash
python3 lesson-01/analysis.py --config lesson-01/config.json --output lesson-01/artifacts/first
```

相对配置和输出路径若含lesson-01，按仓库根解释；每课具体SUPPORT列出完整命令。成功后打开本课点名的CSV/JSON。CSV以逗号分列，可用文本或表格软件查看；JSON是带字段名的结构化记录，可用文本编辑器查看。

显式--output使用新目录，避免覆盖证据；再次运行换成first-2。正式主结果使用各课submission.json中的默认命令，保存最终配置后可重新生成，用于提交复现。默认重建主结果不会替你运行所有候选或填写报告。前1–7不开放最后测试；第8在验证前保存自己的计划、验证后保存选择；只有采用可选示例工具时才需该工具的JSON格式。

找不到文件：核对当前目录及文件名，不追加.txt。配置格式错误：按报错行检查英文引号、逗号和数字。运行失败：保留命令与报错，旧输出不能冒充此次成功。普通CPU即可，代码不需要GPU或付费模型；AI辅导和线上概念检查的网络安排按教师通知，和离线计算分开。
