import csv
import io
import json
from pathlib import Path

from .db.repository import Repository


def export_tournaments_csv(db: Repository, player_id: int, output: Path | io.StringIO) -> int:
    """Export tournaments to CSV. Returns row count."""
    tournaments = db.get_tournaments(player_id)

    if isinstance(output, Path):
        f = open(output, "w", newline="", encoding="utf-8")
        should_close = True
    else:
        f = output
        should_close = False

    try:
        writer = csv.writer(f)
        writer.writerow(["event_name", "date", "buy_in", "prize", "finish_position", "source", "source_url"])
        for t in tournaments:
            writer.writerow([
                t.event_name, t.date, t.buy_in, t.prize,
                t.finish_position, t.source, t.source_url,
            ])
        return len(tournaments)
    finally:
        if should_close:
            f.close()


def export_hands_jsonl(db: Repository, player_id: int, output: Path | io.StringIO) -> int:
    """Export parsed hands to JSONL. Returns row count."""
    hands = db.get_hands(player_id)

    if isinstance(output, Path):
        f = open(output, "w", encoding="utf-8")
        should_close = True
    else:
        f = output
        should_close = False

    try:
        count = 0
        for h in hands:
            record = {
                "id": h.id,
                "source": h.source,
                "source_url": h.source_url,
                "raw_text": h.raw_text,
            }
            if h.parsed_json:
                try:
                    record["parsed"] = json.loads(h.parsed_json)
                except json.JSONDecodeError:
                    record["parsed"] = None
            f.write(json.dumps(record) + "\n")
            count += 1
        return count
    finally:
        if should_close:
            f.close()


def main():
    import sys
    from .config import Config

    config = Config()
    db = Repository(config.db_path)

    player = db.get_player(1)
    if not player:
        print("No player found. Run the pipeline first.")
        sys.exit(1)

    csv_path = config.data_dir / "tournaments.csv"
    jsonl_path = config.data_dir / "hands.jsonl"

    t_count = export_tournaments_csv(db, player.id, csv_path)
    h_count = export_hands_jsonl(db, player.id, jsonl_path)

    print(f"Exported {t_count} tournaments to {csv_path}")
    print(f"Exported {h_count} hands to {jsonl_path}")

    db.close()
