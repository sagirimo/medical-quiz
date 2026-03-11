#!/usr/bin/env python3
"""
PDF题目解析脚本 - 简化版
接受一定损失，优先保证解析速度和正确性
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
            width = page.width

            # 分栏提取
            left_col = page.crop((0, 0, width/2, page.height))
            right_col = page.crop((width/2, 0, width, page.height))

            left_text = left_col.extract_text() or ""
            right_text = right_col.extract_text() or ""

            # 检测章节
            full_page_text = left_text + right_text
            chapter_match = re.search(r'《(\d+\.[^》]+)》', full_page_text)
            if chapter_match:
                current_chapter = chapter_match.group(1).strip()

            # 分别处理两栏
            for col_text in [left_text, right_text]:
                col_questions = parse_column(col_text, current_chapter, subject_name)
                questions.extend(col_questions)

    return questions

def parse_column(text, chapter, subject_name):
    """解析单栏文本中的题目"""
    questions = []

    # 预处理
    text = re.sub(r'得\s*分\s*[：:]?\s*\d*\.?\d*', '', text)
    text = re.sub(r'[一二]、[A-Z]\d?型题\s*\(合计.*?\)', '', text)
    text = re.sub(r'《\d+\.[^》]+》', '', text)

    # 简单正则：找完整的题目块
    # 数字. 内容 + A.B.C.D.E选项 + 参考答案
    pattern = r'(\d+)\s*[\.．]\s*(.+?)((?:[A-Ea-e]\s*[\.．、].+?\n?){2,5})\s*参考答案[：:]\s*([A-Ea-e])'

    for match in re.finditer(pattern, text, re.DOTALL):
        q_num = match.group(1)
        question_text = match.group(2).strip()
        options_text = match.group(3)
        answer = match.group(4).upper()

        # 清理题干
        question_text = re.sub(r'\s+', ' ', question_text).strip()
        if len(question_text) < 10:
            continue

        # 解析选项
        options = {}
        opt_pattern = r'([A-Ea-e])\s*[\.．、]\s*(.+?)(?=\s+[A-Ea-e]\s*[\.．、]|参考答案|$)'
        for opt_match in re.finditer(opt_pattern, options_text, re.DOTALL):
            letter = opt_match.group(1).upper()
            content = re.sub(r'\s+', ' ', opt_match.group(2)).strip()
            if content and len(content) > 0:
                options[letter] = content

        if len(options) >= 2:
            questions.append({
                'number': int(q_num),
                'chapter': chapter,
                'subject': subject_name,
                'question': question_text,
                'options': options,
                'answer': answer
            })

    return questions

def process_all_pdfs():
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
        print(f"\n处理: {subject_name} (预期约{expected}题)")
        questions = extract_questions_from_pdf(pdf_path, subject_name)

        # 去重
        seen = set()
        unique = []
        for q in questions:
            key = q['question'][:40]
            if key not in seen:
                seen.add(key)
                unique.append(q)

        # 按章节组织
        chapters = {}
        for q in unique:
            ch = q['chapter']
            if ch not in chapters:
                chapters[ch] = []
            chapters[ch].append(q)

        # 重新编号
        for ch, qs in chapters.items():
            for i, q in enumerate(qs, 1):
                q['number'] = i
                q['id'] = f"{subject_name}_{ch[:8]}_{i}".replace('.', '_').replace(' ', '_')

        all_data[subject_name] = chapters
        count = sum(len(qs) for qs in chapters.values())
        total += count
        coverage = count / expected * 100
        print(f"  提取: {count} 道 ({coverage:.1f}%)")

        for ch, qs in sorted(chapters.items()):
            print(f"    {ch}: {len(qs)} 道")

        # 保存
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    # 保存汇总
    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total} 道题目")

    return all_data

if __name__ == "__main__":
    process_all_pdfs()
