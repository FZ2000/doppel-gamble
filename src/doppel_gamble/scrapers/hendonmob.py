import re

from bs4 import BeautifulSoup

from ..db.models import Tournament
from ..db.repository import Repository
from .base import BaseScraper


def parse_money(text: str) -> int | None:
    """Parse currency string like '$1,234' into cents."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    if not cleaned:
        return None
    try:
        return int(float(cleaned) * 100)
    except ValueError:
        return None


def parse_tournaments_html(html: str) -> list[dict]:
    """Extract tournament rows from Hendon Mob player page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    table = soup.find("table", class_="table")
    if table is None:
        tables = soup.find_all("table")
        for t in tables:
            headers = [th.get_text(strip=True).lower() for th in t.find_all("th")]
            if any("event" in h for h in headers) or any("tournament" in h for h in headers):
                table = t
                break

    if table is None:
        return results

    # Parse headers to map columns by name
    header_row = table.find("tr")
    headers = [th.get_text(strip=True).lower() for th in header_row.find_all("th")]

    col_map = {}
    for i, h in enumerate(headers):
        if "date" in h:
            col_map["date"] = i
        elif "event" in h or "tournament" in h:
            col_map["event"] = i
        elif "buy" in h:
            col_map["buy_in"] = i
        elif "finish" in h or "position" in h or "place" in h:
            col_map["finish"] = i
        elif "prize" in h or "win" in h:
            col_map["prize"] = i

    rows = table.find_all("tr")[1:]  # skip header
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        texts = [c.get_text(strip=True) for c in cells]

        link = row.find("a")
        source_url = None
        if link and link.get("href"):
            href = link["href"]
            if not href.startswith("http"):
                href = "https://pokerdb.thehendonmob.com" + href
            source_url = href

        event_name = texts[col_map["event"]] if "event" in col_map else texts[0]
        date = texts[col_map["date"]] if "date" in col_map else None
        buy_in = parse_money(texts[col_map["buy_in"]]) if "buy_in" in col_map else None
        prize = parse_money(texts[col_map["prize"]]) if "prize" in col_map else None
        finish_position = texts[col_map["finish"]] if "finish" in col_map else None

        results.append({
            "event_name": event_name,
            "date": date,
            "buy_in": buy_in,
            "prize": prize,
            "finish_position": finish_position,
            "source_url": source_url,
        })

    return results


class HendonMobScraper(BaseScraper):
    BASE_URL = "https://pokerdb.thehendonmob.com"

    async def _get_page_with_cf_wait(self, url: str) -> str:
        """Navigate to page and wait for Cloudflare challenge to resolve."""
        await self._rate_limit()
        page = await self.ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for Cloudflare challenge to resolve (up to 30s)
            for _ in range(15):
                title = await page.title()
                if "just a moment" not in title.lower():
                    break
                await page.wait_for_timeout(2000)

            # Wait for table to appear
            try:
                await page.wait_for_selector("table", timeout=15000)
            except Exception:
                pass

            html = await page.content()
            self.db.store_raw_scrape(url=url, content=html)
            return html
        finally:
            await page.close()

    async def scrape(self, player_id: int, hendonmob_id: str = "53", **kwargs) -> list[dict]:
        url = f"{self.BASE_URL}/player.php?a=r&n={hendonmob_id}"
        html = await self._get_page_with_cf_wait(url)

        tournaments = parse_tournaments_html(html)

        for t_data in tournaments:
            tournament = Tournament(
                player_id=player_id,
                event_name=t_data["event_name"],
                date=t_data.get("date"),
                buy_in=t_data.get("buy_in"),
                prize=t_data.get("prize"),
                finish_position=t_data.get("finish_position"),
                source="hendonmob",
                source_url=t_data.get("source_url"),
            )
            self.db.insert_tournament(tournament)

        return tournaments
