# Meta Search Spiders Collection

This repository contains a collection of web scrapers and spiders for various movie and TV show websites. These scripts are designed to fetch metadata, streaming links, and other related information.

## Projects

The following spider projects are included in this collection:

### 1919ys.com_zh
Spider for `1919ys.com` (Chinese).
- **Key Files**: `spider.py`, `main.py`, `incremental.py`
- **Docs**: `vs_movie_spider_research_report_v3_en.md`

### 97han.com
Comprehensive spider for `97han.com` with enhanced logging and optimization.
- **Key Files**: `optimized_crawler/main_crawler.py`, `spiders/enhanced_movie_spider.py`
- **Docs**: `97han_com_spider_technical_doc.md`, `README_ENHANCED.md`

### cuevana3
Scraper for `cuevana3` (Spanish/Latin).
- **Key Files**: `main.py`, `movie_scraper.py`, `tv_scraper.py`
- **Docs**: `README.md`, `BUGFIX_v1.3.md`

### filmpalast.to
Crawler for `filmpalast.to` (German).
- **Key Files**: `src/crawler.py`, `run_full_crawl.py`
- **Docs**: `filmpalast_crawler_technical_documentation.md`

### jzftdz.com
Spider for `jzftdz.com`.
- **Key Files**: `jzftdz_scraper/main.py`, `core/base_spider.py`
- **Docs**: `jzftdz_scraper_v3_final_doc.md`

### kcechiba.com
Spider for `kcechiba.com` (Chinese).
- **Key Files**: `main.py`, `spiders/movie_spider.py`
- **Docs**: `kcechiba_com_spider_technical_doc.md`

### lk21official
Scraper for `lk21official` (Indonesian).
- **Key Files**: `main.py`, `movie_scraper.py`
- **Docs**: `LK21_SCRAPER_TECHNICAL_GUIDE.md`

### movie.uishishuo11.com
Spider for `movie.uishishuo11.com` (Chinese).
- **Key Files**: `main.py`, `spiders/movie_spider.py`
- **Docs**: `shenma_midnight_movie_spider_technical_doc_final.md`

### pelicinehd
Scraper for `pelicinehd`.
- **Key Files**: `main.py`, `movie_scraper.py`
- **Docs**: `TECHNICAL_IMPLEMENTATION_GUIDE.md`, `pelicinehd_website_structure_analysis.md`

### repelishd
Scraper for `repelishd`.
- **Key Files**: `repelishd_scraper/main.py`, `repelishd_scraper/movie_scraper.py`
- **Docs**: `REPELISHD_SCRAPER_TECHNICAL_GUIDE.md`

### topflix.online
Crawler for `topflix.online`.
- **Key Files**: `spider_main.py`, `scheduler.py`
- **Docs**: `TopFlix_Crawler_Design.md`

### www.mjwu.cc
Spider for `www.mjwu.cc` (Chinese - Meijuwu).
- **Key Files**: `mjwu_spider/main.py`
- **Docs**: `mjwu_cc_spider_technical_doc.md`

### www.xz8.cc_zh
Spider for `www.xz8.cc`.
- **Key Files**: `xz8_spider.py`
- **Docs**: `xz8_spider_architecture_report.md`

### crawler_development_docs
General documentation and guides for crawler development.
- **Docs**: `crontab_setup_guide.md`, `quick_start_guide.md`, `cuevana3_movie_spider_usage.md`, `cuevana3_spider_system.md`

## Usage

Each project typically contains a `requirements.txt` file. You can install dependencies using:

```bash
pip install -r <project_dir>/requirements.txt
```

Most spiders can be started by running the `main.py` or specific startup scripts (e.g., `.bat` or `.sh` files) located in their respective directories.

## Disclaimer

This project is for educational and research purposes only. Please respect the `robots.txt` of the target websites and use responsibly.
