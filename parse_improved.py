#!/usr/bin/env python3
"""
PDF题目解析脚本 - 改进版
处理跨栏跨页的题目
"""

import pdfplumber
import json
import re
import os

def get_chapter_list(pdf_path):
    """从目录页提取章节列表"""
    chapters = []
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        pattern = r'《(\d+\.[^》]+)》\s*\.+\s*(\d+)'
        for match in re.finditer(pattern, text):
            chapters.append({
                'name': match.group(1).strip(),
                'start_page': int(match.group(2))
            })

    for i in range(len(chapters)):
        chapters[i]['end_page'] = chapters[i+1]['start_page'] if i < len(chapters)-1 else 999

    return chapters

def extract_all_text_sequentially(pdf_path):
    """按阅读顺序提取所有文本（处理双栏）"""
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            width = page.width
            height = page.height

            left_col = page.crop((0, 0, width/2, height))
            right_col = page.crop((width/2, 0, width, height))

            left_text = left_col.extract_text() or ""
            right_text = right_col.extract_text() or ""

            all_text.append({
                'page': page_num + 1,
                'left': left_text,
                'right': right_text,
                'combined': left_text + "\n" + right_text
            })

    return all_text

def parse_all_questions(all_text, chapters, subject_name):
    """解析所有题目，处理跨栏跨页"""
    questions = []
    current_chapter = "未知章节"

    # 构建连续文本流
    full_text_parts = []
    for page_data in all_text:
        full_text_parts.append(page_data['combined'])

    full_text = "\n\n--- PAGE ---\n\n".join(full_text_parts)

    # 按章节处理
    for chapter_info in chapters:
        chapter_name = chapter_info['name']
        start = chapter_info['start_page']
        end = chapter_info['end_page']

        # 提取该章节的文本
        chapter_text = ""
        for page_data in all_text:
            if start <= page_data['page'] < end:
                # 合并左右栏，按列顺序
                chapter_text += page_data['left'] + "\n" + page_data['right'] + "\n"

        # 解析题目
        chapter_questions = parse_questions_from_text(chapter_text, chapter_name, subject_name)
        questions.extend(chapter_questions)

    return questions

def parse_questions_from_text(text, chapter_name, subject_name):
    """从文本中解析题目"""
    questions = []

    # 清理干扰
    text = re.sub(r'得\s*分\s*[：:]?\s*\d*\.?\d*', '', text)
    text = re.sub(r'[一二三四五六七八九十]+、[A-Z]\d?型题.*?分[。）]', '', text)
    text = re.sub(r'《\d+\.[^》]+》', '', text)

    # 更宽松的匹配：找到所有题目块
    # 格式：数字. 内容... 选项... 参考答案

    # 方法：按"参考答案"分割，向前查找题目
    segments = re.split(r'(参考答案[：:]\s*[A-Ea-e])', text)

    for i in range(1, len(segments), 2):
        if i >= len(segments):
            continue

        answer_text = segments[i]
        answer = answer_text[-1].upper()

        # 前一段是题目内容
        if i > 0:
            content = segments[i-1]

            # 找最后一个完整题目编号
            matches = list(re.finditer(r'\n\s*(\d+)\s*[\.．、]\s+', content))

            if not matches:
                # 尝试匹配行首的题目编号
                matches = list(re.finditer(r'(\d+)\s*[\.．、]\s+(?=[^\d])', content))

            if not matches:
                continue

            last_match = matches[-1]
            q_num = int(last_match.group(1))
            q_content = content[last_match.start():]

            # 分离题干和选项
            # 找选项开始
            opt_match = re.search(r'\n\s*([A-Ea-e])\s*[\.．、]', q_content)

            if not opt_match:
                continue

            question_text = q_content[:opt_match.start()].strip()
            options_text = q_content[opt_match.start():]

            # 清理题干
            question_text = re.sub(r'^\d+\s*[\.．、]\s*', '', question_text)
            question_text = re.sub(r'\s+', ' ', question_text).strip()

            if len(question_text) < 5:
                continue

            # 解析选项
            options = {}
            for m in re.finditer(r'([A-Ea-e])\s*[\.．、]\s*(.+?)(?=\n\s*[A-Ea-e]\s*[\.．、]|参考答案|$)', options_text, re.DOTALL):
                letter = m.group(1).upper()
                opt_content = re.sub(r'\s+', ' ', m.group(2)).strip()
                if opt_content:
                    options[letter] = opt_content

            if len(options) >= 2:
                questions.append({
                    'chapter': chapter_name,
                    'subject': subject_name,
                    'question': question_text,
                    'options': options,
                    'answer': answer
                })

    return questions

def process_pdf(pdf_path, subject_name):
    """处理PDF"""
    print(f"\n处理: {subject_name}")

    chapters = get_chapter_list(pdf_path)
    print(f"  章节: {len(chapters)} 个")

    all_text = extract_all_text_sequentially(pdf_path)
    questions = parse_all_questions(all_text, chapters, subject_name)

    # 去重并按章节组织
    chapters_data = {}
    seen = set()

    for q in questions:
        key = (q['chapter'], q['question'][:30])
        if key in seen:
            continue
        seen.add(key)

        ch = q['chapter']
        if ch not in chapters_data:
            chapters_data[ch] = []
        chapters_data[ch].append(q)

    # 更新编号
    for ch, qs in chapters_data.items():
        for i, q in enumerate(qs, 1):
            q['number'] = i
            q['id'] = f"{subject_name[:2]}_{ch[:8]}_{i}".replace('.', '_').replace(' ', '_')

    for ch in chapters:
        name = ch['name']
        count = len(chapters_data.get(name, []))
        if count > 0:
            print(f"  {name}: {count} 题")

    return chapters_data

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
    expected_total = 0

    for pdf_path, subject_name, expected in pdf_files:
        chapters = process_pdf(pdf_path, subject_name)
        all_data[subject_name] = chapters

        count = sum(len(qs) for qs in chapters.values())
        total += count
        expected_total += expected
        print(f"  小计: {count}/{expected} ({count/expected*100:.1f}%)")

        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total}/{expected_total} ({total/expected_total*100:.1f}%)")

    return all_data

if __name__ == "__main__":
    process_all()
