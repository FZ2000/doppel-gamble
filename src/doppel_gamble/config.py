import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (walks up from config.py)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


@dataclass
class ScraperConfig:
    min_request_interval: float = 5.0
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    viewport: dict = field(default_factory=lambda: {"width": 1920, "height": 1080})
    headless: bool = True
    timeout_ms: int = 30000


@dataclass
class PlayerConfig:
    name: str
    hendonmob_id: str | None = None
    pokernews_slugs: list[str] = field(default_factory=list)
    youtube_search_terms: list[str] = field(default_factory=list)


PHIL_HELLMUTH = PlayerConfig(
    name="Phil Hellmuth",
    hendonmob_id="53",
    pokernews_slugs=["phil-hellmuth"],
    youtube_search_terms=[
        "Phil Hellmuth poker hand",
        "Phil Hellmuth WSOP",
        "Phil Hellmuth High Stakes Poker",
    ],
)


@dataclass
class Config:
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )
    data_dir: Path = field(default=None)
    raw_dir: Path = field(default=None)
    db_path: Path = field(default=None)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    gemini_api_key: str = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY", "")
    )
    anthropic_api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )
    player: PlayerConfig = field(default_factory=lambda: PHIL_HELLMUTH)

    def __post_init__(self):
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"
        if self.raw_dir is None:
            self.raw_dir = self.data_dir / "raw"
        if self.db_path is None:
            self.db_path = self.data_dir / "doppel_gamble.db"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
