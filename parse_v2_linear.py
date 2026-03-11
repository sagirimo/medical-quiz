#!/usr/bin/env python3
"""
PDF题目解析脚本 - 基于布局的线性流方案
核心思路：物理切分 + 线性化流 + 正则锚点
"""

import pdfplumber
import json
import re
import os

def extract_linear_stream(pdf_path, margin_top=30, margin_bottom=50):
    """
    Step 1 & 2: 页面垂直切分 + 线性流重组
    按照 P1-左 -> P1-右 -> P2-左 -> P2-右 的顺序构建文本河流
    """
    all_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            width = page.width
            height = page.height

            # 左栏裁剪区域
            left_col = page.crop((0, margin_top, width/2, height - margin_bottom))
            # 右栏裁剪区域
            right_col = page.crop((width/2, margin_top, width, height - margin_bottom))

            # 提取文本（先左后右）
            left_text = left_col.extract_text() or ""
            right_text = right_col.extract_text() or ""

            # 清理并添加行
            for text in [left_text, right_text]:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        all_lines.append(line)

    return all_lines


def detect_chapters_and_questions(all_lines):
    """
    Step 3: 正则锚点检测章节和题目边界
    """
    # 章节标题模式
    chapter_pattern = re.compile(r'^《(\d+\.[^》]+)》')

    # 题目开始模式 (如 "1." "10、" "1．")
    question_start_pattern = re.compile(r'^(\d+)\s*[\.．、]\s*')

    # 参考答案模式
    answer_pattern = re.compile(r'参考答案[：:]\s*([A-Ea-e])')

    # 选项模式
    option_pattern = re.compile(r'^([A-Ea-e])\s*[\.．、]')

    chapters = {}  # {章节名: [题目列表]}
    current_chapter = "未知章节"
    current_question_lines = []
    questions = []

    for line in all_lines:
        # 检测章节标题
        chapter_match = chapter_pattern.match(line)
        if chapter_match:
            # 保存当前章节的题目
            if current_question_lines and questions:
                chapters[current_chapter] = questions
                questions = []

            current_chapter = chapter_match.group(1).strip()

            # 检查是否是新的章节（不在chapters中）
            if current_chapter not in chapters:
                chapters[current_chapter] = []
            continue

        # 检测题目开始
        q_match = question_start_pattern.match(line)

        if q_match:
            # 如果当前有缓存的题目行，先保存
            if current_question_lines:
                question_obj = parse_question_buffer(current_question_lines)
                if question_obj:
                    questions.append(question_obj)

            # 开始新题目
            current_question_lines = [line]
        else:
            # 追加到当前题目
            if current_question_lines:
                current_question_lines.append(line)
            else:
                # 可能是章节开头的一些说明文字，忽略
                pass

    # 处理最后一个题目
    if current_question_lines:
        question_obj = parse_question_buffer(current_question_lines)
        if question_obj:
            questions.append(question_obj)

    # 保存最后一个章节
    if questions:
        if current_chapter in chapters:
            chapters[current_chapter].extend(questions)
        else:
            chapters[current_chapter] = questions

    return chapters


def parse_question_buffer(lines):
    """
    Step 4: 结构化解析单个题目
    从题目行缓冲中提取题干、选项、答案
    """
    if not lines:
        return None

    # 组合成文本
    text = '\n'.join(lines)

    # 提取答案
    answer_match = re.search(r'参考答案[：:]\s*([A-Ea-e])', text)
    if not answer_match:
        return None

    answer = answer_match.group(1).upper()

    # 移除答案行
    text = re.sub(r'参考答案[：:]\s*[A-Ea-e]', '', text)

    # 提取题目编号
    num_match = re.match(r'(\d+)\s*[\.．、]\s*', text)
    if not num_match:
        return None

    q_num = int(num_match.group(1))
    text = text[num_match.end():]

    # 分离题干和选项
    # 找第一个选项的位置
    option_start = re.search(r'\n\s*([A-Ea-e])\s*[\.．、]', text)

    if not option_start:
        # 尝试在同行找选项
        option_start = re.search(r'([A-Ea-e])\s*[\.．、]', text)

    if not option_start:
        return None

    question_text = text[:option_start.start()].strip()
    options_text = text[option_start.start():]

    # 清理题干
    question_text = re.sub(r'\s+', ' ', question_text).strip()

    if len(question_text) < 5:
        return None

    # 解析选项
    options = {}
    for match in re.finditer(r'([A-Ea-e])\s*[\.．、]\s*(.+?)(?=\s*[A-Ea-e]\s*[\.．、]|$)', options_text, re.DOTALL):
        letter = match.group(1).upper()
        content = re.sub(r'\s+', ' ', match.group(2)).strip()
        if content:
            options[letter] = content

    if len(options) < 2:
        return None

    return {
        'number': q_num,
        'question': question_text,
        'options': options,
        'answer': answer
    }


def process_pdf(pdf_path, subject_name):
    """处理单个PDF"""
    print(f"\n处理: {subject_name}")

    # Step 1 & 2: 构建线性文本流
    all_lines = extract_linear_stream(pdf_path)
    print(f"  提取行数: {len(all_lines)}")

    # Step 3 & 4: 检测章节和题目
    chapters = detect_chapters_and_questions(all_lines)

    # 输出统计
    total = 0
    for chapter, questions in chapters.items():
        print(f"  {chapter}: {len(questions)} 题")
        total += len(questions)

    print(f"  小计: {total} 题")

    return chapters


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
    expected_total = 0

    for pdf_path, subject_name, expected in pdf_files:
        chapters = process_pdf(pdf_path, subject_name)

        # 添加元数据
        for chapter, questions in chapters.items():
            for i, q in enumerate(questions, 1):
                q['id'] = f"{subject_name[:2]}_{chapter[:8]}_{i}".replace('.', '_').replace(' ', '_')
                q['chapter'] = chapter
                q['subject'] = subject_name
                q['number'] = i

        all_data[subject_name] = chapters

        count = sum(len(qs) for qs in chapters.values())
        total += count
        expected_total += expected

        # 保存
        output_path = f"/Users/moliex/projects/medical-quiz/data/{subject_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    # 保存汇总
    with open("/Users/moliex/projects/medical-quiz/data/all_questions.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"总计: {total}/{expected_total} ({total/expected_total*100:.1f}%)")

    return all_data


if __name__ == "__main__":
    process_all_pdfs()
