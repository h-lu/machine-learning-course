# C02冷读与运行验收（2026-10-09）

## 范围和证据类型

材料在独立本地副本 `ml-course-redesign`，原课归档/原库只读。这里是作者模拟初学者阅读与实际命令演练，**没有真人试读/试教**；不能证明真实学生已在65分钟完成。正式开放项目没有唯一程序或参数，验收分别检查起点可读、自由构建可行和教师独立数学核算，不能把默认文件存在称作标准项目完成。

实际环境Python3.14、NumPy2.5，默认实验离线。共享数据SHA256 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`。原始CSV字节未改，训练13,003/验证2,208，封存2,168条没有评价。

## 学生页模拟冷读

- **首次动作**：README首屏自行写用途/选择一条开发记录，再需要时用SUPPORT数据卡运行默认起点；没有要求先读完别的页面。
- **动作前必要词**：一行一个系统小时，输入/目标/预测分开；数据字典解释temp非摄氏度，cnt非库存，CSV/JSON在SUPPORT就地解释。
- **目录、输入、输出**：学生根执行 `python3 lesson-02/analysis.py`，读取本课config与共享hour.csv，输出本课artifacts/starter。显式输出路径支持学生根lesson前缀或本课相对路径。
- **成功后先看**：sample.csv的instant/datetime/partition；sample仅6train+6validation。再看baseline.json的training_rows、prediction、validation_mae、mae_denominator；这是训练均值参照，无候选比较。
- **手算对象/单位/分母**：LEARN不同情境人工小表给完整例题、半提示、独立题；正式编号由学生选，正式MAE按该方法实际评价条数，不跨方法相加。
- **改变设置/比较**：没有统一配方。主任务至少两个决策会影响实验或建议，支持卡不替学生选候选/参数/阈值/失败组；多项改动需如实列出。
- **失败时保留**：原配置、报错、已生成产物；显式已有目录换新名称；手算标尚未运行，后补程序，不拿示范当实际结果。
- **报告与提交**：report提示可重组、关键证据不可漏；submission默认仅起点，完成时改为自己的程序和真实证据。CI只重算清单，不冒称核全部试验。

冷读中修正了旧稿强制编号/参数顺序、跨方法分母描述、02不存在完整基线CSV的说明、默认状态含义及环境链接。学生README第三节为“课堂任务”，不写分钟预算；教师保10/65/15。

## 实际执行的命令

从学生根执行，退出码均0：

```bash
python3 lesson-02/analysis.py
python3 scripts/course.py run 02
```

SUPPORT的薄reader片段临时保存到本课目录并实际运行，输出 `13003 2208`，随后删除仅验收临时文件。起点科学产物重复运行SHA256一致，sample共12行，summary.status仍not_started。数据审计和起点不代表学生完成标准项目。

从总工作区执行，退出码均0：

```bash
python3 course-instructor/reference/C02/verify.py
python3 course-instructor/reference/C02/simulate_open_project.py
```

[独立核算结果](../../reference/C02/verification.json)用原CSV独立算式核数学；[开放选择模拟](../../reference/C02/open-project-smoke/summary.json)借薄工具、自己构建不同规则/组/阈值，实际保存逐条证据。此模拟是作者示例，不是学生作业或课堂效果调查。共享跨三课起点证据见 [OPEN_STARTER_01_03_VERIFICATION.json](../../reference/OPEN_STARTER_01_03_VERIFICATION.json)。

## 未完成与限制

未真人试教，不能保证65分钟完成率；没有上传、部署或替换历史题库场次。此页不宣布原全课程旧toy测试适用于新真实课包。文档链接/题库结构检查与实际数学核算分别报告；具体项目解释仍由教师依据GRADING阅读。
