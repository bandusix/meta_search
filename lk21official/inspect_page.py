import requests
from bs4 import BeautifulSoup

url = "https://tv8.lk21official.cc/truth-2015"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check Image
    print("\n--- Images ---")
    imgs = soup.find_all('img')
    for img in imgs:
        # Check for poster-like images
        if 'myui' in str(img.parent) or 'lazyload' in img.get('class', []) or img.get('itemprop') == 'image':
            print(f"Tag: {img}")
            print(f"Parent class: {img.parent.get('class')}")
            print(f"Src: {img.get('src')}")
            print(f"Data-Original: {img.get('data-original')}")
            print("-" * 20)

    # Check Breadcrumbs/Category
    print("\n--- Breadcrumbs / Category ---")
    breadcrumbs = soup.select('.breadcrumb, .breadcrumbs, .path')
    if breadcrumbs:
        print(breadcrumbs[0].text.strip())
    
    # Check Genre/Tags
    print("\n--- Tags / Genres ---")
    tags = soup.select('.tag-list a, .genre a, a[rel="category tag"]')
    for tag in tags:
        print(f"Text: {tag.text}, Href: {tag.get('href')}")
        
    # Check "Short Drama" keywords in page
    print("\n--- Keywords Check ---")
    text = soup.get_text()
    keywords = ["Short Drama", "Drama", "Series", "TV Series", "短剧", "电视剧", "Episode", "Season"]
    for kw in keywords:
        if kw in text:
            print(f"Found keyword: {kw}")

except Exception as e:
    print(f"Error: {e}")
