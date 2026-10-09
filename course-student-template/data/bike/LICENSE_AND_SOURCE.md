# Bike Sharing：来源、许可与文件审计

作者：Hadi Fanaee-T。数据来自Capital Bikeshare在2011–2012年的小时级记录，由UCI Machine Learning Repository提供。

推荐引用：Fanaee-T, H. (2013). *Bike Sharing* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5W894。

- 官方数据页：https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset
- 官方下载：https://archive.ics.uci.edu/static/public/275/bike%2Bsharing%2Bdataset.zip
- 许可：Creative Commons Attribution 4.0 International（CC BY 4.0），https://creativecommons.org/licenses/by/4.0/ 。保留作者、来源和许可；如果后续修改或派生，说明修改内容。
- 本副本的官方ZIP、`hour.csv`与`Readme.txt`保持原始字节，没有修改CSV或替换缺少的小时。

2026-10-09下载及检查：

| 文件 | 检查 |
|---|---|
| 官方ZIP | 279,992字节；SHA-256 `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401` |
| hour.csv | SHA-256 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`；17,379数据行、17列 |

完整时间为2011-01-01 00:00至2012-12-31 23:00。该网格应有17,544小时，CSV缺165个小时行；没有重复小时或空字段。缺小时不能解释成零需求，也不能称为自然字段缺失。网页显示的17,389条与实际CSV行数不一致，教学审计按文件计数。

固定日期切分：训练 `<2012-07-01` 为13,003行；验证 `[2012-07-01,2012-10-01)` 为2,208行；最后测试 `>=2012-10-01` 为2,168行。天气类别4只有3行，全部在训练部分；验证或测试对此类应写无样本、不可评估，不能写零误差。

`casual + registered = cnt` 在每一行成立。前两列是目标的组成项，不能输入预测`cnt`的模型。`instant`仅为记录编号。日历信息可能事前可取得；实际天气只能用于明确为“给定当小时实际天气的条件需求估计”的场景，不能假装为提前调度时已知。

官方网页与ZIP旧Readme对season的文字标签有冲突。本课程保留原数值 `season_1` 至 `season_4`，不静默改标签或CSV；如后续中文解释，应记录核对依据。
