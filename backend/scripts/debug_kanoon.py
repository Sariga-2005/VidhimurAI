import requests

url = "https://indiankanoon.org/search/?formInput=landlord+eviction&pagenum=0"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://indiankanoon.org/",
    "Connection": "keep-alive"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content Length: {len(resp.text)}")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = soup.find_all(class_='result')
    print(f"Results found: {len(results)}")
    if len(results) > 0:
        print("Success: results found")
        first = results[0]
        title_elem = first.find(class_='result_title')
        print(f"First Title: {title_elem.text.strip() if title_elem else 'Not found'}")
    else:
        print("Failure: NO results found")
        # Print a snippet of the body to see what's there
        print(resp.text[2000:4000])
except Exception as e:
    print(f"Error: {e}")
