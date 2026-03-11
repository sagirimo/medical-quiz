#!/usr/bin/env python3
"""
PDF题目解析脚本 - 修复章节映射
"""

import pdfplumber
import json
import re
import os

def get_chapter_list_from_toc(pdf_path):
    """从目录页提取章节列表，页码+1（因为第1页是目录）"""
    chapters = []
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        pattern = r'《(\d+\.[^》]+)》\s*\.+\s*(\d+)'
        for match in re.finditer(pattern, text):
            # 页码+1，因为目录页是第1页
            pdf_page = int(match.group(2)) + 1
            chapters.append({
                'name': match.group(1).strip(),
                'start_page': pdf_page
            })

    for i in range(len(chapters)):
        chapters[i]['end_page'] = chapters[i+1]['start_page'] if i < len(chapters)-1 else 999

    return chapters


def is_noise_line(line):
    """判断是否为干扰行"""
    noise_patterns = [
        r'^得\s*分',
        r'^分[：:]?\s*$',
        r'^\d+\.?\d*\s*$',
        r'^一、[A-Z]\d?型题',
        r'^二、[A-Z]\d?型题',
        r'^三、[A-Z]\d?型题',
        r'^合计.*分',
        r'^《',
        r'^》$',
        r'^系统疾病》',
        r'^统疾病》',
        r'^疾病》',
        r'^\d+\s*[/／]\s*\d+$',
        r'^\d+\s*$',
        r'^\.\.\.\.\.\.',
        r'^[－—－-]+$',
    ]
    for pattern in noise_patterns:
        if re.match(pattern, line):
            return True
    if re.match(r'^\d+\s*[/／]\s*$', line):
        return True
    return False


def extract_linear_stream_for_pages(pdf_path, start_page, end_page):
    """提取指定页面范围的线性文本流"""
    all_lines = []
    margin_top, margin_bottom = 30, 50

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


def parse_single_question(lines, chapter_name, subject_name):
    """解析单个题目"""
    if not lines:
        return None

    text = '\n'.join(lines)

    answer_match = re.search(r'参考答案[：:]\s*([A-Ea-e])', text)
    if not answer_match:
        return None

    answer = answer_match.group(1).upper()
    text = re.sub(r'参考答案[：:]\s*[A-Ea-e]', '', text)

    num_match = re.match(r'(\d+)\s*[\.．、]\s*', text)
    if not num_match:
        return None

    text = text[num_match.end():]

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

    options = {}
    for match in re.finditer(r'([A-Ea-e])\s*[\.．、]?\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]?|\s*参考答案|$)', options_text, re.DOTALL):
        letter = match.group(1).upper()
        content = re.sub(r'\s+', ' ', match.group(2)).strip()
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
    """从线性流中解析题目"""
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


def process_pdf(pdf_path, subject_name):
    """处理单个PDF"""
    print(f"\n处理: {subject_name}")

    chapters = get_chapter_list_from_toc(pdf_path)
    print(f"  章节: {len(chapters)} 个")
    for ch in chapters:
        print(f"    {ch['name']}: PDF第{ch['start_page']}页-第{ch['end_page']}页")

    result = {}

    for chapter_info in chapters:
        chapter_name = chapter_info['name']
        start_page = chapter_info['start_page']
        end_page = chapter_info['end_page']

        lines = extract_linear_stream_for_pages(pdf_path, start_page, end_page)
        questions = parse_questions_from_lines(lines, chapter_name, subject_name)

        # 去重（按题目内容前50字）
        seen = set()
        unique = []
        for q in questions:
            key = q['question'][:50]
            if key not in seen:
                seen.add(key)
                unique.append(q)

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

    for pdf_path, subject_name, expected in pdf_files:
        chapters = process_pdf(pdf_path, subject_name)
        all_data[subject_name] = chapters

        count = sum(len(qs) for qs in chapters.values())
        total += count
        print(f"  小计: {count}/{expected} ({count/expected*100:.1f}%)")

        output_path = f"../data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    with open("../data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total} 题")


if __name__ == "__main__":
    process_all()
