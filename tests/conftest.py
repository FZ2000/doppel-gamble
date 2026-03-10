from pathlib import Path

import pytest

from doppel_gamble.db.models import Player
from doppel_gamble.db.repository import Repository

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def db():
    repo = Repository(":memory:")
    yield repo
    repo.close()


@pytest.fixture
def player_id(db):
    player = Player(name="Phil Hellmuth", hendonmob_id="53")
    return db.upsert_player(player)


@pytest.fixture
def hendonmob_html():
    return (FIXTURES_DIR / "hendonmob_player_53.html").read_text()


@pytest.fixture
def pokernews_html():
    return (FIXTURES_DIR / "pokernews_hand_update.html").read_text()


@pytest.fixture
def youtube_vtt():
    return (FIXTURES_DIR / "youtube_transcript.vtt").read_text()
