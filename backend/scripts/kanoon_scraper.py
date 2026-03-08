import requests
from bs4 import BeautifulSoup
import json
import time
import re
import random
from pathlib import Path

# --- Configuration ---
DATA_DIR = Path("backend/app/data")
OUTPUT_FILE = DATA_DIR / "kanoon_raw.json"
TARGET_COUNT = 500

QUERIES = [
    "landlord eviction",
    "wrongful termination",
    "medical negligence",
    "cyber crime hacking",
    "domestic violence protection order",
    "fundamental rights article 21",
    "security deposit refund",
    "consumer complaint defective product",
    "environmental pollution NGT",
    "divorce alimony custody",
    "bail application criminal",
    "cheating fraud forgery",
    "negotiable instruments act section 138",
    "writ petition motor vehicle accident"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://indiankanoon.org/",
    "Connection": "keep-alive"
}

def parse_date(title_text):
    """Try to extract date from title text (e.g., '... on 24 April, 1973')."""
    match = re.search(r"on (\d+\s+\w+,\s+\d{4})", title_text)
    if match:
        return match.group(1)
    return "01-01-2000"

def scrape_kanoon():
    dataset = []
    seen_ids = set()

    for query in QUERIES:
        if len(dataset) >= TARGET_COUNT:
            break
            
        print(f"Scraping query: {query}")
        for page in range(10):  # Scrape up to 10 pages per query
            if len(dataset) >= TARGET_COUNT:
                break
                
            url = f"https://indiankanoon.org/search/?formInput={query.replace(' ', '+')}&pagenum={page}"
            try:
                # Add random jitter to be polite and avoid blocks
                time.sleep(random.uniform(2, 4))
                
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                
                if "captcha" in resp.text.lower():
                    print("BLOCKED: Captcha detected. Waiting longer...")
                    time.sleep(60)
                    continue

                soup = BeautifulSoup(resp.text, 'html.parser')
                results = soup.find_all(class_='result')
                
                if not results:
                    print(f"No more results for query '{query}' at page {page}")
                    break

                for item in results:
                    try:
                        # Extract TID
                        tid_str = item.get('data-id')
                        if not tid_str:
                            title_link = item.find('a', href=True)
                            if title_link:
                                match = re.search(r'/doc(?:fragment)?/(\d+)/', title_link['href'])
                                if match:
                                    tid_str = match.group(1)
                        
                        if not tid_str:
                            continue
                            
                        tid = int(tid_str)
                        if tid in seen_ids:
                            continue
                        
                        # Extract Title and Date
                        title_elem = item.find(class_='result_title')
                        title = ""
                        publish_date = "01-01-2000"
                        if title_elem:
                            full_title_text = title_elem.text.strip()
                            a_tag = title_elem.find('a')
                            title = a_tag.text.strip() if a_tag else full_title_text
                            publish_date = parse_date(full_title_text)

                        # Extract Source
                        source_elem = item.find(class_='docsource')
                        docsource = source_elem.text.strip() if source_elem else "Unknown"

                        # Extract Headline
                        headline_elem = item.find(class_='headline')
                        headline = headline_elem.text.strip() if headline_elem else ""

                        # Extract Citations
                        cite_tags = item.find_all('a', class_='cite_tag')
                        numcites = 0
                        numcitedby = 0
                        for tag in cite_tags:
                            text = tag.text.lower()
                            if 'cited by' in text:
                                m = re.search(r'cited by (\d+)', text)
                                if m: numcitedby = int(m.group(1))
                            elif 'cites' in text:
                                m = re.search(r'cites (\d+)', text)
                                if m: numcites = int(m.group(1))

                        dataset.append({
                            "tid": tid,
                            "title": title,
                            "headline": headline,
                            "docsource": docsource,
                            "docsize": 10000,
                            "publishdate": publish_date,
                            "numcites": numcites,
                            "numcitedby": numcitedby,
                            "catname": docsource,
                            "citeList": [],
                            "citedbyList": []
                        })
                        seen_ids.add(tid)
                        
                        if len(dataset) >= TARGET_COUNT:
                            break
                            
                    except Exception as e:
                        print(f"Error parsing result in '{query}': {e}")
                        continue

                print(f"  Captured {len(dataset)} so far...")
                
            except Exception as e:
                print(f"Error fetching page {page} for query '{query}': {e}")
                time.sleep(10)
                continue

    # Final cleanup of publishdate to DD-M-YYYY if possible, or just keep as is
    # The adapter expects DD-M-YYYY but can handle others if we are careful.
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4)
        
    print(f"Successfully scraped {len(dataset)} cases to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_kanoon()
