from doppel_gamble.scrapers.youtube import parse_vtt, segment_transcript_into_hands


def test_parse_vtt(youtube_vtt):
    text = parse_vtt(youtube_vtt)
    assert "Phil Hellmuth" in text
    assert "pocket aces" in text
    # Should not contain VTT metadata
    assert "WEBVTT" not in text
    assert "-->" not in text
    assert "00:00" not in text


def test_parse_vtt_removes_html_tags():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:05.000
<c.colorCCCCCC>Hello</c> world

00:00:05.000 --> 00:00:10.000
<b>Bold text</b> here
"""
    text = parse_vtt(vtt)
    assert "<" not in text
    assert "Hello" in text
    assert "Bold text" in text


def test_segment_transcript_into_hands(youtube_vtt):
    text = parse_vtt(youtube_vtt)
    hands = segment_transcript_into_hands(text)
    assert len(hands) >= 1


def test_segment_empty_text():
    hands = segment_transcript_into_hands("")
    assert hands == []


def test_segment_short_segments_filtered():
    text = "Hand number 1. short. Hand number 2. also short."
    hands = segment_transcript_into_hands(text)
    # Both segments are under 50 chars, should be filtered
    assert len(hands) == 0


def test_segment_long_enough():
    text = (
        "Hand number 1. Phil Hellmuth raises to 3000 from the button. "
        "Tom Dwan calls from the big blind. The flop comes ace king queen. "
        "Hand number 2. Daniel Negreanu raises to 2500 from under the gun. "
        "Phil Hellmuth three bets to 8000 from the cutoff and everyone folds."
    )
    hands = segment_transcript_into_hands(text)
    assert len(hands) == 2
