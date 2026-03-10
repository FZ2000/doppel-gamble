import re

from bs4 import BeautifulSoup

from ..db.models import HandHistory
from ..db.repository import Repository
from .base import BaseScraper


def extract_hand_entries(html: str, player_name: str) -> list[dict]:
    """Extract blog entries mentioning a player from PokerNews live reporting HTML."""
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    # Try structured update divs first (live reporting pages)
    updates = soup.find_all("div", class_=re.compile(r"(blog-update|live-update|update-block)"))
    if not updates:
        updates = soup.find_all("div", class_=re.compile(r"(entry|post)"))
    if not updates:
        updates = soup.find_all("article")

    if updates:
        for update in updates:
            text = update.get_text(strip=True)
            if player_name.lower() not in text.lower():
                continue

            hand_match = re.search(r"Hand\s*#?(\d+)", text, re.IGNORECASE)
            hand_id = hand_match.group(1) if hand_match else None

            entries.append({
                "hand_id": hand_id,
                "raw_text": text,
                "html": str(update),
            })
    else:
        # Fall back to paragraph extraction (news articles)
        paragraphs = soup.find_all("p")
        hand_paragraphs = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 50:
                continue
            if player_name.split()[-1].lower() in text.lower():
                hand_paragraphs.append(text)

        if hand_paragraphs:
            # Group consecutive paragraphs into hand entries
            full_text = "\n".join(hand_paragraphs)
            entries.append({
                "hand_id": None,
                "raw_text": full_text,
                "html": "",
            })

    return entries


class PokerNewsScraper(BaseScraper):
    BASE_URL = "https://www.pokernews.com"

    async def scrape(self, player_id: int, event_urls: list[str] | None = None,
                     player_name: str = "Phil Hellmuth", **kwargs) -> list[dict]:
        if not event_urls:
            event_urls = await self._discover_articles(player_name)

        all_entries = []
        for url in event_urls:
            html = await self._get_page(url)
            entries = extract_hand_entries(html, player_name)

            for entry in entries:
                hand = HandHistory(
                    player_id=player_id,
                    source="pokernews",
                    source_url=url,
                    raw_text=entry["raw_text"],
                )
                self.db.insert_hand(hand)

            all_entries.extend(entries)

        return all_entries

    async def _discover_articles(self, player_name: str) -> list[str]:
        """Search PokerNews for articles with hand descriptions."""
        slug = player_name.lower().replace(" ", "+")
        search_url = f"{self.BASE_URL}/search/?q={slug}+WSOP+hand"
        html = await self._get_page(search_url)
        soup = BeautifulSoup(html, "html.parser")

        urls = []
        seen = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True).lower()
            last_name = player_name.split()[-1].lower()

            if last_name not in text:
                continue
            if "/news/" not in href and "/live-reporting/" not in href:
                continue

            full_url = href if href.startswith("http") else self.BASE_URL + href
            if full_url not in seen:
                seen.add(full_url)
                urls.append(full_url)

        return urls[:15]
