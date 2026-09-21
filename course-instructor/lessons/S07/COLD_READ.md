# S07 模拟冷读与命令验收（2026-09-21）

## 验收身份与边界

这是作者按“第一次接触本课、只看学生 README、SUPPORT、LEARN 和数据说明”进行的模拟冷读，并非真人学生试读。受检工作区含未提交改动，因此未记录提交号；正式发布时应补记最终提交。

## 第一项动作与必要术语

第一项动作：打开 records.csv 的 R21 并重算分钟误差。开始前只需要 SUPPORT 第一节就地解释的术语；不需要先读完术语表，也不依赖教师参考答案。

## 实际运行

从学生仓库根目录依次执行：

```bash
python3 scripts/course.py start 09
python3 lesson-09/analysis.py --config lesson-09/config-start.json --output lesson-09/artifacts/start
python3 lesson-09/analysis.py --config lesson-09/config-support.json --output lesson-09/artifacts/support
python3 -m json.tool lesson-09/config-mine.json
python3 lesson-09/analysis.py --config lesson-09/config-mine.json --output lesson-09/artifacts/mine
python3 scripts/course.py run 09
python3 scripts/course.py check 09
```

个人副本只改 SUPPORT 点名的一项设置。生成并逐项打开：summary.json、comparison.csv、records.csv、outside_check.csv。六课起始运行均不足 0.11 秒；普通 CPU 离线通过。随后在临时完整仓库把六课状态设为完成，`python3 scripts/course.py ci` 的逐文件哈希复现全部通过。

## 停顿点与修订

首次程序联调发现 S07 范围外单值数组转换错误，已改为显式取单个数；随后发现 S07 起始表会提前显示测试分数，已改成每次只输出配置指定的验证集或测试集；题库人工检查还发现 S08 一项正确选项原样出现在题干，已改写选项。学生文案中的旧说法已按检查器提示替换。修订后，起点、支持、个人副本、主运行、提交检查和复现均通过。

## 尚未完成的验收

没有进行真人学生 90 分钟试读，不能据此断言所有学生可在规定时间独立完成。正式发布前还需同步在线题库，并由根任务记录最终提交与实际试教时间。
