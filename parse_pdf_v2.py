#!/usr/bin/env python3
"""
PDF题目解析脚本 v2
改进版：处理双栏排版的PDF
"""

import pdfplumber
import json
import re
import os

def extract_questions_from_pdf(pdf_path, subject_name):
    """从PDF提取题目"""
    questions = []
    current_chapter = "未知章节"

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # 尝试分栏提取
            text = page.extract_text()
            if not text:
                continue

            # 检测章节标题
            chapter_match = re.search(r'《(\d+\.[^》]+)》', text)
            if chapter_match:
                current_chapter = chapter_match.group(1).strip()

            # 提取本页的题目
            page_questions = extract_questions_from_text(
                text, subject_name, current_chapter, page_num
            )
            questions.extend(page_questions)

    return questions

def extract_questions_from_text(text, subject_name, chapter, page_num):
    """从文本中提取题目"""
    questions = []

    # 更灵活的题目匹配模式
    # 匹配：编号. 或 编号、或 编号． 后面跟着题干
    # 然后是A-E选项
    # 最后是参考答案

    # 方法：先找到所有"参考答案"位置，然后回溯找题目
    answer_pattern = r'参考答案[：:]\s*([A-Ea-e])'

    # 分割文本为段落
    # 用参考答案作为分割点
    parts = re.split(r'(参考答案[：:]\s*[A-Ea-e])', text)

    current_question_text = ""

    for i, part in enumerate(parts):
        # 检查是否是答案部分
        answer_match = re.match(r'参考答案[：:]\s*([A-Ea-e])', part)
        if answer_match:
            answer = answer_match.group(1).upper()
            # 在前面的文本中找题目
            if i > 0:
                question_block = parts[i-1] if i > 0 else ""
                question = parse_question_block(question_block, answer, subject_name, chapter)
                if question:
                    questions.append(question)
        else:
            current_question_text = part

    return questions

def parse_question_block(text, answer, subject_name, chapter):
    """解析题目块"""
    # 移除一些干扰文本
    text = re.sub(r'得分[：:]?\s*\d*\.?\d*', '', text)
    text = re.sub(r'分[：:]\s*\d*\.?\d*', '', text)
    text = re.sub(r'一、[A-Z]\d?型题.*?分。?\)', '', text)
    text = re.sub(r'二、[A-Z]\d?型题.*?分。?\)', '', text)

    # 找题目编号和题干
    # 从后往前找最后一个题目编号
    question_pattern = r'(\d+)\s*[\.．、]\s*([^A-Ea-e]+?)(?=[A-Ea-e][\.．、])'

    matches = list(re.finditer(question_pattern, text, re.DOTALL))

    if not matches:
        return None

    # 取最后一个匹配（最近的题目）
    match = matches[-1]
    q_num = match.group(1)
    question_text = match.group(2).strip()

    # 提取选项
    options_start = match.end()
    options_text = text[options_start:]
    options = parse_options(options_text)

    if not options or len(options) < 4:
        # 尝试从整个文本提取选项
        options = parse_options(text)

    if not options or len(options) < 2:
        return None

    # 清理题干
    question_text = clean_text(question_text)
    if len(question_text) < 5:
        return None

    return {
        "id": f"{subject_name[:2]}_{chapter[:10]}_{q_num}",
        "number": int(q_num),
        "subject": subject_name,
        "chapter": chapter,
        "question": question_text,
        "options": options,
        "answer": answer
    }

def parse_options(text):
    """解析选项"""
    options = {}

    # 更灵活的选项匹配
    # A．xxx 或 A.xxx 或 A、xxx 或 A xxx
    option_pattern = r'([A-Ea-e])\s*[\.．、]\s*([^A-Ea-e\.．、]+?)(?=\s*[A-Ea-e]\s*[\.．、]|$|参考答案)'

    matches = re.findall(option_pattern, text, re.DOTALL)

    for letter, opt_text in matches:
        clean_opt = clean_text(opt_text)
        if clean_opt and len(clean_opt) > 0:
            options[letter.upper()] = clean_opt

    return options

def clean_text(text):
    """清理文本"""
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    # 移除页码
    text = re.sub(r'\d+\s*/\s*\d+', '', text)
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？、；：""''（）【】《》\.\,\?\!\;\:\"\'\(\)\[\]\-\/\\％%~～+-]', '', text)
    return text.strip()

def process_all_pdfs():
    """处理所有PDF"""
    pdf_files = [
        ("/Users/moliex/Downloads/北医内科学题库-706题（分章节重排）.pdf", "内科学"),
        ("/Users/moliex/Downloads/北医外科学题库-702题（分章节重排）.pdf", "外科学"),
        ("/Users/moliex/Downloads/北医妇产科学题库-750题（分章节重排）.pdf", "妇产科学"),
        ("/Users/moliex/Downloads/北医儿科学题库-770题（分章节重排）.pdf", "儿科学"),
    ]

    all_questions = {}
    total = 0

    for pdf_path, subject_name in pdf_files:
        print(f"处理: {subject_name}...")
        questions = extract_questions_from_pdf(pdf_path, subject_name)

        # 按章节组织
        subject_data = {}
        for q in questions:
            chapter = q['chapter']
            if chapter not in subject_data:
                subject_data[chapter] = []
            subject_data[chapter].append(q)

        all_questions[subject_name] = subject_data
        count = len(questions)
        total += count
        print(f"  提取: {count} 道")

        # 去重
        seen_ids = set()
        unique_questions = []
        for chapter, qs in subject_data.items():
            for q in qs:
                if q['id'] not in seen_ids:
                    seen_ids.add(q['id'])
                    unique_questions.append(q)
            subject_data[chapter] = [q for q in qs if q['id'] in seen_ids]

        # 保存
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

    # 汇总
    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print(f"\n总计: {total} 道")
    return all_questions

if __name__ == "__main__":
    process_all_pdfs()
