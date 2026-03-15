import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def get_page_content(page):
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    url = f"https://filmpalast.to/page/{page}"
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'lxml')
        articles = soup.find_all('article', class_='liste')
        print(f"Found {len(articles)} articles with class 'liste'")
        
        if len(articles) > 0:
            print("First article title:", articles[0].find('h2').get_text(strip=True))
            
        # Check for specific "No results" text if any
        if "Keine Ergebnisse" in response.text:
            print("Found 'Keine Ergebnisse' text")
            
        return len(articles)
    except Exception as e:
        print(f"Error: {e}")
        return -1

print("--- Checking Valid Page (998) ---")
count_998 = get_page_content(998)

print("\n--- Checking Likely Invalid Page (50000) ---")
count_50000 = get_page_content(50000)
