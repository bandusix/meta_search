import requests
from parsers.list_parser import ListPageParser

def check_no_year_url():
    # Construct URL without year: category 1 (movie), page 1
    # Standard: /vodshow/1--------1---2024.html
    # No Year: /vodshow/1--------1---.html
    url = "https://jzftdz.com/vodshow/1--------1---.html"
    print(f"Testing URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("Request successful!")
            # Parse to see if we get items and what years they are
            cards, _ = ListPageParser.parse(response.text, 1, "https://jzftdz.com")
            if cards:
                print(f"Found {len(cards)} items.")
                for i, card in enumerate(cards[:5]):
                    print(f"{i+1}. {card['title']} (URL: {card['detail_url']})")
                
                # Check if we have mixed years or just new items
                # Since list parser doesn't extract year (detail parser does), we can't be 100% sure from list.
                # But if we get items, it means the URL is valid.
                return True
            else:
                print("No items parsed.")
        else:
            print(f"Request failed with status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == "__main__":
    check_no_year_url()
