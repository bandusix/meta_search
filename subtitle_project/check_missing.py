import re
import json

file_path = r"x:\WORK\FALCON\Capybaba\Script\subtitle_project\bilingual_subtitle_final_fixed_v2.srt"

def is_chinese(text):
    # Basic check for Chinese characters
    return any(u'\u4e00' <= char <= u'\u9fff' for char in text)

def analyze_srt():
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newlines to get blocks
    # SRT blocks are usually separated by blank lines.
    # However, sometimes there might be inconsistencies.
    # A better way is to iterate line by line.
    
    lines = content.splitlines()
    blocks = []
    current_block = []
    
    for line in lines:
        if line.strip() == "":
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
            
    if current_block:
        blocks.append(current_block)

    missing_translation = []

    for block in blocks:
        if len(block) < 3:
            continue # Skip invalid blocks
            
        index = block[0]
        timestamp = block[1]
        
        # Usually:
        # 0: Index
        # 1: Time
        # 2: English
        # 3: Chinese (Optional/Missing)
        
        if len(block) == 3:
            # Only English line present
            english_text = block[2]
            missing_translation.append({
                "index": index,
                "timestamp": timestamp,
                "english": english_text,
                "reason": "Missing Chinese line"
            })
        elif len(block) >= 4:
            english_text = block[2]
            chinese_text = block[3]
            
            if not is_chinese(chinese_text) and chinese_text.strip() != "..." and not re.search(r'[0-9]+', chinese_text):
                 # If it doesn't look like Chinese, and isn't just numbers (sometimes subtitles are just numbers), mark it.
                 # Also exclude "..." which might be valid in some cases but usually indicates waiting.
                 # But the user specifically mentioned "..." as an issue in the example provided (Line 49).
                 pass

            if chinese_text.strip() == "..." or chinese_text.strip() == "…":
                 missing_translation.append({
                    "index": index,
                    "timestamp": timestamp,
                    "english": english_text,
                    "current_translation": chinese_text,
                    "reason": "Placeholder '...'"
                })
            elif not is_chinese(chinese_text):
                # Check if it's just punctuation or symbols
                clean_text = re.sub(r'[^\w\s]', '', chinese_text)
                if len(clean_text) > 0 and not any(u'\u4e00' <= char <= u'\u9fff' for char in clean_text):
                     # It has content but no Chinese characters. Might be English repetition or untranslated.
                     # However, sometimes subtitles are just names or "Oh" "Ah", which might be fine in English.
                     # Let's collect them for review.
                     missing_translation.append({
                        "index": index,
                        "timestamp": timestamp,
                        "english": english_text,
                        "current_translation": chinese_text,
                        "reason": "No Chinese characters"
                    })
    
    print(json.dumps(missing_translation, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    analyze_srt()
