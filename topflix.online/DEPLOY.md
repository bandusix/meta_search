# TopFlix Crawler Deployment Guide

This document describes how to deploy the TopFlix Crawler to a production environment.

## 1. Environment Requirements
- **OS**: Linux (Ubuntu 22.04+ recommended) or Windows Server
- **Python**: 3.10 or higher
- **Disk Space**: At least 10GB (for database and logs)
- **Memory**: 2GB+ RAM

## 2. Installation

1.  **Clone the Repository** (or upload the project folder):
    ```bash
    # Upload the project files to /opt/topflix_crawler or similar
    cd /opt/topflix_crawler
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install schedule  # For the scheduler
    ```

## 3. Configuration
- Modify `spider_main.py` if you need to change:
    - `TARGET_COUNT`: Default crawl limit.
    - `MAX_WORKERS`: Number of threads (Default: 10).
    - `BASE_URL`: Target website URL.

## 4. Running Full Crawl (First Time)
To populate the database with all existing content:

```bash
# Run with a high limit (e.g., 20,000 items) and 20 threads
python spider_main.py 20000 20
```

## 5. Running Daily Incremental Crawl
Use the included scheduler to run the crawler daily (default at 02:00 AM).

### Method A: Python Scheduler (Recommended for simple setup)
Run the scheduler in the background:

```bash
nohup python scheduler.py > scheduler.out 2>&1 &
```

### Method B: Systemd Service (Linux Production)
1.  Create a service file: `/etc/systemd/system/topflix_crawler.service`
    ```ini
    [Unit]
    Description=TopFlix Daily Crawler
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/opt/topflix_crawler
    ExecStart=/usr/bin/python3 /opt/topflix_crawler/scheduler.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
2.  Enable and start:
    ```bash
    sudo systemctl enable topflix_crawler
    sudo systemctl start topflix_crawler
    ```

## 6. Docker Deployment (Alternative)
1.  **Build Image**:
    ```bash
    docker build -t topflix-crawler .
    ```
2.  **Run Container**:
    ```bash
    docker run -d --name topflix-crawler -v $(pwd)/exports:/app/exports -v $(pwd)/topflix.db:/app/topflix.db topflix-crawler
    ```

## 7. Data & Logs
- **Database**: `topflix.db` (SQLite) - Contains all crawled data.
- **Exports**: `exports/YYYY-MM-DD/` - Daily Excel/CSV dumps.
- **Logs**: 
    - `crawler.log`: Detailed crawler activity.
    - `scheduler.log`: Scheduler execution logs.

## 8. Maintenance
- Check `crawler.log` for errors.
- Regularly backup `topflix.db`.
- `exports/` folder can grow over time; consider setting up a cleanup script for old files.
