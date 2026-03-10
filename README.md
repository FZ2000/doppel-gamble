# doppel-gamble

Poker player data extraction pipeline. Scrapes tournament histories, live reporting hand data, and YouTube transcripts to build structured hand history databases for poker AI research.

## Sources

- **Hendon Mob** — Tournament history (events, finishes, prizes)
- **PokerNews** — Live reporting hand-by-hand updates
- **YouTube** — Televised hand transcripts via yt-dlp

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

Set your API key for LLM parsing:
```bash
export ANTHROPIC_API_KEY=your_key
```

## Usage

Run the full pipeline:
```bash
doppel-gamble
```

Export data:
```bash
doppel-export
```

Run tests:
```bash
pytest
```

## Architecture

```
src/doppel_gamble/
├── config.py              # Settings and player profiles
├── db/                    # SQLite schema, models, repository
├── scrapers/
│   ├── base.py            # Playwright-based scraper with rate limiting
│   ├── hendonmob.py       # Tournament history scraper
│   ├── pokernews.py       # Live reporting scraper
│   └── youtube.py         # Transcript scraper (yt-dlp)
├── parsers/
│   ├── llm_parser.py      # Claude API for structured hand extraction
│   └── prompts.py         # Prompt templates
├── pipeline.py            # Orchestrator
└── export.py              # CSV/JSONL export
```
