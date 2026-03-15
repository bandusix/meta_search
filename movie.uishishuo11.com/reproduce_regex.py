
import re
from bs4 import BeautifulSoup

def test_parse(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    data = {}
    info = soup.find('div', class_='myui-content__detail')
    
    if not info:
        # Simulate what the crawler does if it finds the div
        # But here we just use the soup directly if user provided partial html inside a div structure
        # The user provided <p class="data">...
        # So we wrap it in a mock div structure
        info = soup
        
    category_text = info.find('span', string='分类：')
    if category_text:
        parent = category_text.parent
        full_text = parent.get_text(strip=True)
        print(f"Full Text: {full_text}")
        
        # Original Regex
        match = re.search(r'分类：(.+?)地区：(.+?)年份：(\d+)', full_text)
        if match:
            print("Original Regex: MATCH")
            print(f"Category: {match.group(1)}")
            print(f"Region: {match.group(2)}")
            print(f"Year: {match.group(3)}")
        else:
            print("Original Regex: NO MATCH")
            
        # Proposed Fix: More flexible regex
        # Allow year to be non-digit, and handle potentially missing parts if needed
        # We use (.*?) for year, but need to be careful about what comes after.
        # Usually it's the end of string or another tag.
        match_fix = re.search(r'分类：(.+?)地区：(.+?)年份：(.*)', full_text)
        if match_fix:
            print("Fixed Regex: MATCH")
            print(f"Category: {match_fix.group(1)}")
            print(f"Region: {match_fix.group(2)}")
            year_str = match_fix.group(3).strip()
            print(f"Year Raw: {year_str}")
            # Try to extract number, default to 0
            year_match = re.search(r'(\d+)', year_str)
            year = int(year_match.group(1)) if year_match else 0
            print(f"Year Parsed: {year}")
        else:
            print("Fixed Regex: NO MATCH")

# User provided HTML
html = """
<div class="myui-content__detail">
<p class="data"><span class="text-muted">分类：</span><a href="/vodshow/34-----------.html">短剧</a><span class="split-line"></span><span class="text-muted hidden-xs">地区：</span><a href="/vodshow/34-----------.html">未知</a><span class="split-line"></span><span class="text-muted hidden-xs">年份：</span><a href="/vodshow/34-----------.html">未知</a></p>
</div>
"""

test_parse(html)
