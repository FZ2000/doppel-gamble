import asyncio
import json
import re
import tempfile
from pathlib import Path

from ..db.models import HandHistory
from ..db.repository import Repository


def parse_vtt(vtt_text: str) -> str:
    """Convert VTT subtitle format to plain text."""
    lines = []
    for line in vtt_text.splitlines():
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if re.match(r"\d{2}:\d{2}", line):
            continue
        if "-->" in line:
            continue
        cleaned = re.sub(r"<[^>]+>", "", line)
        if cleaned and cleaned not in lines[-1:]:
            lines.append(cleaned)
    return " ".join(lines)


def segment_transcript_into_hands(text: str) -> list[str]:
    """Split a poker transcript into individual hand segments."""
    pattern = re.compile(
        r"(?i)(?=(?:hand\s*(?:number|#|no\.?)\s*\d+|new hand|the dealer|blinds are now))"
    )
    parts = pattern.split(text)
    return [s.strip() for s in parts if s and len(s.strip()) > 50]


class YouTubeTranscriptScraper:
    def __init__(self, db: Repository):
        self.db = db

    async def search_videos(self, query: str, max_results: int = 10) -> list[str]:
        """Use yt-dlp to search YouTube and return video URLs."""
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--flat-playlist", "--dump-json",
            f"ytsearch{max_results}:{query}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        urls = []
        for line in stdout.decode().splitlines():
            try:
                data = json.loads(line)
                vid_id = data.get("id", data.get("url", ""))
                if vid_id:
                    urls.append(f"https://www.youtube.com/watch?v={vid_id}")
            except json.JSONDecodeError:
                continue
        return urls

    async def get_transcript(self, video_url: str) -> str | None:
        """Download auto-generated subtitles for a video."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = str(Path(tmpdir) / "%(id)s.%(ext)s")
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--write-auto-sub",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--skip-download",
                "-o", output_template,
                video_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            vtt_files = list(Path(tmpdir).glob("*.vtt"))
            if not vtt_files:
                return None

            vtt_text = vtt_files[0].read_text(encoding="utf-8", errors="replace")
            return parse_vtt(vtt_text)

    async def scrape(self, player_id: int, search_terms: list[str] | None = None,
                     player_name: str = "Phil Hellmuth", **kwargs) -> list[dict]:
        if not search_terms:
            search_terms = [f"{player_name} poker hand"]

        all_entries = []
        seen_urls = set()

        for term in search_terms:
            urls = await self.search_videos(term, max_results=5)

            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                transcript = await self.get_transcript(url)
                if not transcript:
                    continue

                self.db.store_raw_scrape(url=url, content=transcript, content_type="vtt")

                hands = segment_transcript_into_hands(transcript)
                for hand_text in hands:
                    if player_name.lower() not in hand_text.lower():
                        continue

                    hand = HandHistory(
                        player_id=player_id,
                        source="youtube",
                        source_url=url,
                        raw_text=hand_text,
                    )
                    self.db.insert_hand(hand)

                    all_entries.append({
                        "source_url": url,
                        "raw_text": hand_text,
                    })

        return all_entries
