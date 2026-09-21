"""Server-rendered concept practice with anonymous completion receipts."""
from html import escape as e

BASE = '/ml-check'


def student_lesson_path(lesson_id: str) -> str:
    """Map question-bank C/S identifiers to the public lesson-NN layout."""
    if lesson_id.startswith('C') and lesson_id[1:].isdigit():
        number = int(lesson_id[1:])
    elif lesson_id.startswith('S') and lesson_id[1:].isdigit():
        number = int(lesson_id[1:]) + 2
    else:
        return lesson_id
    return f'lesson-{number:02d}'


def lesson_display_label(lesson_id: str) -> str:
    path = student_lesson_path(lesson_id)
    if path.startswith('lesson-') and path[7:].isdigit():
        return f'第 {int(path[7:]):02d} 课（{lesson_id}）'
    return lesson_id


def layout(title, body):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · 机器学习概念练习</title><link rel="stylesheet" href="{BASE}/assets/site.css"></head>
<body><header class="site-header"><a class="brand" href="{BASE}/"><span class="brand-mark">ML</span><span>机器学习<span class="brand-sub">概念练习</span></span></a>
<nav aria-label="站点导航"><a href="{BASE}/">全部课次</a><a href="https://github.com/h-lu/machine-learning-course">课程教材 ↗</a></nav></header>
<main>{body}</main><footer>现代机器学习项目课 · 先判断，后核对，再换一个场景。<span>练习帮助理解概念，不替代项目中的实验与论证。</span></footer></body></html>'''


def home(bank):
    lessons = bank['lessons']
    count = sum(len(x['questions']) for x in lessons)
    groups = {}
    for lesson in lessons:
        groups.setdefault(lesson['module'], []).append(lesson)
    body = f'''<section class="hero"><div class="eyebrow">学习从一个自己的判断开始</div><h1>先想一想，<br>再检查为什么。</h1><p class="lead">用一个短问题检查理解，再把概念带到不同情境。<br>选一课开始，不必追求一次全对。</p><div class="facts"><span><b>{len(lessons)}</b> 次课</span><span><b>{count}</b> 道概念题</span><span><b>A / B</b> 两轮练习</span></div></section>
<section class="how" aria-label="练习顺序"><div><span class="step">01</span><h2>先作判断</h2><p>完成 A 轮五道题，想清楚选它的理由。</p></div><div><span class="step">02</span><h2>核对与学习</h2><p>阅读解释，用 AI 或学习卡弄懂疑惑。</p></div><div><span class="step">03</span><h2>换个场景再试</h2><p>完成 B 轮五道题，看看同一个概念能否用在新问题上。</p></div></section>
<div class="section-heading"><div><div class="eyebrow">32 次课的学习路径</div><h2>从今天的课开始</h2></div><a href="https://github.com/h-lu/machine-learning-course/tree/main/course-student-template">查看项目任务 ↗</a></div>'''
    for index, (name, rows) in enumerate(groups.items(), 1):
        body += f'<section class="module"><h3><span>{index:02}</span>{e(name)}</h3><div class="cards">'
        for lesson in rows:
            id = lesson['lesson_id']
            label = lesson_display_label(id)
            body += f'<a class="card" href="{BASE}/lessons/{e(id)}"><span class="lesson-id">{e(label)}</span><h4>{e(label)} · {e(lesson["title"])}</h4><span class="card-bottom">A 轮 5 题 · B 轮 5 题 <span aria-hidden="true">↗</span></span></a>'
        body += '</div></section>'
    return layout('选择一课开始', body)


def phase_tabs(lesson, phase):
    id = e(lesson['lesson_id'])
    return '<nav class="phase-tabs" aria-label="选择练习轮次">' + ''.join(
        f'<a {"aria-current=page" if p == phase else ""} href="{BASE}/lessons/{id}?phase={p}">{label}</a>'
        for p, label in [('A', 'A 轮 · 先作判断'), ('B', 'B 轮 · 换个场景')]) + '</nav>'


def lesson_page(lesson, phase='A', answers=None, receipt=None):
    questions = [q for q in lesson['questions'] if q['phase'] == phase]
    label = lesson_display_label(lesson["lesson_id"])
    body = f'<a class="back" href="{BASE}/">← 全部课次</a><div class="lesson-header"><div class="eyebrow">{e(label)} · {e(lesson["module"])}</div><h1>{e(label)} · {e(lesson["title"])}</h1><p>先选择你认为合理的答案，提交后核对解释。每轮五道题。</p></div>'
    body += phase_tabs(lesson, phase)
    if answers is not None:
        correct = sum(answers[q['id']] == q['answer'] for q in questions)
        heading = '这轮判断都与题目依据一致' if correct == len(questions) else f'有 {len(questions)-correct} 道题值得再想一想'
        body += f'<section class="feedback-banner" role="status"><div class="eyebrow">已核对 {len(questions)} 道题</div><h2>{heading}</h2><p>看看下面的解释，再判断原来的理由是否需要修改。</p></section>'
        if receipt:
            rid = e(receipt['receipt_id'])
            body += f'<p class="receipt" role="status">已生成完成凭据：<a href="{BASE}/api/receipts/{rid}">{rid}</a>。它只记录课次、轮次、得分和提交时间，不包含你的答案。</p>'
    body += f'<form method="post" action="{BASE}/lessons/{e(lesson["lesson_id"])}/check"><input type="hidden" name="phase" value="{phase}">'
    for number, q in enumerate(questions, 1):
        body += f'<fieldset class="question"><legend><span class="question-number">{e(q["id"])} · {number:02}</span>{e(q["prompt"])}</legend><div class="options">'
        for i, option in enumerate(q['options']):
            selected = answers is not None and answers[q['id']] == i
            mark = 'checked' if selected else ''
            body += f'<label class="option"><input type="radio" name="{e(q["id"])}" value="{i}" required {mark}><span class="option-letter">{"ABCD"[i]}</span><span>{e(option)}</span></label>'
        body += '</div>'
        if answers is not None:
            matched = answers[q['id']] == q['answer']
            body += f'<div class="explanation {"matched" if matched else "rethink"}"><strong>{"你的判断有依据" if matched else "重新看看这个条件"} · 参考选项 {"ABCD"[q["answer"]]}</strong><p>{e(q["explanation"])}</p></div>'
        body += '</fieldset>'
    body += '<div class="submit-row"><button type="submit">' + ('再次核对' if answers is not None else '提交并查看解释') + '</button><span>练习不直接计项目分；提交会生成匿名完成凭据。</span></div></form>'
    if answers is not None:
        if phase == 'A':
            body += f'<section class="next-step"><h2>弄懂疑惑，再换一个场景</h2><p>请 AI 用一个不同的小例子解释你仍不理解的地方，或者回到本课学习卡核对。不要只记住选项字母。</p><a class="button" href="{BASE}/lessons/{e(lesson["lesson_id"])}?phase=B">开始 B 轮 →</a></section>'
        else:
            student_path = student_lesson_path(lesson["lesson_id"])
            body += f'<section class="next-step"><h2>把理解带回你的项目</h2><p>检查自己的数据、指标和建议是否也有类似问题。需要时修改原来的判断，并说明理由。</p><a class="button" href="https://github.com/h-lu/machine-learning-course/tree/main/course-student-template/{e(student_path)}">返回本课项目 ↗</a></section>'
    return layout(lesson['title'], body)


def error_page(message):
    return layout('检查一下再继续', f'<section class="hero"><div class="eyebrow">暂时不能继续</div><h1>检查一下再继续</h1><p class="lead">{e(message)}</p><a class="button" href="{BASE}/">返回课次列表</a></section>')
