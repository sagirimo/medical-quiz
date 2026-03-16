"""
通用题库MD转JSON脚本
用法: python3 convert_md.py <科目名> <输入MD文件> <输出JSON文件>
例: python3 convert_md.py 妇产科学 题库md/妇科.md public/妇产科学.json
"""
import sys
import json
import re

def parse_md_table(md_content):
    """解析MD表格，返回按章节分组的题目列表"""
    chapters = {}
    question_id = 1

    for line in md_content.split('\n'):
        line = line.strip()
        if not line.startswith('|'):
            continue
        if '---|' in line or '|---' in line:
            continue
        if '题目编号' in line and '正确答案' in line:
            continue

        cells = [c.strip() for c in line.split('|')]
        cells = [c for c in cells if c]

        if len(cells) >= 10:
            try:
                chapter = cells[1]
                question = cells[3]
                opts = [f"{chr(65+i)}. {cells[4+i]}" for i in range(5)]
                answer = cells[9].upper()

                if answer not in 'ABCDE':
                    continue

                q = {
                    "id": question_id,
                    "chapter": chapter,
                    "type": "mcq",
                    "question": question,
                    "options": opts,
                    "correctAnswer": ord(answer) - ord('A'),
                    "explanation": ""
                }

                chapters.setdefault(chapter, []).append(q)
                question_id += 1
            except:
                pass

    return chapters

def main():
    if len(sys.argv) != 4:
        print("用法: python3 convert_md.py <科目名> <输入MD> <输出JSON>")
        sys.exit(1)

    subject, input_md, output_json = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(input_md, 'r', encoding='utf-8') as f:
        md_content = f.read()

    chapters = parse_md_table(md_content)
    total = sum(len(qs) for qs in chapters.values())

    print(f"{subject}: {len(chapters)} 章节, {total} 题")
    for ch, qs in chapters.items():
        print(f"  {ch}: {len(qs)} 题")

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)

    print(f"已保存: {output_json}")

if __name__ == '__main__':
    main()
