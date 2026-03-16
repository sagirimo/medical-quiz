"""
北医题库 PDF 解析引擎 (PyMuPDF 多栏布局版)
pip install pymupdf
"""
import fitz  # PyMuPDF
import re
import json
import os

def extract_questions_from_pdf(pdf_path):
    """
    使用PyMuPDF解析多栏布局的PDF题库
    """
    # 正则表达式
    regex_chapter = re.compile(r'^《(\d+)\.(.*?)》')
    regex_question = re.compile(r'^(\d+)\s*\.\s*(.+)')
    regex_option = re.compile(r'^([A-E])\s*[.、．]\s*(.+)')
    regex_answer = re.compile(r'参考答案\s*[:：]\s*([A-E])')

    ignore_keywords = ["一、A1型题", "一、A2型题", "二、A", "得分:", "目录", "合计"]

    doc = fitz.open(pdf_path)
    page_width = doc[0].rect.width
    mid_point = page_width / 2  # 左右栏分界点

    print(f"🚀 解析: {os.path.basename(pdf_path)}")
    print(f"   页面宽度: {page_width:.0f}, 中分线: {mid_point:.0f}")

    questions = []
    current_chapter = "未知章节"

    for page_num, page in enumerate(doc):
        # 获取所有文本块
        blocks = page.get_text("blocks")

        # 分离左右栏
        left_blocks = []
        right_blocks = []

        for b in blocks:
            if b[6] != 0:  # 跳过图片块
                continue
            x0 = b[0]
            text = b[4].strip()
            if not text:
                continue

            # 根据x坐标分栏
            if x0 < mid_point:
                left_blocks.append((b[1], x0, text))  # (y, x, text)
            else:
                right_blocks.append((b[1], x0, text))

        # 左栏从上到下，然后右栏从上到下
        left_blocks.sort(key=lambda t: t[0])
        right_blocks.sort(key=lambda t: t[0])

        all_text_blocks = left_blocks + right_blocks

        # 解析每个文本块
        for y, x, text in all_text_blocks:
            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 检查章节
                chap_match = regex_chapter.match(line)
                if chap_match:
                    current_chapter = chap_match.group(2).strip()
                    continue

                # 过滤垃圾
                if any(kw in line for kw in ignore_keywords):
                    continue

                # 页码过滤
                if re.match(r'^\d+\s*/\s*\d+$', line):
                    continue

                # 检查题目
                q_match = regex_question.match(line)
                if q_match:
                    # 检查这一行是否包含答案（可能跟在后面）
                    ans_in_line = regex_answer.search(line)
                    if ans_in_line:
                        answer = ans_in_line.group(1)
                    else:
                        answer = ''

                    # 提取题号和题干
                    qid = q_match.group(1)
                    question_text = q_match.group(2)

                    # 从题干中提取答案（如果有的话）
                    ans_match = regex_answer.search(question_text)
                    if ans_match:
                        answer = ans_match.group(1)
                        question_text = regex_answer.sub('', question_text).strip()

                    # 提取选项
                    options = []
                    remaining_text = question_text

                    # 找所有选项
                    opt_pattern = re.compile(r'([A-E])\s*[.、．]\s*([^A-E]+?)(?=([A-E]\s*[.、．])|$)')
                    matches = list(opt_pattern.finditer(question_text))

                    if matches:
                        # 有内联选项
                        for m in matches:
                            opt_letter = m.group(1)
                            opt_text = m.group(2).strip()
                            if opt_text:
                                options.append(f"{opt_letter}. {opt_text}")

                        # 题干是第一个选项之前的内容
                        first_opt_start = matches[0].start()
                        question_text = question_text[:first_opt_start].strip()

                    # 单独处理答案行
                    if not answer:
                        # 检查是否有答案标记
                        pass

                    # 只有当有足够选项时才保存
                    if len(options) >= 4 and answer:
                        questions.append({
                            'id': len(questions) + 1,
                            'chapter': current_chapter,
                            'type': 'mcq',
                            'question': question_text,
                            'options': options[:5],  # 最多5个选项
                            'correctAnswer': answer,
                            'explanation': ''
                        })

    doc.close()

    print(f"✅ 提取了 {len(questions)} 道题目")
    return questions


