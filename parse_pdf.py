#!/usr/bin/env python3
"""
PDF题目解析脚本
从北医题库PDF中提取题目，输出为JSON格式
"""

import pdfplumber
import json
import re
import os

def extract_text_from_pdf(pdf_path):
    """提取PDF全部文本"""
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    return '\n'.join(all_text)

def parse_questions(text, subject_name):
    """解析文本中的题目"""
    questions = []

    # 按章节分割
    chapter_pattern = r'《(\d+\.[^》]+)》'
    chapters = re.split(chapter_pattern, text)

    # chapters[0] 是目录部分，跳过
    # 之后是交替的：章节名、章节内容

    current_chapter = ""

    for i in range(1, len(chapters), 2):
        if i < len(chapters):
            current_chapter = chapters[i].strip()
        if i + 1 < len(chapters):
            chapter_content = chapters[i + 1]
            chapter_questions = parse_chapter_questions(chapter_content, current_chapter, subject_name)
            questions.extend(chapter_questions)

    return questions

def parse_chapter_questions(text, chapter, subject_name):
    """解析单个章节的题目"""
    questions = []

    # 匹配题目模式
    # 题目编号. 题干内容 (可能多行)
    # A. 选项 (可能多行)
    # B. 选项
    # C. 选项
    # D. 选项
    # E. 选项
    # 参考答案：X

    # 先按"参考答案"分割，找到所有答案位置
    answer_pattern = r'参考答案[：:]\s*([A-Ea-e])'

    # 找到所有答案
    answers = re.findall(answer_pattern, text)

    # 用更复杂的正则匹配整个题目块
    question_pattern = r'(\d+)\s*[\.．、]\s*(.+?)((?:[A-Ea-e][\.．、]\s*.+?\n?)+)\s*参考答案[：:]\s*([A-Ea-e])'

    matches = re.findall(question_pattern, text, re.DOTALL)

    for match in matches:
        q_num, question_text, options_text, answer = match

        # 清理题干文本
        question_text = clean_text(question_text)

        # 解析选项
        options = parse_options(options_text)

        if options and question_text:
            questions.append({
                "id": f"{subject_name[:2]}_{chapter}_{q_num}",
                "number": int(q_num),
                "subject": subject_name,
                "chapter": chapter,
                "question": question_text,
                "options": options,
                "answer": answer.upper()
            })

    return questions

def parse_options(options_text):
    """解析选项文本"""
    options = {}

    # 匹配选项: A. xxx 或 A、xxx
    option_pattern = r'([A-Ea-e])[\.．、]\s*(.+?)(?=[A-Ea-e][\.．、]|$)'
    matches = re.findall(option_pattern, options_text, re.DOTALL)

    for letter, text in matches:
        clean_opt = clean_text(text)
        if clean_opt:
            options[letter.upper()] = clean_opt

    return options

def clean_text(text):
    """清理文本"""
    # 移除多余的空白和换行
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

    all_questions = {}
    total_count = 0

    for pdf_path, subject_name in pdf_files:
        print(f"处理: {subject_name}...")
        text = extract_text_from_pdf(pdf_path)
        questions = parse_questions(text, subject_name)

        # 按章节组织
        subject_data = {}
        for q in questions:
            chapter = q['chapter']
            if chapter not in subject_data:
                subject_data[chapter] = []
            subject_data[chapter].append(q)

        all_questions[subject_name] = subject_data
        count = len(questions)
        total_count += count
        print(f"  提取到 {count} 道题目")

        # 保存单独文件
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)

    # 保存汇总文件
    summary_path = "/Users/moliex/projects/medical-quiz/data/all_questions.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print(f"\n总计提取 {total_count} 道题目")
    print(f"数据已保存到 /Users/moliex/projects/medical-quiz/data/")

    return all_questions

if __name__ == "__main__":
    process_all_pdfs()
