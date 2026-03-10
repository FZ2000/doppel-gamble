import csv
import io
import json

from doppel_gamble.db.models import HandHistory, Tournament
from doppel_gamble.export import export_hands_jsonl, export_tournaments_csv


def test_export_tournaments_csv(db, player_id):
    db.insert_tournament(Tournament(
        player_id=player_id,
        event_name="2023 WSOP Main Event",
        date="2023-07-10",
        buy_in=1000000,
        prize=60000000,
        finish_position="15th",
        source="hendonmob",
        source_url="https://example.com",
    ))

    output = io.StringIO()
    count = export_tournaments_csv(db, player_id, output)
    assert count == 1

    output.seek(0)
    reader = csv.DictReader(output)
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["event_name"] == "2023 WSOP Main Event"
    assert rows[0]["finish_position"] == "15th"


def test_export_hands_jsonl(db, player_id):
    db.insert_hand(HandHistory(
        player_id=player_id,
        source="pokernews",
        raw_text="Hand #47 text",
        parsed_json='{"hand_id": "47"}',
    ))
    db.insert_hand(HandHistory(
        player_id=player_id,
        source="youtube",
        raw_text="YouTube hand text",
    ))

    output = io.StringIO()
    count = export_hands_jsonl(db, player_id, output)
    assert count == 2

    output.seek(0)
    lines = output.getvalue().strip().split("\n")
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["source"] == "pokernews"
    assert first["parsed"]["hand_id"] == "47"

    second = json.loads(lines[1])
    assert second["source"] == "youtube"
    assert "parsed" not in second


def test_export_empty(db, player_id):
    output = io.StringIO()
    assert export_tournaments_csv(db, player_id, output) == 0

    output = io.StringIO()
    assert export_hands_jsonl(db, player_id, output) == 0
