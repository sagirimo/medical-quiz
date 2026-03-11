#!/usr/bin/env python3
"""
PDF题目解析脚本 - 最终完整版
使用目录页确定章节边界，逐页解析题目
"""

import pdfplumber
import json
import re
import os

def get_chapter_list(pdf_path):
    """从目录页提取章节列表和起始页"""
    chapters = []

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""

        # 匹配章节和页码
        pattern = r'《(\d+\.[^》]+)》\s*\.+\s*(\d+)'
        for match in re.finditer(pattern, text):
            chapter_name = match.group(1).strip()
            start_page = int(match.group(2))
            chapters.append({
                'name': chapter_name,
                'start_page': start_page
            })

    # 添加结束页
    for i in range(len(chapters)):
        if i < len(chapters) - 1:
            chapters[i]['end_page'] = chapters[i+1]['start_page']
        else:
            chapters[i]['end_page'] = 999  # 最后一章

    return chapters

def extract_page_text(page):
    """分栏提取页面文本"""
    width = page.width
    height = page.height

    left_col = page.crop((0, 0, width/2, height))
    right_col = page.crop((width/2, 0, width, height))

    left_text = left_col.extract_text() or ""
    right_text = right_col.extract_text() or ""

    return left_text, right_text

def parse_questions_from_column(text, chapter_name, subject_name, q_offset):
    """从单栏文本中解析题目"""
    questions = []

    # 预处理 - 移除干扰文本
    text = re.sub(r'《\d+\.[^》]+》', '', text)
    text = re.sub(r'得\s*分\s*[：:]?\s*\d*\.?\d*', '', text)
    text = re.sub(r'[一二三四五六七八九十]+、[A-Z]\d?型题.*?分[。）]', '', text)
    text = re.sub(r'\d+\s*/\s*\d+', '', text)

    # 找所有"参考答案：X"作为锚点
    answer_pattern = r'参考答案[：:]\s*([A-Ea-e])'

    # 按参考答案分割文本
    parts = re.split(r'(参考答案[：:]\s*[A-Ea-e])', text)

    current_question_text = ""

    for i, part in enumerate(parts):
        if re.match(r'参考答案[：:]\s*[A-Ea-e]', part):
            # 提取答案
            answer = part[-1].upper()

            # 前一部分包含题目
            if i > 0:
                q_text = parts[i-1] if i > 0 else ""
                question = extract_single_question(q_text, answer, chapter_name, subject_name, q_offset)
                if question:
                    questions.append(question)
                    q_offset += 1

    return questions, q_offset

def extract_single_question(text, answer, chapter_name, subject_name, q_offset):
    """从文本块中提取单个题目"""
    # 找最后一个题目编号
    matches = list(re.finditer(r'(\d+)\s*[\.．、]\s*(?=[^\d\s])', text))

    if not matches:
        return None

    # 取最后一个（最近的）题目编号
    last_match = matches[-1]
    q_num = int(last_match.group(1))

    # 从题目编号后开始
    q_start = last_match.end()

    # 找选项开始位置
    option_match = re.search(r'\s([A-Ea-e])\s*[\.．、]', text[q_start:])
    if not option_match:
        return None

    option_start = q_start + option_match.start()

    # 分离题干和选项
    question_text = text[q_start:option_start].strip()
    options_text = text[option_start:]

    # 清理题干
    question_text = re.sub(r'\s+', ' ', question_text).strip()
    if len(question_text) < 5:
        return None

    # 解析选项
    options = {}
    for opt_match in re.finditer(r'([A-Ea-e])\s*[\.．、]\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]|$)', options_text, re.DOTALL):
        letter = opt_match.group(1).upper()
        content = re.sub(r'\s+', ' ', opt_match.group(2)).strip()
        if content:
            options[letter] = content

    if len(options) < 2:
        return None

    return {
        'id': f"{subject_name[:2]}_{chapter_name[:6]}_{q_offset}".replace('.', '_'),
        'number': q_offset,
        'chapter': chapter_name,
        'subject': subject_name,
        'question': question_text,
        'options': options,
        'answer': answer
    }

def process_pdf(pdf_path, subject_name):
    """处理单个PDF文件"""
    print(f"\n处理: {subject_name}")

    # 获取章节列表
    chapters = get_chapter_list(pdf_path)
    print(f"  章节: {len(chapters)} 个")
    for ch in chapters:
        print(f"    - {ch['name']} (第{ch['start_page']}页起)")

    all_questions = {}

    with pdfplumber.open(pdf_path) as pdf:
        for chapter_info in chapters:
            chapter_name = chapter_info['name']
            start_page = chapter_info['start_page']
            end_page = chapter_info['end_page']

            chapter_questions = []
            q_offset = 1

            # 遍历该章节的页面（PDF页码从0开始，但文档页码从1开始）
            for page_num in range(start_page, min(end_page + 1, len(pdf.pages))):
                page = pdf.pages[page_num - 1]  # 转换为0-based索引
                left_text, right_text = extract_page_text(page)

                for col_text in [left_text, right_text]:
                    questions, q_offset = parse_questions_from_column(
                        col_text, chapter_name, subject_name, q_offset
                    )
                    chapter_questions.extend(questions)

            # 去重
            seen = set()
            unique = []
            for q in chapter_questions:
                key = q['question'][:30]
                if key not in seen:
                    seen.add(key)
                    unique.append(q)

            # 更新编号
            for i, q in enumerate(unique, 1):
                q['number'] = i
                q['id'] = f"{subject_name[:2]}_{chapter_name[:8]}_{i}".replace('.', '_').replace(' ', '_')

            all_questions[chapter_name] = unique
            print(f"  {chapter_name}: {len(unique)} 题")

    return all_questions

def process_all_pdfs():
    """处理所有PDF文件"""
    pdf_files = [
        ("/Users/moliex/Downloads/北医内科学题库-706题（分章节重排）.pdf", "内科学", 706),
        ("/Users/moliex/Downloads/北医外科学题库-702题（分章节重排）.pdf", "外科学", 702),
        ("/Users/moliex/Downloads/北医妇产科学题库-750题（分章节重排）.pdf", "妇产科学", 750),
        ("/Users/moliex/Downloads/北医儿科学题库-770题（分章节重排）.pdf", "儿科学", 770),
    ]

    all_data = {}
    total = 0
    total_expected = 0

    for pdf_path, subject_name, expected in pdf_files:
        chapters = process_pdf(pdf_path, subject_name)
        all_data[subject_name] = chapters

        count = sum(len(qs) for qs in chapters.values())
        total += count
        total_expected += expected
        coverage = count / expected * 100
        print(f"  小计: {count}/{expected} ({coverage:.1f}%)")

        # 保存单独文件
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    # 保存汇总
    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total}/{total_expected} ({total/total_expected*100:.1f}%)")
    print(f"保存至: /Users/moliex/projects/medical-quiz/data/")

    return all_data

if __name__ == "__main__":
    process_all_pdfs()
