import json
from unittest.mock import MagicMock, patch

from doppel_gamble.db.models import HandHistory
from doppel_gamble.parsers.llm_parser import LLMParser


MOCK_RESPONSE_JSON = {
    "hand_id": "47",
    "players": [
        {"name": "Phil Hellmuth", "position": "CO"},
        {"name": "Daniel Negreanu", "position": "BB"},
    ],
    "board": ["Ks", "9h", "4d"],
    "actions": [
        {"street": "preflop", "player": "Phil Hellmuth", "action": "raise", "amount": 120000},
        {"street": "preflop", "player": "Daniel Negreanu", "action": "call", "amount": 120000},
        {"street": "flop", "player": "Daniel Negreanu", "action": "check"},
        {"street": "flop", "player": "Phil Hellmuth", "action": "bet", "amount": 150000},
        {"street": "flop", "player": "Daniel Negreanu", "action": "fold"},
    ],
    "pot": 390000,
    "winner": "Phil Hellmuth",
    "showdown": False,
}


def _make_mock_client(response_text: str):
    client = MagicMock()
    response = MagicMock()
    response.text = response_text
    client.models.generate_content.return_value = response
    return client


def test_parse_hand(db, player_id):
    parser = LLMParser(db, api_key="test-key")
    parser.client = _make_mock_client(json.dumps(MOCK_RESPONSE_JSON))

    result = parser.parse_hand("Hand #47: Phil Hellmuth raised to 120,000...")
    assert result is not None
    assert result["hand_id"] == "47"
    assert len(result["actions"]) == 5
    assert result["winner"] == "Phil Hellmuth"


def test_parse_hand_with_markdown_wrapper(db, player_id):
    wrapped = f"```json\n{json.dumps(MOCK_RESPONSE_JSON)}\n```"
    parser = LLMParser(db, api_key="test-key")
    parser.client = _make_mock_client(wrapped)

    result = parser.parse_hand("Hand #47: ...")
    assert result is not None
    assert result["hand_id"] == "47"


def test_parse_hand_invalid_json(db, player_id):
    parser = LLMParser(db, api_key="test-key")
    parser.client = _make_mock_client("this is not json at all")

    result = parser.parse_hand("some text")
    assert result is None


def test_parse_all_unparsed(db, player_id):
    db.insert_hand(HandHistory(
        player_id=player_id, source="pokernews",
        raw_text="Hand #47: Phil Hellmuth raised...",
    ))
    db.insert_hand(HandHistory(
        player_id=player_id, source="pokernews",
        raw_text="Hand #48: Already parsed",
        parsed_json='{"existing": true}', parsed_at="2024-01-01",
    ))

    parser = LLMParser(db, api_key="test-key")
    parser.client = _make_mock_client(json.dumps(MOCK_RESPONSE_JSON))

    count = parser.parse_all_unparsed(player_id)
    assert count == 1

    hands = db.get_unparsed_hands(player_id)
    assert len(hands) == 0
