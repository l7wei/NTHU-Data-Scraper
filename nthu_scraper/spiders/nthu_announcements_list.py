"""清華大學公告爬蟲 - 公告列表爬蟲"""

import re
from typing import Dict, List

import scrapy

from nthu_scraper.utils.constants import (
    ANNOUNCEMENTS_LIST_PATH,
    DIRECTORY_PATH,
    LANGUAGES,
    RPAGE_DOMAIN_SUFFIX,
)
from nthu_scraper.utils.file_utils import load_json, save_json
from nthu_scraper.utils.url_utils import (
    build_multi_lang_urls,
    check_domain_suffix,
    update_url_query_param,
)

# 其他公告來源
OTHER_SOURCES = {
    "清華公佈欄": {
        "zh-tw": "https://bulletin.site.nthu.edu.tw/?Lang=zh-tw",
        "en": "https://bulletin.site.nthu.edu.tw/?Lang=en",
    },
    "國立清華大學學生會": {
        "zh-tw": "https://nthusa.site.nthu.edu.tw/?Lang=zh-tw",
    },
}


class AnnouncementListItem(scrapy.Item):
    """公告列表 Item"""

    title = scrapy.Field()
    link = scrapy.Field()
    language = scrapy.Field()
    department = scrapy.Field()


class AnnouncementsListSpider(scrapy.Spider):
    """
    公告列表爬蟲

    負責遞迴爬取公告列表頁面，建立並更新 announcements_list.json
    """

    name = "nthu_announcements_list"
    custom_settings = {
        "ITEM_PIPELINES": {
            "nthu_scraper.spiders.nthu_announcements_list.AnnouncementListPipeline": 1,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department_urls = self._load_department_urls()
        self.existing_links = self._load_existing_links()

    def _load_department_urls(self) -> Dict[str, Dict[str, str]]:
        """從通訊錄載入單位 URL"""
        urls = {}
        directory = load_json(DIRECTORY_PATH)

        if directory:
            for dept in directory:
                try:
                    dept_name = dept["name"]
                    website = dept["details"]["contact"]["website"]
                    lang_urls = build_multi_lang_urls(website, LANGUAGES)
                    if lang_urls and check_domain_suffix(website, RPAGE_DOMAIN_SUFFIX):
                        urls[dept_name] = lang_urls
                except KeyError:
                    continue

        # 添加其他來源
        urls.update(OTHER_SOURCES)
        return urls

    def _load_existing_links(self) -> set:
        """載入現有的公告列表連結"""
        existing_data = load_json(ANNOUNCEMENTS_LIST_PATH)
        if existing_data:
            return {item["link"] for item in existing_data}
        return set()

    async def start(self):
        """發送初始請求"""
        for dept, lang_urls in self.department_urls.items():
            for lang, url in lang_urls.items():
                yield scrapy.Request(
                    url,
                    callback=self.parse,
                    meta={"department": dept, "language": lang, "base_url": url},
                )

    def parse(self, response):
        """解析主頁面"""
        # 解析 tab content 中的動態載入連結
        yield from self._parse_tab_content(response)

        # 解析 "more" 連結
        yield from self._parse_more_links(response)

    def _parse_tab_content(self, response):
        """解析 tab content 中的公告連結"""
        tab_panes = response.css("div.tab-pane")
        for tab in tab_panes:
            tab_text = tab.xpath("string(.)").get()
            match = re.search(r'\$\.\s*hajaxOpenUrl\(\s*["\']([^"\']+)', tab_text)
            if match:
                url = response.urljoin(match.group(1))
                url = update_url_query_param(url, "Lang", response.meta.get("language"))
                yield scrapy.Request(
                    url,
                    callback=self.parse,
                    meta=response.meta,
                )

    def _parse_more_links(self, response):
        """解析 more 連結"""
        more_links = response.css("p.more a::attr(href)").getall()
        for link in more_links:
            abs_url = response.urljoin(link)
            abs_url = update_url_query_param(
                abs_url, "Lang", response.meta.get("language")
            )

            if not check_domain_suffix(abs_url, RPAGE_DOMAIN_SUFFIX):
                continue

            # 檢查是否為新連結
            if abs_url not in self.existing_links:
                self.logger.info(f"發現新公告列表: {abs_url}")

            yield scrapy.Request(
                abs_url,
                callback=self.parse_announcement_list,
                meta=response.meta.copy(),
            )

    def parse_announcement_list(self, response):
        """解析公告列表頁面"""
        # 提取標題
        title = response.css("[class*='title']::text").get()
        if not title or not title.strip():
            title = response.css("title::text").get()
        if title:
            title = title.strip()

        # 檢查是否有公告內容
        has_content = bool(response.css("#pageptlist .row.listBS, #pageptlist tr"))

        if not has_content:
            self.logger.warning(f"公告列表頁面無內容: {response.url}")
            return

        yield AnnouncementListItem(
            title=title,
            link=response.url,
            language=response.meta.get("language"),
            department=response.meta.get("department"),
        )


class AnnouncementListPipeline:
    """公告列表 Pipeline"""

    def open_spider(self, spider):
        """初始化"""
        self.collected_items = []
        self.existing_data = load_json(ANNOUNCEMENTS_LIST_PATH) or []
        self.existing_links = {item["link"] for item in self.existing_data}

    def process_item(self, item, spider):
        """處理 Item"""
        if not isinstance(item, AnnouncementListItem):
            return item

        link = item["link"]

        # 只添加新連結
        if link not in self.existing_links:
            self.collected_items.append(dict(item))
            self.existing_links.add(link)
            spider.logger.info(f"新增公告列表: {item['department']}/{item['title']}")

        return item

    def close_spider(self, spider):
        """儲存資料"""
        # 合併新舊資料
        all_items = self.existing_data + self.collected_items

        # 檢查並移除空連結（可選：驗證連結是否仍然有效）
        # 這裡先保留所有連結，實際驗證需要額外的請求

        # 按連結排序
        all_items.sort(key=lambda x: x["link"])

        save_json(all_items, ANNOUNCEMENTS_LIST_PATH)
        spider.logger.info(
            f"儲存公告列表: 共 {len(all_items)} 筆 (新增 {len(self.collected_items)} 筆)"
        )
