from doppel_gamble.scrapers.pokernews import extract_hand_entries


def test_extract_hand_entries_finds_hellmuth(pokernews_html):
    entries = extract_hand_entries(pokernews_html, "Phil Hellmuth")
    # Should find entries mentioning Phil Hellmuth (hands #47, #49, and chip count)
    assert len(entries) >= 2

    hand_ids = [e["hand_id"] for e in entries if e["hand_id"]]
    assert "47" in hand_ids
    assert "49" in hand_ids


def test_extract_entries_filters_by_player(pokernews_html):
    # Mike Matusow is only in hand #48 (no Hellmuth)
    hellmuth_entries = extract_hand_entries(pokernews_html, "Phil Hellmuth")
    matusow_entries = extract_hand_entries(pokernews_html, "Mike Matusow")

    hellmuth_texts = [e["raw_text"] for e in hellmuth_entries]
    matusow_texts = [e["raw_text"] for e in matusow_entries]

    # Hellmuth should not have hand #48
    assert not any("Hand #48" in t for t in hellmuth_texts)
    # Matusow should have hand #48
    assert any("Hand #48" in t for t in matusow_texts)


def test_extract_no_matches(pokernews_html):
    entries = extract_hand_entries(pokernews_html, "Nobody Here")
    assert len(entries) == 0


def test_extract_case_insensitive(pokernews_html):
    entries = extract_hand_entries(pokernews_html, "phil hellmuth")
    assert len(entries) >= 2


def test_entry_contains_raw_text(pokernews_html):
    entries = extract_hand_entries(pokernews_html, "Phil Hellmuth")
    for entry in entries:
        assert len(entry["raw_text"]) > 0
        assert "html" in entry
