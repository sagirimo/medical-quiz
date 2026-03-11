#!/usr/bin/env python3
"""
PDF题目解析脚本 - 最优版
整体处理+章节检测，避免边界问题
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
                'start_page': int(match.group(2)) + 1  # PDF页码
            })
    return chapters


def extract_all_text_linear(pdf_path, start_page=2):
    """提取所有文本为线性流（从指定页开始，跳过目录）"""
    all_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, len(pdf.pages)):
            page = pdf.pages[page_num]
            width, height = page.width, page.height

            left_col = page.crop((0, 30, width/2, height - 50))
            right_col = page.crop((width/2, 30, width, height - 50))

            for text in [left_col.extract_text() or "", right_col.extract_text() or ""]:
                for line in text.split('\n'):
                    line = line.strip()
                    if line and not is_noise_line(line):
                        all_lines.append(line)

    return all_lines


def is_noise_line(line):
    noise_patterns = [
        r'^得\s*分', r'^分[：:]?\s*$', r'^\d+\.?\d*\s*$',
        r'^一、[A-Z]\d?型题', r'^二、[A-Z]\d?型题', r'^合计.*分',
        r'^\d+\s*[/／]\s*\d+$', r'^\d+\s*$', r'^\.\.\...\.', r'^[－—－-]+$',
    ]
    for p in noise_patterns:
        if re.match(p, line):
            return True
    return False


def detect_chapter(line, chapter_names):
    """检测行是否包含章节标题"""
    for ch_name in chapter_names:
        # 章节标题可能被切断，检测部分匹配
        if f'《{ch_name}' in line or f'{ch_name}》' in line:
            return ch_name
        # 完整标题
        if f'《{ch_name}》' in line:
            return ch_name
    return None


def parse_questions_with_chapters(all_lines, chapter_names, subject_name):
    """解析题目并同时检测章节"""
    chapters = {name: [] for name in chapter_names}
    current_chapter = chapter_names[0] if chapter_names else "未知章节"

    current_buffer = []
    question_start = re.compile(r'^(\d+)\s*[\.．、]\s*')
    chapter_pattern = re.compile(r'《(\d+\.[^》]+)》')

    for line in all_lines:
        # 检测章节切换
        ch_match = chapter_pattern.search(line)
        if ch_match:
            detected_ch = ch_match.group(1).strip()
            if detected_ch in chapter_names:
                # 保存之前的题目
                if current_buffer:
                    q = parse_single_question(current_buffer, current_chapter, subject_name)
                    if q:
                        chapters[current_chapter].append(q)
                    current_buffer = []
                current_chapter = detected_ch
                continue

        # 检测题目开始
        if question_start.match(line):
            if current_buffer:
                q = parse_single_question(current_buffer, current_chapter, subject_name)
                if q:
                    chapters[current_chapter].append(q)
            current_buffer = [line]
        elif current_buffer:
            current_buffer.append(line)

    # 处理最后一个题目
    if current_buffer:
        q = parse_single_question(current_buffer, current_chapter, subject_name)
        if q:
            chapters[current_chapter].append(q)

    return chapters


def parse_single_question(lines, chapter_name, subject_name):
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


def process_pdf(pdf_path, subject_name, expected):
    print(f"\n处理: {subject_name}")

    chapters_info = get_chapter_list_from_toc(pdf_path)
    chapter_names = [ch['name'] for ch in chapters_info]
    print(f"  章节: {len(chapter_names)} 个")

    all_lines = extract_all_text_linear(pdf_path)
    print(f"  总行数: {len(all_lines)}")

    chapters = parse_questions_with_chapters(all_lines, chapter_names, subject_name)

    # 全局去重
    seen_global = set()
    for ch_name in chapter_names:
        unique = []
        for q in chapters[ch_name]:
            key = q['question'][:50]
            if key not in seen_global:
                seen_global.add(key)
                unique.append(q)

        for i, q in enumerate(unique, 1):
            q['number'] = i
            q['id'] = f"{subject_name[:2]}_{ch_name[:8]}_{i}".replace('.', '_').replace(' ', '_')

        chapters[ch_name] = unique
        print(f"  {ch_name}: {len(unique)} 题")

    total = sum(len(qs) for qs in chapters.values())
    print(f"  小计: {total}/{expected} ({total/expected*100:.1f}%)")

    return chapters


def process_all():
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

        with open(f"../data/{subject_name}.json", 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    with open("../data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {grand_total} 题")


if __name__ == "__main__":
    process_all()
