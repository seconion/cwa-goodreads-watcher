# CWA Goodreads Watcher

An automated sidecar for **Calibre-Web Automated (CWA)** that monitors your Goodreads RSS feed and automatically queues new books for download.

## 🚀 How it Works
This project runs as a lightweight "sidecar" container alongside your [Calibre-Web Automated Book Downloader](https://github.com/calibrain/calibre-web-automated-book-downloader) instance.

1.  **Monitor:** It polls your Goodreads "To-Read" (or any other) shelf RSS feed.
2.  **Clean:** It automatically strips CDATA tags and handles XML/HTML parsing issues.
3.  **Search:** When a new book is found, it calls the CWA API to search for the best available copy.
4.  **Download:** It automatically queues the best match for download in CWA.

## 🛠️ Installation

### Step 1: Prepare your configuration
Before starting the containers, you need to set up your private settings (like passwords and RSS links).

1. Find the file named `.env.example` in the folder.
2. Make a copy of it and name the new file exactly `.env`. 
   - *On Linux/Mac:* `cp .env.example .env`
   - *On Windows:* Copy and paste, then rename.
3. Open the new `.env` file with any text editor and fill in your details:
   - **GOODREADS_RSS_URL**: Your secret Goodreads link.
   - **CWA_USER** / **CWA_PASS**: Your login for the downloader.
   - **CWA_URL**: How the watcher reaches the downloader.

### Step 2: Choose your Deployment Option

You can run this watcher either as a standalone service (if you already have CWA running) or combined with a new CWA instance.

#### Option A: Standalone (Connect to existing CWA)
Use this if CWA is already running on your server or in another stack.

1. Ensure you have `watcher.py`, `.env`, and `docker-compose.standalone.yml` in the same folder.
2. Run: `docker compose -f docker-compose.standalone.yml up -d`
   - **Note on Networking:** If CWA is in a different Docker Compose stack, ensure both containers share the same Docker network, or use the host IP for `CWA_URL` in your `.env`.

#### Option B: Combined (Full Stack)
Use this to spin up both CWA and the Watcher together.

1. Ensure you have `watcher.py`, `.env`, and `docker-compose.combined.yml` in the same folder.
2. Run: `docker compose -f docker-compose.combined.yml up -d`

### Option 3: Add to existing Stack
Add the following service definition to your existing `docker-compose.yaml`:

```yaml
  goodreads-watcher:
    image: python:3.11-slim
    container_name: goodreads-watcher
    # ... (see docker-compose.standalone.yml for full env details)
```

## ⚙️ Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GOODREADS_RSS_URL` | Your private Goodreads RSS feed URL. | Required |
| `POLL_INTERVAL` | How often to check for new books (in seconds). | `3600` |
| `CWA_URL` | Internal or external URL of your CWA instance. | `http://...:8084` |
| `CWA_USER` | Your CWA username. | Optional |
| `CWA_PASS` | Your CWA password. | Optional |

## 📚 Dependencies
- [Calibre-Web Automated Book Downloader](https://github.com/calibrain/calibre-web-automated-book-downloader)
- Python 3.x
- `requests`
- `beautifulsoup4`

## ⚖️ License
MIT
