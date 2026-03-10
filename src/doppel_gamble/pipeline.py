import asyncio
import sys

from playwright.async_api import async_playwright

from .config import Config
from .db.models import Player
from .db.repository import Repository
from .export import export_hands_jsonl, export_tournaments_csv
from .parsers.llm_parser import LLMParser
from .scrapers.hendonmob import HendonMobScraper
from .scrapers.pokernews import PokerNewsScraper
from .scrapers.youtube import YouTubeTranscriptScraper


async def run_pipeline(config: Config):
    db = Repository(config.db_path)

    player = Player(name=config.player.name, hendonmob_id=config.player.hendonmob_id)
    player_id = db.upsert_player(player)

    print(f"Pipeline started for {config.player.name} (player_id={player_id})")

    # --- Playwright scrapers ---
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.scraper.headless)
        context = await browser.new_context(
            user_agent=config.scraper.user_agent,
            viewport=config.scraper.viewport,
        )

        # 1. Hendon Mob
        print("Scraping Hendon Mob tournament history...")
        try:
            hmob = HendonMobScraper(context, db, config.scraper)
            tournaments = await hmob.scrape(player_id, hendonmob_id=config.player.hendonmob_id)
            print(f"  Found {len(tournaments)} tournaments")
        except Exception as e:
            print(f"  Hendon Mob scraper failed: {e}")

        # 2. PokerNews
        print("Scraping PokerNews live reporting...")
        try:
            pn = PokerNewsScraper(context, db, config.scraper)
            pn_entries = await pn.scrape(player_id, player_name=config.player.name)
            print(f"  Found {len(pn_entries)} hand entries")
        except Exception as e:
            print(f"  PokerNews scraper failed: {e}")

        await context.close()
        await browser.close()

    # 3. YouTube (no Playwright needed)
    print("Scraping YouTube transcripts...")
    try:
        yt = YouTubeTranscriptScraper(db)
        yt_entries = await yt.scrape(
            player_id,
            search_terms=config.player.youtube_search_terms,
            player_name=config.player.name,
        )
        print(f"  Found {len(yt_entries)} hand entries from YouTube")
    except Exception as e:
        print(f"  YouTube scraper failed: {e}")

    # 4. LLM parsing
    if config.gemini_api_key:
        print("Parsing hands with Gemini...")
        try:
            parser = LLMParser(db, config.gemini_api_key)
            parsed_count = parser.parse_all_unparsed(player_id)
            print(f"  Parsed {parsed_count} hands")
        except Exception as e:
            print(f"  LLM parser failed: {e}")
    else:
        print("Skipping LLM parsing (no GEMINI_API_KEY)")

    # 5. Export
    print("Exporting data...")
    csv_path = config.data_dir / "tournaments.csv"
    jsonl_path = config.data_dir / "hands.jsonl"
    t_count = export_tournaments_csv(db, player_id, csv_path)
    h_count = export_hands_jsonl(db, player_id, jsonl_path)
    print(f"  Exported {t_count} tournaments, {h_count} hands")

    # Summary
    print("\n--- Summary ---")
    print(f"Tournaments: {db.count_tournaments(player_id)}")
    print(f"Hands: {db.count_hands(player_id)}")
    print(f"Database: {config.db_path}")

    db.close()


def main():
    config = Config()
    asyncio.run(run_pipeline(config))


if __name__ == "__main__":
    main()
