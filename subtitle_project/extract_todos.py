import re
import json
import os

file_path = r"x:\Downloads\bilingual_subtitle_final.srt"

def extract_todos():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

    todos = []
    
    for i, line in enumerate(lines):
        if "[需要人工校对:" in line:
            # The English text is usually on the previous line (i-1)
            english_line_index = i - 1
            if english_line_index >= 0:
                english_text = lines[english_line_index].strip()
                todos.append({
                    "line_number": i + 1, # 1-based index
                    "english_text": english_text
                })
    
    print(json.dumps(todos, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    extract_todos()
