from dataclasses import dataclass, field


@dataclass
class Player:
    name: str
    hendonmob_id: str | None = None
    id: int | None = None


@dataclass
class Tournament:
    player_id: int
    event_name: str
    source: str
    date: str | None = None
    buy_in: int | None = None
    prize: int | None = None
    finish_position: str | None = None
    source_url: str | None = None
    id: int | None = None


@dataclass
class HandHistory:
    player_id: int
    source: str
    raw_text: str
    tournament_id: int | None = None
    source_url: str | None = None
    parsed_json: str | None = None
    parsed_at: str | None = None
    id: int | None = None


@dataclass
class RawScrape:
    url: str
    content: str
    content_type: str = "html"
    id: int | None = None
