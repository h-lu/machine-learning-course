# 第10课前统一准备，覆盖10–14

1. 从UCI官方ZIP保留原件、readme与SHA，使用tools/prepare_sms.py离线生成固定分组划分。已有本包文件无需重切分。课堂不重新选择种子；近重复审计只用文本，不用标签选阈值。
2. 学生环境Python3.10+、NumPy；第13课新增CPU依赖data/sms/requirements-encoder.txt在课前装好。仓库附已核实的17.5 MB模型，课上不下载。Linux x86_64实测；非AVX2/其他系统应预先实测ONNX可用性，失败时教师准备兼容的真实模型版本并重建全部缓存，不能冒充已有版本。
3. 模型与缓存已含在包中。tools/prepare_encoder_cache.py重建时先核各模型哈希，train/dev/finalholdout分别编码，不按标签调整编码参数。finalholdout原文、标签、缓存不放学生常用入口。保留英文阅读支架，别替换模型输入。
4. 开课前按tools/validate_lessons09_14.py和validation/lessons09-14/REPORT.md核验。抽取两条新英文文本，实跑scripts/sms.py encode，区分模型加载和推理耗时。检查约8GB内存机器可运行，不以作者电脑快代替学生试教。
5. 10–13只用开发结果。14学生交选定系统后，从仓库根运行 `python3 course-instructor/scripts/final_sms.py --system 学生selected目录绝对路径`。一个系统的结果不覆盖；同学事后改阈值/表示等需新的独立评价。脚本只实现留痕，不能阻止公开数据被另行查看。

本包未推送、未部署、未运行GitHub Actions，未变更账号、成绩或历史场次。新60题是新版本，正式启用由后续发布任务负责。学生的提交标签与评分仍沿用原规则。
