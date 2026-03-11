#!/usr/bin/env python3
"""
PDF题目解析脚本 v3
使用分栏提取，更准确地解析题目
"""

import pdfplumber
import json
import re
import os

def extract_page_text_by_columns(page):
    """分栏提取页面文本"""
    width = page.width
    height = page.height

    # 左右分栏提取
    left_col = page.crop((0, 0, width/2, height))
    right_col = page.crop((width/2, 0, width, height))

    left_text = left_col.extract_text() or ""
    right_text = right_col.extract_text() or ""

    return left_text, right_text

def extract_all_text(pdf_path):
    """提取PDF所有文本（分栏后合并）"""
    all_pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            left_text, right_text = extract_page_text_by_columns(page)
            all_pages.append({
                'page_num': page_num,
                'left': left_text,
                'right': right_text,
                'full': left_text + "\n" + right_text
            })

    return all_pages

def find_chapters(pages_text):
    """找到所有章节标题的位置"""
    chapters = []
    chapter_pattern = re.compile(r'《(\d+\.[^》]+)》')

    for page_data in pages_text:
        full_text = page_data['full']
        for match in chapter_pattern.finditer(full_text):
            chapters.append({
                'name': match.group(1).strip(),
                'page': page_data['page_num']
            })

    return chapters

def parse_questions_from_pages(pages_text, subject_name):
    """从页面中解析题目"""
    questions = []
    current_chapter = "未知章节"

    # 合并所有文本，但保留分页信息
    full_text_parts = []
    for page_data in pages_text:
        # 使用完整页面文本
        full_text_parts.append(page_data['full'])

    full_text = "\n\n---PAGE_BREAK---\n\n".join(full_text_parts)

    # 按章节分割
    chapter_pattern = r'《(\d+\.[^》]+)》'
    parts = re.split(chapter_pattern, full_text)

    # parts[0] 是目录等，跳过
    # 之后交替：章节名、章节内容

    for i in range(1, len(parts), 2):
        if i < len(parts):
            current_chapter = parts[i].strip()
        if i + 1 < len(parts):
            chapter_text = parts[i + 1]
            # 移除页码等干扰
            chapter_text = re.sub(r'\d+\s*/\s*\d+', '', chapter_text)
            chapter_text = re.sub(r'得\s*分[：:]?\s*\d*\.?\d*', '', chapter_text)
            chapter_text = re.sub(r'分[：:]', '', chapter_text)
            chapter_text = re.sub(r'一、[A-Z]\d?型题\s*\(合计\d+\.?\d*分。?\)', '', chapter_text)
            chapter_text = re.sub(r'二、[A-Z]\d?型题\s*\(合计\d+\.?\d*分。?\)', '', chapter_text)
            chapter_text = re.sub(r'---PAGE_BREAK---', '', chapter_text)

            chapter_questions = parse_chapter_questions(chapter_text, current_chapter, subject_name)
            questions.extend(chapter_questions)

    return questions

def parse_chapter_questions(text, chapter, subject_name):
    """解析章节内的所有题目"""
    questions = []

    # 找到所有题目块
    # 题目块格式：编号. 题干 选项 参考答案

    # 先按"参考答案"分割
    parts = text.split('参考答案')

    for i, part in enumerate(parts[:-1]):  # 最后一个没有答案
        # 找答案
        answer_match = re.match(r'[：:]\s*([A-Ea-e])', parts[i+1] if i+1 < len(parts) else "")
        if not answer_match:
            continue
        answer = answer_match.group(1).upper()

        # 在part中找题目
        question = extract_single_question(part, answer, chapter, subject_name)
        if question:
            questions.append(question)

    return questions

def extract_single_question(text, answer, chapter, subject_name):
    """从文本块中提取单个题目"""
    # 找最后一个题目编号（因为一个块可能包含多个题目的残余）
    # 匹配：数字. 或 数字、或 数字． 后面跟着非选项内容

    # 移除一些干扰
    text = text.strip()

    # 找所有题目编号的位置
    question_starts = list(re.finditer(r'(\d+)\s*[\.．、]\s*(?=[^\d])', text))

    if not question_starts:
        return None

    # 取最后一个题目（当前题目）
    last_match = question_starts[-1]
    q_num = last_match.group(1)
    start_pos = last_match.start()

    # 从这个位置开始到结尾就是当前题目
    question_block = text[start_pos:]

    # 分离题干和选项
    # 找选项开始的位置
    option_pattern = r'\n\s*([A-Ea-e])\s*[\.．、]'
    option_matches = list(re.finditer(option_pattern, question_block))

    if not option_matches:
        return None

    # 第一个选项之前是题干
    first_option_pos = option_matches[0].start()
    question_text = question_block[:first_option_pos]
    options_text = question_block[first_option_pos:]

    # 提取题干（去掉编号）
    question_text = re.sub(r'^\d+\s*[\.．、]\s*', '', question_text)
    question_text = clean_text(question_text)

    if len(question_text) < 5:
        return None

    # 提取选项
    options = extract_options(options_text)

    if len(options) < 2:
        return None

    return {
        "id": f"{subject_name}_{chapter}_{q_num}",
        "number": int(q_num),
        "subject": subject_name,
        "chapter": chapter,
        "question": question_text,
        "options": options,
        "answer": answer
    }

def extract_options(text):
    """提取选项"""
    options = {}

    # 匹配选项
    pattern = r'([A-Ea-e])\s*[\.．、]\s*([^A-Ea-e\.．、]+?)(?=\s*[A-Ea-e]\s*[\.．、]|$)'

    matches = re.findall(pattern, text, re.DOTALL)

    for letter, content in matches:
        clean_content = clean_text(content)
        if clean_content:
            options[letter.upper()] = clean_content

    return options

def clean_text(text):
    """清理文本"""
    # 移除多余空白和换行
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def process_all_pdfs():
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

        pages_text = extract_all_text(pdf_path)
        questions = parse_questions_from_pages(pages_text, subject_name)

        # 去重（按题目内容）
        seen = set()
        unique_questions = []
        for q in questions:
            key = (q['chapter'], q['question'][:50])
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

        all_data[subject_name] = subject_data
        count = sum(len(qs) for qs in subject_data.values())
        total += count
        print(f"  共提取: {count} 道题目")

        for chapter, qs in subject_data.items():
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
    print(f"总计提取: {total} 道题目")
    print(f"数据保存至: /Users/moliex/projects/medical-quiz/data/")

    return all_data

if __name__ == "__main__":
    process_all_pdfs()
