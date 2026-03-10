import sqlite3
from pathlib import Path

from .models import HandHistory, Player, RawScrape, Tournament

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Repository:
    def __init__(self, db_path: str | Path = ":memory:"):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        schema = SCHEMA_PATH.read_text()
        self.conn.executescript(schema)

    def close(self):
        self.conn.close()

    # --- Players ---

    def upsert_player(self, player: Player) -> int:
        cur = self.conn.execute(
            "INSERT INTO players (name, hendonmob_id) VALUES (?, ?) "
            "ON CONFLICT(hendonmob_id) DO UPDATE SET name=excluded.name "
            "RETURNING id",
            (player.name, player.hendonmob_id),
        )
        row = cur.fetchone()
        self.conn.commit()
        return row["id"]

    def get_player(self, player_id: int) -> Player | None:
        cur = self.conn.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return Player(id=row["id"], name=row["name"], hendonmob_id=row["hendonmob_id"])

    # --- Tournaments ---

    def insert_tournament(self, t: Tournament) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO tournaments "
            "(player_id, event_name, date, buy_in, prize, finish_position, source, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ",
            (t.player_id, t.event_name, t.date, t.buy_in, t.prize,
             t.finish_position, t.source, t.source_url),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_tournaments(self, player_id: int) -> list[Tournament]:
        cur = self.conn.execute(
            "SELECT * FROM tournaments WHERE player_id = ? ORDER BY date DESC",
            (player_id,),
        )
        return [
            Tournament(
                id=r["id"], player_id=r["player_id"], event_name=r["event_name"],
                date=r["date"], buy_in=r["buy_in"], prize=r["prize"],
                finish_position=r["finish_position"], source=r["source"],
                source_url=r["source_url"],
            )
            for r in cur.fetchall()
        ]

    # --- Hand Histories ---

    def insert_hand(self, h: HandHistory) -> int:
        cur = self.conn.execute(
            "INSERT INTO hand_histories "
            "(player_id, tournament_id, source, source_url, raw_text, parsed_json, parsed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (h.player_id, h.tournament_id, h.source, h.source_url,
             h.raw_text, h.parsed_json, h.parsed_at),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_hands(self, player_id: int, source: str | None = None) -> list[HandHistory]:
        if source:
            cur = self.conn.execute(
                "SELECT * FROM hand_histories WHERE player_id = ? AND source = ?",
                (player_id, source),
            )
        else:
            cur = self.conn.execute(
                "SELECT * FROM hand_histories WHERE player_id = ?", (player_id,),
            )
        return [
            HandHistory(
                id=r["id"], player_id=r["player_id"], tournament_id=r["tournament_id"],
                source=r["source"], source_url=r["source_url"], raw_text=r["raw_text"],
                parsed_json=r["parsed_json"], parsed_at=r["parsed_at"],
            )
            for r in cur.fetchall()
        ]

    def get_unparsed_hands(self, player_id: int) -> list[HandHistory]:
        cur = self.conn.execute(
            "SELECT * FROM hand_histories WHERE player_id = ? AND parsed_json IS NULL",
            (player_id,),
        )
        return [
            HandHistory(
                id=r["id"], player_id=r["player_id"], tournament_id=r["tournament_id"],
                source=r["source"], source_url=r["source_url"], raw_text=r["raw_text"],
                parsed_json=r["parsed_json"], parsed_at=r["parsed_at"],
            )
            for r in cur.fetchall()
        ]

    def update_hand_parsed(self, hand_id: int, parsed_json: str, parsed_at: str):
        self.conn.execute(
            "UPDATE hand_histories SET parsed_json = ?, parsed_at = ? WHERE id = ?",
            (parsed_json, parsed_at, hand_id),
        )
        self.conn.commit()

    # --- Raw Scrapes ---

    def store_raw_scrape(self, url: str, content: str, content_type: str = "html") -> int:
        cur = self.conn.execute(
            "INSERT INTO raw_scrapes (url, content, content_type) VALUES (?, ?, ?)",
            (url, content, content_type),
        )
        self.conn.commit()
        return cur.lastrowid

    # --- Stats ---

    def count_tournaments(self, player_id: int) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM tournaments WHERE player_id = ?", (player_id,),
        )
        return cur.fetchone()["cnt"]

    def count_hands(self, player_id: int) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM hand_histories WHERE player_id = ?", (player_id,),
        )
        return cur.fetchone()["cnt"]
