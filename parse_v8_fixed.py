#!/usr/bin/env python3
"""
PDF题目解析脚本 - 修复版
正确处理章节页码映射
"""

import pdfplumber
import json
import re
import os

def get_chapter_list_from_toc(pdf_path):
    """从目录页提取章节列表，返回实际PDF页码范围"""
    chapters = []
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        pattern = r'《(\d+\.[^》]+)》\s*\.+\s*(\d+)'
        for match in re.finditer(pattern, text):
            # 目录页码是文档页码，PDF页码 = 文档页码 + 1（因为第1页是目录）
            doc_page = int(match.group(2))
            pdf_page = doc_page + 1
            chapters.append({
                'name': match.group(1).strip(),
                'pdf_start': pdf_page,
                'pdf_end': None  # 稍后填充
            })

    # 设置结束页（下一章开始页 - 1）
    for i in range(len(chapters)):
        if i < len(chapters) - 1:
            chapters[i]['pdf_end'] = chapters[i+1]['pdf_start'] - 1
        else:
            chapters[i]['pdf_end'] = 999

    return chapters


def is_noise_line(line):
    """判断干扰行"""
    noise_patterns = [
        r'^得\s*分', r'^分[：:]?\s*$', r'^\d+\.?\d*\s*$',
        r'^一、[A-Z]\d?型题', r'^二、[A-Z]\d?型题', r'^三、[A-Z]\d?型题',
        r'^合计.*分', r'^《', r'^》$',
        r'^\d+\s*[/／]\s*\d+$', r'^\d+\s*$', r'^\.\.\...\.', r'^[－—－-]+$',
    ]
    for p in noise_patterns:
        if re.match(p, line):
            return True
    return False


def extract_linear_stream_for_pages(pdf_path, pdf_start, pdf_end):
    """提取指定PDF页码范围的线性流"""
    all_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        # pdf_start和pdf_end是1-based的页码，需要-1转0-based
        for page_idx in range(pdf_start - 1, min(pdf_end, len(pdf.pages))):
            page = pdf.pages[page_idx]
            width, height = page.width, page.height

            left_col = page.crop((0, 30, width/2, height - 50))
            right_col = page.crop((width/2, 30, width, height - 50))

            for text in [left_col.extract_text() or "", right_col.extract_text() or ""]:
                for line in text.split('\n'):
                    line = line.strip()
                    if line and not is_noise_line(line):
                        all_lines.append(line)

    return all_lines


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
    text = re.sub(r'参考答案[：:]\s*[A-Ea-e]', '', text)

    # 提取题号
    num_match = re.match(r'(\d+)\s*[\.．、]\s*', text)
    if not num_match:
        return None

    text = text[num_match.end():]

    # 找选项开始
    option_match = re.search(r'\n\s*[A-Ea-e]\s*[\.．、]', text)
    if not option_match:
        option_match = re.search(r'[A-Ea-e]\s*[\.．、]', text)
    if not option_match:
        return None

    question_text = text[:option_match.start()].strip()
    options_text = text[option_match.start():]

    question_text = re.sub(r'\s+', ' ', question_text).strip()
    if len(question_text) < 5:
        return None

    # 解析选项
    options = {}
    for m in re.finditer(r'([A-Ea-e])\s*[\.．、]?\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]?|\s*参考答案|$)', options_text, re.DOTALL):
        letter = m.group(1).upper()
        content = re.sub(r'\s+', ' ', m.group(2)).strip()
        if content:
            options[letter] = content

    if len(options) < 2:
        return None

    return {
        'number': 0,
        'chapter': chapter_name,
        'subject': subject_name,
        'question': question_text,
        'options': options,
        'answer': answer
    }


def parse_questions_from_lines(all_lines, chapter_name, subject_name):
    """从线性流解析题目"""
    questions = []
    current_buffer = []
    question_start = re.compile(r'^(\d+)\s*[\.．、]\s*')

    for line in all_lines:
        if question_start.match(line):
            if current_buffer:
                q = parse_single_question(current_buffer, chapter_name, subject_name)
                if q:
                    questions.append(q)
            current_buffer = [line]
        elif current_buffer:
            current_buffer.append(line)

    if current_buffer:
        q = parse_single_question(current_buffer, chapter_name, subject_name)
        if q:
            questions.append(q)

    return questions


def process_pdf(pdf_path, subject_name, expected):
    """处理单个PDF"""
    print(f"\n处理: {subject_name}")

    chapters_info = get_chapter_list_from_toc(pdf_path)
    print(f"  章节: {len(chapters_info)} 个")

    # 先收集所有题目，全局去重
    all_questions = {}  # {(章节名, 题目内容前50字): 题目对象}

    for ch_info in chapters_info:
        ch_name = ch_info['name']
        pdf_start = ch_info['pdf_start']
        pdf_end = ch_info['pdf_end']

        lines = extract_linear_stream_for_pages(pdf_path, pdf_start, pdf_end)
        questions = parse_questions_from_lines(lines, ch_name, subject_name)

        for q in questions:
            key = (q['question'][:50])
            if key not in all_questions:
                all_questions[key] = (ch_name, q)

    # 按章节组织
    result = {ch['name']: [] for ch in chapters_info}
    for key, (ch_name, q) in all_questions.items():
        result[ch_name].append(q)

    # 编号
    for ch_name, questions in result.items():
        for i, q in enumerate(questions, 1):
            q['number'] = i
            q['id'] = f"{subject_name[:2]}_{ch_name[:8]}_{i}".replace('.', '_').replace(' ', '_')
        print(f"  {ch_name}: {len(questions)} 题")

    total = sum(len(qs) for qs in result.values())
    print(f"  小计: {total}/{expected} ({total/expected*100:.1f}%)")

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
    grand_total = 0

    for pdf_path, subject_name, expected in pdf_files:
        chapters = process_pdf(pdf_path, subject_name, expected)
        all_data[subject_name] = chapters
        grand_total += sum(len(qs) for qs in chapters.values())

        with open(f"data/{subject_name}.json", 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    with open("data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {grand_total} 题")


if __name__ == "__main__":
    process_all()
