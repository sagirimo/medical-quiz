#!/usr/bin/env python3
"""
PDF题目解析脚本 - 最终优化版
改进噪声过滤，处理跨栏干扰
"""

import pdfplumber
import json
import re
import os

def get_chapter_list_from_toc(pdf_path):
    """从目录页提取章节列表"""
    chapters = []
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        pattern = r'《(\d+\.[^》]+)》\s*\.+\s*(\d+)'
        for match in re.finditer(pattern, text):
            chapters.append({
                'name': match.group(1).strip(),
                'start_page': int(match.group(2))
            })

    for i in range(len(chapters)):
        chapters[i]['end_page'] = chapters[i+1]['start_page'] if i < len(chapters)-1 else 999

    return chapters


def extract_linear_stream_for_pages(pdf_path, start_page, end_page, margin_top=30, margin_bottom=50):
    """提取指定页面范围的线性文本流"""
    all_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
            page = pdf.pages[page_num]
            width = page.width
            height = page.height

            left_col = page.crop((0, margin_top, width/2, height - margin_bottom))
            right_col = page.crop((width/2, margin_top, width, height - margin_bottom))

            for text in [left_col.extract_text() or "", right_col.extract_text() or ""]:
                for line in text.split('\n'):
                    line = line.strip()
                    if line and not is_noise_line(line):
                        all_lines.append(line)

    return all_lines


def is_noise_line(line):
    """判断是否为干扰行"""
    noise_patterns = [
        r'^得\s*分',          # 得分
        r'^分[：:]?\s*$',     # 分：
        r'^\d+\.?\d*\s*$',    # 纯数字如 0.0
        r'^一、[A-Z]\d?型题', # 题型标注
        r'^二、[A-Z]\d?型题',
        r'^三、[A-Z]\d?型题',
        r'^合计.*分',         # 合计
        r'^《',               # 章节标题开头
        r'^》$',              # 单独的右括号
        r'^系统疾病》',       # 章节标题残留
        r'^统疾病》',         # 章节标题残留
        r'^疾病》',           # 章节标题残留
        r'^\d+\s*[/／]\s*\d+$',  # 页码如 1/111
        r'^\d+\s*$',          # 纯页码
        r'^\.\.\.\.\.\.',     # 省略号
        r'^[－—－-]+$',       # 分隔线
    ]

    for pattern in noise_patterns:
        if re.match(pattern, line):
            return True

    # 检查是否是页码残片 (如 "1 /")
    if re.match(r'^\d+\s*[/／]\s*$', line):
        return True

    return False


def parse_questions_from_lines(all_lines, chapter_name, subject_name):
    """从线性流中解析题目"""
    questions = []
    current_buffer = []
    question_start = re.compile(r'^(\d+)\s*[\.．、]\s*')

    i = 0
    while i < len(all_lines):
        line = all_lines[i]

        # 检测题目开始
        if question_start.match(line):
            # 保存之前的题目
            if current_buffer:
                q = parse_single_question(current_buffer, chapter_name, subject_name)
                if q:
                    questions.append(q)
            current_buffer = [line]
        elif current_buffer:
            current_buffer.append(line)

        i += 1

    # 处理最后一个题目
    if current_buffer:
        q = parse_single_question(current_buffer, chapter_name, subject_name)
        if q:
            questions.append(q)

    return questions


def parse_single_question(lines, chapter_name, subject_name):
    """解析单个题目"""
    if not lines:
        return None

    text = '\n'.join(lines)

    # 提取答案
    answer_match = re.search(r'参考答案[：:]\s*([A-Ea-e])', text)
    if not answer_match:
        return None

    answer = answer_match.group(1).upper()

    # 移除答案行
    text = re.sub(r'参考答案[：:]\s*[A-Ea-e]', '', text)

    # 提取题目编号
    num_match = re.match(r'(\d+)\s*[\.．、]\s*', text)
    if not num_match:
        return None

    text = text[num_match.end():]

    # 找选项开始位置 - 改进匹配
    # 尝试多种选项格式
    option_patterns = [
        r'[A-Ea-e]\s*[\.．、]',  # A. 或 A、
        r'[A-Ea-e]\s+',          # A 后面是空格（没有标点的情况）
    ]

    option_match = None
    for pattern in option_patterns:
        # 在换行后找选项
        option_match = re.search(r'\n\s*' + pattern, text)
        if option_match:
            break
        # 也尝试同行
        option_match = re.search(pattern, text)
        if option_match:
            break

    if not option_match:
        return None

    question_text = text[:option_match.start()].strip()
    options_text = text[option_match.start():]

    # 清理题干
    question_text = re.sub(r'\s+', ' ', question_text).strip()
    if len(question_text) < 5:
        return None

    # 解析选项
    options = {}
    # 改进选项匹配，处理没有标点的情况
    for match in re.finditer(r'([A-Ea-e])\s*[\.．、]?\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]?|\s*参考答案|$)', options_text, re.DOTALL):
        letter = match.group(1).upper()
        content = re.sub(r'\s+', ' ', match.group(2)).strip()
        if content and len(content) > 0:
            options[letter] = content

    if len(options) < 2:
        return None

    return {
        'number': 0,  # 稍后统一编号
        'chapter': chapter_name,
        'subject': subject_name,
        'question': question_text,
        'options': options,
        'answer': answer
    }


def process_pdf(pdf_path, subject_name):
    """处理单个PDF"""
    print(f"\n处理: {subject_name}")

    chapters = get_chapter_list_from_toc(pdf_path)
    print(f"  章节: {len(chapters)} 个")

    result = {}

    for chapter_info in chapters:
        chapter_name = chapter_info['name']
        start_page = chapter_info['start_page']
        end_page = chapter_info['end_page']

        lines = extract_linear_stream_for_pages(pdf_path, start_page, end_page)
        questions = parse_questions_from_lines(lines, chapter_name, subject_name)

        # 去重
        seen = set()
        unique = []
        for q in questions:
            key = q['question'][:30]
            if key not in seen:
                seen.add(key)
                unique.append(q)

        # 编号
        for i, q in enumerate(unique, 1):
            q['number'] = i
            q['id'] = f"{subject_name[:2]}_{chapter_name[:8]}_{i}".replace('.', '_').replace(' ', '_')

        result[chapter_name] = unique
        print(f"  {chapter_name}: {len(unique)} 题")

    return result


def process_all():
    """处理所有PDF"""
    pdf_files = [
        ("/Users/moliex/Downloads/北医内科学题库-706题（分章节重排）.pdf", "内科学", 706),
        ("/Users/moliex/Downloads/北医外科学题库-702题（分章节重排）.pdf", "外科学", 702),
        ("/Users/moliex/Downloads/北医妇产科学题库-750题（分章节重排）.pdf", "妇产科学", 750),
        ("/Users/moliex/Downloads/北医儿科学题库-770题（分章节重排）.pdf", "儿科学", 770),
    ]

    all_data = {}
    total = 0
    expected_total = 0

    for pdf_path, subject_name, expected in pdf_files:
        chapters = process_pdf(pdf_path, subject_name)
        all_data[subject_name] = chapters

        count = sum(len(qs) for qs in chapters.values())
        total += count
        expected_total += expected
        print(f"  小计: {count}/{expected} ({count/expected*100:.1f}%)")

        output_path = f"../data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    with open("../data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total}/{expected_total} ({total/expected_total*100:.1f}%)")


if __name__ == "__main__":
    process_all()
