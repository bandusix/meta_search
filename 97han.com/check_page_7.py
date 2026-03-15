import requests

url = "http://www.97han.com/type/1-7.html"
print(f"Checking {url}...")

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("Page exists!")
    else:
        print("Page NOT found!")
except Exception as e:
    print(f"Error: {e}")
