# S30 冷读与实际运行记录

## 模拟学生冷读

只按学生目录的 README、SUPPORT、LEARN、数据说明、配置和程序阅读，没有先查看教师参考。

- 第一次动作：复制 `config-start.json`，执行 `start 32` 和默认 `run 32`。
- 第一次动作前需要理解：开发数据用于选择方案；最后评价只在候选、指标和停止条件固定后使用。README 首屏直接说明这一区别。
- 默认命令读取 `data/base.json` 和 `config.json`，生成 summary、records 和 manifest。成功后先在 summary 核对 `evaluation_stage=development`，再看 T 编号记录。
- 开发手算单位为一条文字请求；两个方案分母同为 8。开发结果为原方案 6/8、适配方案 8/8，变化请求为 T01、T02。
- 只改变 `release_candidate` 选择；指标、严重条件和停止条件先写入报告，再复制为 `config-final.json`。
- 复制 `submission-final.json` 后，`course.py run 32` 的打印命令显式出现 `--final-data` 和 `config-final.json`。成功后先核对 `evaluation_stage=final_evaluation`，再看 D 编号记录。
- 失败时保留报错和旧输出；开发运行不应依赖 final 文件，最终运行则应核对 final 和固定配置摘要。

阅读中发现的原问题是 `--final-data` 曾默认指向 `data/final.json`，导致学生直接运行程序便提前读取最后评价。现已改为默认 `None`；默认提交只执行开发阶段，最终提交清单才显式传入最后数据。

## 临时学生副本的实际操作

日期：2026-09-21。临时副本：`/tmp/s30-student-lifecycle-wiyjvN/student`。使用 `/usr/bin/python3`；这是模型模拟学生操作和实际命令运行，不是真人试读。

1. 将 `lesson-32/data/final.json` 临时移出原位置，再执行默认 `start 32` 与 `run 32`。运行成功；summary 为 `development`，manifest 没有 `--final-data` 与 `final_data_sha256`。这证明默认路径不读取最后数据。
2. 根据开发输出固定 `library_adapted`，填写 contract、报告中的指标和停止条件，把 `config.json` 复制为 `config-final.json`。
3. 复制 `submission-final.json` 为 `submission.json`，再执行 `course.py run 32`。打印命令显式读取 base、final 和 config-final；summary 为 `final_evaluation`。
4. 最后评价实际结果为原方案 5/8、适配方案 8/8；固定候选结果为 8/8；变化请求为 D01、D02、D06。D04、D07 均送人工，没有触发预先记录的停止条件。
5. 按 manifest 在 `artifacts/replay` 重跑。两个目录中 summary、records、manifest 的 SHA-256 分别完全相同；manifest 的命令把输出目录规范化为 `<OUTPUT_DIR>`。
6. 将提交状态改为 `complete` 后，`python3 scripts/course.py check 32` 通过；`python3 scripts/course.py ci` 在临时副本中删除并重建最终产物后通过。

## 专项软件检查

`python3 -m unittest tests.test_operations_module` 共 14 项通过。测试包含：在临时课程副本中把 final 写成无效 JSON 后默认运行仍成功；删除 final 后默认运行仍成功；显式最终命令读取 final；最终候选切换；manifest 不受输出目录影响；默认和最终 submission 的命令边界。

## 验收限度

这次记录证明文档路径可以按顺序执行、开发与最后评价在程序和提交清单中分开、最终产物可确定性重建。它不能证明真人初学者能在 90 分钟内完成，也不能证明课程人工参考路线符合真实图书馆规定；两项仍需真人试读和业务核对。
