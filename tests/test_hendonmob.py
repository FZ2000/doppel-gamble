from doppel_gamble.scrapers.hendonmob import parse_money, parse_tournaments_html


def test_parse_money():
    assert parse_money("$10,000") == 1000000
    assert parse_money("$250,000") == 25000000
    assert parse_money("$1,500,000") == 150000000
    assert parse_money("") is None
    assert parse_money(None) is None
    assert parse_money("€5,300") == 530000


def test_parse_tournaments_html(hendonmob_html):
    results = parse_tournaments_html(hendonmob_html)
    assert len(results) == 3

    first = results[0]
    assert "WSOP Event #1" in first["event_name"]
    assert first["date"] == "2023-06-15"
    assert first["finish_position"] == "3rd"
    assert first["source_url"] is not None
    assert "12345" in first["source_url"]


def test_parse_tournaments_buy_in_and_prize(hendonmob_html):
    results = parse_tournaments_html(hendonmob_html)
    # First tournament: $10,000 buy-in, $250,000 prize
    first = results[0]
    assert first["buy_in"] == 1000000
    assert first["prize"] == 25000000


def test_parse_empty_html():
    results = parse_tournaments_html("<html><body>No table here</body></html>")
    assert results == []


def test_parse_table_without_class():
    html = """
    <html><body>
    <table>
    <tr><th>Date</th><th>Event</th><th>Buy-in</th><th>Finish</th></tr>
    <tr><td>2023-01-01</td><td>Test Event</td><td>$1,000</td><td>5th</td></tr>
    </table>
    </body></html>
    """
    results = parse_tournaments_html(html)
    assert len(results) == 1
    assert results[0]["event_name"] == "Test Event"
