import os
import time
import sqlite3
import logging
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

# Suppress the warning when using html.parser for XML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Configuration from Environment
RSS_URL = os.environ.get("GOODREADS_RSS_URL")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 3600))
CWA_URL = os.environ.get("CWA_URL", "http://calibre-web-automated-book-downloader:8084")
CWA_USER = os.environ.get("CWA_USER")
CWA_PASS = os.environ.get("CWA_PASS")

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GoodreadsWatcher")

# Database Setup
DB_PATH = Path("/data/watchers.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS processed_books "
            "(id TEXT PRIMARY KEY, title TEXT, processed_at DATETIME)"
        )

def is_processed(book_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT 1 FROM processed_books WHERE id = ?", (book_id,))
        return cursor.fetchone() is not None

def mark_processed(book_id, title):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO processed_books (id, title, processed_at) VALUES (?, ?, ?)",
            (book_id, title, datetime.now())
        )

def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    })
    
    if CWA_USER and CWA_PASS:
        try:
            resp = session.post(f"{CWA_URL}/api/auth/login", json={
                "username": CWA_USER,
                "password": CWA_PASS
            }, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to login to CWA: {e}")
            
    return session

def check_feed():
    if not RSS_URL:
        logger.warning("GOODREADS_RSS_URL not set")
        return

    logger.info("Checking Goodreads RSS feed...")
    session = get_session()

    try:
        rss_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
        response = requests.get(RSS_URL, headers=rss_headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')
        
        for item in items:
            guid_elem = item.find('guid') or item.find('link')
            guid = guid_elem.get_text(strip=True) if guid_elem else ""
            
            title_elem = item.find('title')
            title = title_elem.get_text(strip=True) if title_elem else ""

            if title.startswith('<![CDATA[') and title.endswith(']]>'):
                title = title[9:-3]
            if guid.startswith('<![CDATA[') and guid.endswith(']]>'):
                guid = guid[9:-3]

            if not guid or is_processed(guid):
                continue

            logger.info(f"New book found: {title}")
            
            try:
                search_resp = session.get(f"{CWA_URL}/api/search", params={"query": title}, timeout=30)
                search_resp.raise_for_status()
                results = search_resp.json()
                
                if not results or "error" in results:
                    logger.warning(f"No results found in CWA for: {title}")
                    continue
                
                best_match = results[0]
                book_id = best_match.get('id')
                
                queue_resp = session.get(f"{CWA_URL}/api/download", params={"id": book_id, "priority": 10}, timeout=10)
                queue_resp.raise_for_status()
                
                logger.info(f"Successfully queued: {best_match.get('title')}")
                mark_processed(guid, title)
                
            except Exception as e:
                logger.error(f"Error interacting with CWA for '{title}': {e}")

    except Exception as e:
        logger.error(f"Failed to fetch RSS: {e}")

if __name__ == "__main__":
    init_db()
    while True:
        check_feed()
        time.sleep(POLL_INTERVAL)
