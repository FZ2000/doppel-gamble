from doppel_gamble.db.models import HandHistory, Player, Tournament


def test_upsert_and_get_player(db):
    player = Player(name="Phil Hellmuth", hendonmob_id="53")
    pid = db.upsert_player(player)
    assert pid > 0

    fetched = db.get_player(pid)
    assert fetched.name == "Phil Hellmuth"
    assert fetched.hendonmob_id == "53"


def test_upsert_player_updates_name(db):
    p1 = Player(name="Phil Hellmuth", hendonmob_id="53")
    id1 = db.upsert_player(p1)

    p2 = Player(name="Phil Hellmuth Jr", hendonmob_id="53")
    id2 = db.upsert_player(p2)

    assert id1 == id2
    fetched = db.get_player(id1)
    assert fetched.name == "Phil Hellmuth Jr"


def test_insert_and_get_tournaments(db, player_id):
    t = Tournament(
        player_id=player_id,
        event_name="2023 WSOP Main Event",
        date="2023-07-10",
        buy_in=1000000,
        prize=60000000,
        finish_position="15th",
        source="hendonmob",
    )
    tid = db.insert_tournament(t)
    assert tid > 0

    tournaments = db.get_tournaments(player_id)
    assert len(tournaments) == 1
    assert tournaments[0].event_name == "2023 WSOP Main Event"


def test_duplicate_tournament_ignored(db, player_id):
    t = Tournament(
        player_id=player_id,
        event_name="2023 WSOP Event #1",
        date="2023-06-15",
        source="hendonmob",
    )
    db.insert_tournament(t)
    db.insert_tournament(t)  # duplicate

    assert db.count_tournaments(player_id) == 1


def test_insert_and_get_hands(db, player_id):
    h = HandHistory(
        player_id=player_id,
        source="pokernews",
        raw_text="Hand #47: Phil Hellmuth raised to 120,000",
    )
    hid = db.insert_hand(h)
    assert hid > 0

    hands = db.get_hands(player_id)
    assert len(hands) == 1
    assert "Phil Hellmuth" in hands[0].raw_text


def test_get_hands_by_source(db, player_id):
    db.insert_hand(HandHistory(player_id=player_id, source="pokernews", raw_text="pn hand"))
    db.insert_hand(HandHistory(player_id=player_id, source="youtube", raw_text="yt hand"))

    pn = db.get_hands(player_id, source="pokernews")
    yt = db.get_hands(player_id, source="youtube")
    assert len(pn) == 1
    assert len(yt) == 1


def test_unparsed_hands(db, player_id):
    db.insert_hand(HandHistory(player_id=player_id, source="pokernews", raw_text="text1"))
    db.insert_hand(HandHistory(
        player_id=player_id, source="pokernews", raw_text="text2",
        parsed_json='{"test": true}', parsed_at="2024-01-01",
    ))

    unparsed = db.get_unparsed_hands(player_id)
    assert len(unparsed) == 1
    assert unparsed[0].raw_text == "text1"


def test_update_hand_parsed(db, player_id):
    hid = db.insert_hand(HandHistory(player_id=player_id, source="pokernews", raw_text="text"))
    db.update_hand_parsed(hid, '{"parsed": true}', "2024-01-01T00:00:00")

    hands = db.get_hands(player_id)
    assert hands[0].parsed_json == '{"parsed": true}'


def test_store_raw_scrape(db):
    sid = db.store_raw_scrape("https://example.com", "<html>test</html>")
    assert sid > 0


def test_count_functions(db, player_id):
    assert db.count_tournaments(player_id) == 0
    assert db.count_hands(player_id) == 0

    db.insert_tournament(Tournament(
        player_id=player_id, event_name="Test", source="test",
    ))
    db.insert_hand(HandHistory(
        player_id=player_id, source="test", raw_text="test",
    ))

    assert db.count_tournaments(player_id) == 1
    assert db.count_hands(player_id) == 1
