import asyncio
import time
from abc import ABC, abstractmethod

from playwright.async_api import BrowserContext

from ..config import ScraperConfig
from ..db.repository import Repository


class BaseScraper(ABC):
    def __init__(self, browser_context: BrowserContext, db: Repository, config: ScraperConfig):
        self.ctx = browser_context
        self.db = db
        self.config = config
        self._last_request_time = 0.0

    async def _get_page(self, url: str, wait_selector: str | None = None) -> str:
        await self._rate_limit()
        page = await self.ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=self.config.timeout_ms)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=self.config.timeout_ms)
            html = await page.content()
            self.db.store_raw_scrape(url=url, content=html)
            return html
        finally:
            await page.close()

    async def _rate_limit(self):
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.config.min_request_interval:
            await asyncio.sleep(self.config.min_request_interval - elapsed)
        self._last_request_time = time.monotonic()

    @abstractmethod
    async def scrape(self, player_id: int, **kwargs) -> list[dict]:
        ...
