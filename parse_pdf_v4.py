#!/usr/bin/env python3
"""
PDF题目解析脚本 v4 - 最终版
使用更稳健的解析策略
"""

import pdfplumber
import json
import re
import os

def extract_all_text_by_columns(pdf_path):
    """分栏提取PDF所有文本"""
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            width = page.width
            height = page.height

            left_col = page.crop((0, 0, width/2, height))
            right_col = page.crop((width/2, 0, width, height))

            left_text = left_col.extract_text() or ""
            right_text = right_col.extract_text() or ""

            all_text.append({
                'left': left_text,
                'right': right_text
            })

    return all_text

def parse_questions(pdf_path, subject_name):
    """解析PDF中的所有题目"""
    pages = extract_all_text_by_columns(pdf_path)

    questions = []
    current_chapter = "未知章节"
    question_counter = 0

    for page_data in pages:
        # 检查是否有章节标题
        for col_text in [page_data['left'], page_data['right']]:
            # 匹配章节标题 《X.XXXXX》
            chapter_match = re.search(r'《(\d+\.[^》]+)》', col_text)
            if chapter_match:
                current_chapter = chapter_match.group(1).strip()

        # 从两栏提取题目
        for col_text in [page_data['left'], page_data['right']]:
            page_questions = extract_questions_from_column(
                col_text, subject_name, current_chapter, question_counter
            )
            if page_questions:
                questions.extend(page_questions)
                question_counter = max(q['number'] for q in page_questions)

    return questions

def extract_questions_from_column(text, subject_name, chapter, start_num):
    """从单栏文本中提取题目"""
    questions = []

    # 清理干扰文本
    text = re.sub(r'得\s*分[：:]?\s*\d*\.?\d*', '', text)
    text = re.sub(r'一、[A-Z]\d?型题\s*\(合计.*?\)', '', text)
    text = re.sub(r'二、[A-Z]\d?型题\s*\(合计.*?\)', '', text)
    text = re.sub(r'\d+\s*/\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # 找所有 "参考答案：X"
    answer_positions = []
    for match in re.finditer(r'参考答案[：:]\s*([A-Ea-e])', text):
        answer_positions.append((match.start(), match.group(1).upper()))

    if not answer_positions:
        return questions

    # 根据答案位置，向前回溯找题目
    for i, (ans_pos, answer) in enumerate(answer_positions):
        # 确定这个答案对应的题目范围
        prev_ans_pos = answer_positions[i-1][0] + 20 if i > 0 else 0
        question_area = text[prev_ans_pos:ans_pos]

        # 在这个区域找题目编号
        num_match = None
        for m in re.finditer(r'(\d+)\s*[\.．、]\s*', question_area):
            num_match = m

        if not num_match:
            continue

        q_num = int(num_match.group(1))
        question_start = num_match.end()

        # 从题目开始到选项前是题干
        # 找选项开始的位置
        option_start = re.search(r'\s[A-Ea-e][\.．、]', question_area[question_start:])
        if not option_start:
            continue

        option_start_pos = question_start + option_start.start()
        question_text = question_area[question_start:option_start_pos].strip()
        options_text = question_area[option_start_pos:]

        # 解析选项
        options = parse_options(options_text)

        if len(options) < 2 or len(question_text) < 5:
            continue

        # 清理题干
        question_text = clean_question_text(question_text)

        questions.append({
            "id": f"{subject_name}_{chapter[:10].replace('.', '_')}_{q_num}",
            "number": q_num,
            "subject": subject_name,
            "chapter": chapter,
            "question": question_text,
            "options": options,
            "answer": answer
        })

    return questions

def parse_options(text):
    """解析选项"""
    options = {}

    # 匹配选项，支持多种格式
    pattern = r'([A-Ea-e])\s*[\.．、]\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]|$)'

    for match in re.finditer(pattern, text, re.DOTALL):
        letter = match.group(1).upper()
        content = match.group(2).strip()
        content = re.sub(r'\s+', ' ', content)
        if content:
            options[letter] = content

    return options

def clean_question_text(text):
    """清理题目文本"""
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    # 移除页码等
    text = re.sub(r'\d+\s*/\s*\d+', '', text)
    return text.strip()

def process_all_pdfs():
    """处理所有PDF文件"""
    pdf_files = [
        ("/Users/moliex/Downloads/北医内科学题库-706题（分章节重排）.pdf", "内科学"),
        ("/Users/moliex/Downloads/北医外科学题库-702题（分章节重排）.pdf", "外科学"),
        ("/Users/moliex/Downloads/北医妇产科学题库-750题（分章节重排）.pdf", "妇产科学"),
        ("/Users/moliex/Downloads/北医儿科学题库-770题（分章节重排）.pdf", "儿科学"),
    ]

    all_data = {}
    total = 0

    for pdf_path, subject_name in pdf_files:
        print(f"\n处理: {subject_name}")
        questions = parse_questions(pdf_path, subject_name)

        # 去重
        seen = set()
        unique_questions = []
        for q in questions:
            key = (q['chapter'], q['question'][:30])
            if key not in seen:
                seen.add(key)
                unique_questions.append(q)

        # 按章节组织
        subject_data = {}
        for q in unique_questions:
            chapter = q['chapter']
            if chapter not in subject_data:
                subject_data[chapter] = []
            subject_data[chapter].append(q)

        # 给题目编号
        for chapter, qs in subject_data.items():
            for i, q in enumerate(qs, 1):
                q['number'] = i
                q['id'] = f"{subject_name}_{chapter[:10].replace('.', '_')}_{i}"

        all_data[subject_name] = subject_data
        count = sum(len(qs) for qs in subject_data.values())
        total += count
        print(f"  提取: {count} 道题目")

        for chapter, qs in sorted(subject_data.items()):
            print(f"    {chapter}: {len(qs)} 道")

        # 保存
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

    # 汇总
    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total} 道题目")
    print(f"保存至: /Users/moliex/projects/medical-quiz/data/")

    return all_data

if __name__ == "__main__":
    process_all_pdfs()
