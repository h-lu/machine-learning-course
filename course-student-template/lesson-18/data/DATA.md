# S16 数据说明：短资料、查询与检索标注

本课的三份 `documents` 是课程人工编写的短资料。`id` 是资料编号，`text` 是完整文字，`units` 是允许回答器逐字抽取的句子。程序不会调用网络，也不会使用隐藏知识。

每条 `queries` 是一个问题。`search_terms` 是已经切分好的检索词；程序计算这些词在每份资料中出现了几个。`expected_document` 只用于课后评价检索是否找到正确资料，不参与排序。空的 `expected_document` 表示这三份资料无法回答，应返回“资料不足”。

`data/base.json` 只有 5 条 `development` 查询，可反复用于调整 `min_overlap`。`data/final.json` 包含同样的三份短资料和 4 条 `final` 查询，只在规则选好后使用。默认 `submission.json` 只读取 `base.json`；复制 `submission-final.json` 后才会显式读取 `final.json`。公开仓库中的 final 文件不是技术保密；提前查看后必须如实称为开发证据。

程序会在资料或查询改变后重新检索，并让回答步骤接收本次实际找到的句子。它验证的是小型检索流程，不代表关键词重合能理解所有中文，也不代表真实大模型的生成能力。
