#!/usr/bin/env python3
"""
PDF题目解析脚本 v5
策略：逐页处理，每页分栏提取后根据题目位置智能组织
"""

import pdfplumber
import json
import re
import os

def extract_page_content(page):
    """提取页面内容，返回分栏文本和各元素位置"""
    width = page.width
    height = page.height

    # 左右分栏
    left_col = page.crop((0, 0, width/2, height))
    right_col = page.crop((width/2, 0, width, height))

    left_text = left_col.extract_text() or ""
    right_text = right_col.extract_text() or ""

    return left_text, right_text

def get_chapter_title(text):
    """从文本中提取章节标题"""
    match = re.search(r'《(\d+\.[^》]+)》', text)
    if match:
        return match.group(1).strip()
    return None

def preprocess_text(text):
    """预处理文本，移除干扰元素"""
    text = re.sub(r'得\s*分\s*[：:]?\s*\d*\.?\d*', '', text)
    text = re.sub(r'一、[A-Z]\d?型题\s*\(合计.*?\)', '', text)
    text = re.sub(r'二、[A-Z]\d?型题\s*\(合计.*?\)', '', text)
    text = re.sub(r'\d+\s*/\s*\d+', '', text)
    text = re.sub(r'《\d+\.[^》]+》', '', text)  # 移除章节标题
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def find_all_questions(text):
    """找到文本中所有题目"""
    questions = []

    # 预处理
    text = preprocess_text(text)

    # 使用统一的题目块模式
    # 一个题目块 = 题目编号 + 题干 + 选项 + 参考答案

    # 方法：找到所有"参考答案"作为锚点，然后回溯
    pattern = r'(\d+)\s*[\.．、]\s*(.+?)((?:[A-Ea-e]\s*[\.．、].+?\n?)+)\s*参考答案[：:]\s*([A-Ea-e])'

    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        q_num, question_text, options_text, answer = match

        # 清理题干
        question_text = re.sub(r'\s+', ' ', question_text).strip()
        if len(question_text) < 5:
            continue

        # 解析选项
        options = {}
        opt_pattern = r'([A-Ea-e])\s*[\.．、]\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]|$)'
        for opt_match in re.finditer(opt_pattern, options_text, re.DOTALL):
            letter = opt_match.group(1).upper()
            content = re.sub(r'\s+', ' ', opt_match.group(2)).strip()
            if content:
                options[letter] = content

        if len(options) < 2:
            continue

        questions.append({
            'number': int(q_num),
            'question': question_text,
            'options': options,
            'answer': answer.upper()
        })

    return questions

def process_pdf(pdf_path, subject_name):
    """处理单个PDF"""
    all_questions = []
    current_chapter = "未知章节"
    chapter_questions = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            left_text, right_text = extract_page_content(page)

            # 检查章节标题（可能在左栏或右栏）
            left_chapter = get_chapter_title(left_text)
            right_chapter = get_chapter_title(right_text)

            new_chapter = left_chapter or right_chapter
            if new_chapter:
                # 保存之前的章节
                if current_chapter != "未知章节" and current_chapter not in chapter_questions:
                    chapter_questions[current_chapter] = []
                current_chapter = new_chapter

            if current_chapter not in chapter_questions:
                chapter_questions[current_chapter] = []

            # 从两栏提取题目
            for col_text in [left_text, right_text]:
                questions = find_all_questions(col_text)
                for q in questions:
                    q['chapter'] = current_chapter
                    q['subject'] = subject_name
                chapter_questions[current_chapter].extend(questions)

    # 保存最后章节
    if current_chapter != "未知章节" and current_chapter not in chapter_questions:
        chapter_questions[current_chapter] = []

    # 去重和编号
    final_chapters = {}
    for chapter, questions in chapter_questions.items():
        seen = set()
        unique = []
        for q in questions:
            key = q['question'][:30]
            if key not in seen:
                seen.add(key)
                unique.append(q)

        # 重新编号
        for i, q in enumerate(unique, 1):
            q['number'] = i
            q['id'] = f"{subject_name}_{chapter[:15]}_{i}".replace(' ', '_').replace('.', '_')

        if unique:
            final_chapters[chapter] = unique

    return final_chapters

def process_all():
    """处理所有PDF"""
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
        chapters = process_pdf(pdf_path, subject_name)
        all_data[subject_name] = chapters

        subject_total = sum(len(qs) for qs in chapters.values())
        total += subject_total
        print(f"  共: {subject_total} 道")

        for chapter, qs in sorted(chapters.items()):
            print(f"    {chapter}: {len(qs)} 道")

        # 保存
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    # 汇总
    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total} 道题目")

    return all_data

if __name__ == "__main__":
    process_all()
