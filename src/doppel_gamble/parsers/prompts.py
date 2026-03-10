HAND_PARSE_SYSTEM = """You are a poker hand history parser. Extract structured data from poker hand descriptions.
Output valid JSON only, no markdown or explanation."""

HAND_PARSE_USER = """Extract structured poker hand data from this text. Output a JSON object with these fields:
- hand_id: string or null
- players: list of {{name, position (if known), stack (if known), hole_cards (if shown)}}
- board: list of cards shown (e.g. ["Ks", "9h", "4d"]) or empty list
- actions: list of {{street, player, action, amount (if applicable)}}
  - street is one of: "preflop", "flop", "turn", "river"
  - action is one of: "fold", "check", "call", "bet", "raise", "all-in"
  - amount is an integer in chips/dollars, or null
- pot: total pot size (integer) or null
- winner: name of winner or null
- showdown: boolean

Text:
\"\"\"
{raw_text}
\"\"\"

Output JSON only:"""