def process_pdf_v2(pdf_path):
    """
    改进版：逐行处理，更精确地提取题目
    """
    regex_chapter = re.compile(r'^《(\d+)\.(.*?)》')
    regex_question = re.compile(r'^(\d+)\s*\.\s*(.+)')
    regex_option = re.compile(r'^([A-E])\s*[.、．]\s*(.+)')
    regex_answer = re.compile(r'参考答案\s*[:：]\s*([A-E])')

    ignore_keywords = ["一、A1型题", "一、A2型题", "二、A", "得分:", "目录", "合计", "北医"]

    doc = fitz.open(pdf_path)
    page_width = doc[0].rect.width
    mid_point = page_width / 2

    print(f"🚀 解析: {os.path.basename(pdf_path)}")

    questions = []
    current_chapter = "未知章节"

    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")

        # 分栏并排序
        left_blocks = [(b[0], b[1], b[4]) for b in blocks if b[6] == 0 and b[0] < mid_point]
        right_blocks = [(b[0], b[1], b[4]) for b in blocks if b[6] == 0 and b[0] >= mid_point]

        left_blocks.sort(key=lambda t: (t[1], t[0]))  # 按y, x排序
        right_blocks.sort(key=lambda t: (t[1], t[0]))

        all_lines = []

        for _, _, text in left_blocks + right_blocks:
            for line in text.split('\n'):
                line = line.strip()
                if line:
                    all_lines.append(line)

        # 状态机处理
        current_q = None
        current_state = None

        for line in all_lines:
            # 章节检测
            chap_match = regex_chapter.match(line)
            if chap_match:
                current_chapter = chap_match.group(2).strip()
                continue

            # 垃圾过滤
            if any(kw in line for kw in ignore_keywords):
                continue
            if re.match(r'^\d+\s*/\s*\d+$', line):
                continue

            # 答案行
            ans_match = regex_answer.search(line)
            if ans_match and current_q:
                current_q['answer'] = ans_match.group(1)
                # 保存题目
                if len(current_q['options']) >= 4:
                    questions.append({
                        'id': len(questions) + 1,
                        'chapter': current_q['chapter'],
                        'type': 'mcq',
                        'question': current_q['question'],
                        'options': current_q['options'],
                        'correctAnswer': current_q['answer'],
                        'explanation': ''
                    })
                current_q = None
                current_state = None
                continue

            # 题目行
            q_match = regex_question.match(line)
            if q_match:
                # 保存上一题（如果有）
                if current_q and len(current_q['options']) >= 4 and current_q['answer']:
                    questions.append({
                        'id': len(questions) + 1,
                        'chapter': current_q['chapter'],
                        'type': 'mcq',
                        'question': current_q['question'],
                        'options': current_q['options'],
                        'correctAnswer': current_q['answer'],
                        'explanation': ''
                    })

                # 开始新题
                current_q = {
                    'chapter': current_chapter,
                    'question': q_match.group(2),
                    'options': [],
                    'answer': ''
                }
                current_state = 'question'
                continue

            # 选项行
            opt_match = regex_option.match(line)
            if opt_match:
                if current_q:
                    opt_text = f"{opt_match.group(1)}. {opt_match.group(2)}"
                    current_q['options'].append(opt_text)
                current_state = 'option'
                continue

            # 续行
            if current_q:
                if current_state == 'question':
                    current_q['question'] += ' ' + line
                elif current_state == 'option' and current_q['options']:
                    current_q['options'][-1] += line

    # 保存最后一题
    if current_q and len(current_q['options']) >= 4 and current_q['answer']:
        questions.append({
            'id': len(questions) + 1,
            'chapter': current_q['chapter'],
            'type': 'mcq',
            'question': current_q['question'],
            'options': current_q['options'],
            'correctAnswer': current_q['answer'],
            'explanation': ''
        })

    doc.close()
    print(f"✅ 提取了 {len(questions)} 道题目")
    return questions


def convert_to_frontend_format(questions):
    answer_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    return [{
        'id': q['id'],
        'chapter': q['chapter'],
        'type': q['type'],
        'question': q['question'],
        'options': q['options'],
        'correctAnswer': answer_map.get(q['correctAnswer'], 0),
        'explanation': q['explanation']
    } for q in questions]


def group_by_chapter(questions):
    chapters = {}
    for q in questions:
        c = q['chapter']
        if c not in chapters:
            chapters[c] = []
        chapters[c].append(q)
    return chapters


if __name__ == "__main__":
    desktop_path = "/mnt/c/Users/administrator/Desktop"

    pdf_files = {
        "儿科学": "北医儿科学题库-770题（分章节重排）.pdf",
        "内科学": "北医内科学题库-706题（分章节重排）.pdf",
        "外科学": "北医外科学题库-702题（分章节重排）.pdf",
        "妇产科学": "北医妇产科学题库-750题（分章节重排）.pdf"
    }

    output_dir = "/mnt/c/Dev/Projects/medical-quiz/data"
    os.makedirs(output_dir, exist_ok=True)

    for subject, filename in pdf_files.items():
        pdf_path = os.path.join(desktop_path, filename)
        if not os.path.exists(pdf_path):
            print(f"⚠️  文件不存在: {filename}")
            continue

        questions = process_pdf_v2(pdf_path)
        questions = convert_to_frontend_format(questions)
        chapters = group_by_chapter(questions)

        output_file = os.path.join(output_dir, f"{subject}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

        print(f"💾 保存: {output_file}")
        print(f"   章节: {len(chapters)} 个, 题目: {len(questions)} 道\n")

    print("🎉 全部完成！")
