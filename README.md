# NTHU-Data-Scraper
<p align="center">
    <em>NTHU-Data-Scraper is a project designed for NTHU developers.</em>
    <br>
    <em>We scrape data from NTHU official website with GitHub Action and deliver it with our website.</em>
</p>
<p align="center">
<a href="https://github.com/psf/black" target="_blank">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
</a>
<a href="https://github.com/NTHU-SA/NTHU-Data-Scraper/actions/workflows/update_data.yml" target="_blank">
    <img src="https://github.com/NTHU-SA/NTHU-Data-Scraper/actions/workflows/update_data.yml/badge.svg" alt="Crawl and update data">
<br>
<a href="https://sonarcloud.io/summary/new_code?id=NTHU-SA_NTHU-Data-Scraper" target="_blank">
    <img src="https://sonarcloud.io/api/project_badges/measure?project=NTHU-SA_NTHU-Data-Scraper&metric=sqale_rating" alt="
Maintainability Rating">
</a>
<a href="https://sonarcloud.io/summary/new_code?id=NTHU-SA_NTHU-Data-Scraper" target="_blank">
    <img src="https://sonarcloud.io/api/project_badges/measure?project=NTHU-SA_NTHU-Data-Scraper&metric=ncloc" alt="Lines of Code">
</a>
<a href="https://sonarcloud.io/summary/new_code?id=NTHU-SA_NTHU-Data-Scraper" target="_blank">
    <img src="https://sonarcloud.io/api/project_badges/measure?project=NTHU-SA_NTHU-Data-Scraper&metric=sqale_index" alt="Technical Debt">
</a>
</p>

## Features

### Intelligent Announcement Crawling
- **Incremental Crawling**: Fast, efficient crawling of known announcement URLs (runs every 2 hours)
- **Full Site Crawling**: Comprehensive crawling to discover new announcement pages (manual trigger)
- **URL Management**: Automatic tracking and cleanup of announcement URLs
- **Failure Handling**: Smart retry logic for temporarily unavailable pages

### Data Sources
- Course information
- Campus announcements (including bus announcements)
- Dining hall information
- Department directory
- Campus maps
- Newsletters
- Bus schedules (main campus and Nanda shuttle)

## Usage

### Local Development
Use the `crawl.sh` script for local testing:

```bash
# Run all spiders with incremental crawl
./crawl.sh --group all

# Run ubuntu spiders with full crawl
./crawl.sh --group ubuntu --crawl-type full

# Run specific spider
./crawl.sh nthu_announcements --crawl-type incremental
```

### GitHub Actions
The workflow runs automatically:
- **Push to main**: Triggers incremental crawl on ubuntu runners
- **Scheduled**: Every 2 hours, incremental crawl on ubuntu runners
- **Manual**: Use workflow_dispatch to trigger either incremental or full crawl

Self-hosted runners are now **manual trigger only** to save resources.

## Credit
This project is maintained by NTHUSA 32nd.

## License
This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

## Acknowledgements
Thanks to SonarCloud for providing code quality metrics:

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/summary/new_code?id=NTHU-SA_NTHU-Data-API)