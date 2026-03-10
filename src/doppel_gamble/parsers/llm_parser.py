import json
from datetime import datetime, timezone

from google import genai

from ..db.repository import Repository
from .prompts import HAND_PARSE_SYSTEM, HAND_PARSE_USER


class LLMParser:
    def __init__(self, db: Repository, api_key: str, model: str = "gemini-3-flash-preview"):
        self.db = db
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def parse_hand(self, raw_text: str) -> dict | None:
        """Parse a single hand description into structured JSON."""
        prompt = HAND_PARSE_SYSTEM + "\n\n" + HAND_PARSE_USER.format(raw_text=raw_text)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        content = response.text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    def parse_all_unparsed(self, player_id: int) -> int:
        """Parse all unparsed hand histories for a player. Returns count parsed."""
        hands = self.db.get_unparsed_hands(player_id)
        count = 0

        for hand in hands:
            parsed = self.parse_hand(hand.raw_text)
            if parsed:
                now = datetime.now(timezone.utc).isoformat()
                self.db.update_hand_parsed(hand.id, json.dumps(parsed), now)
                count += 1

        return count
