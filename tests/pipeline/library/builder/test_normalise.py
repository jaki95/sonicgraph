from sonicgraph.library.builder.helpers import (
    make_album_id,
    make_artist_id,
    make_track_id,
)


def test_artist_id_deterministic():
    a1 = make_artist_id("Chlär")
    a2 = make_artist_id("chlär")
    assert a1 == a2


def test_album_id_depends_on_artist():
    a1 = make_artist_id("Artist A")
    a2 = make_artist_id("Artist B")

    alb1 = make_album_id("Same Album", a1)
    alb2 = make_album_id("Same Album", a2)

    assert alb1 != alb2


def test_track_id_disambiguation():
    album_id = "album123"
    artist_id = "artist123"

    t1 = make_track_id("Intro", album_id, artist_id, "1")
    t2 = make_track_id("Intro", album_id, artist_id, "2")

    assert t1 != t2


def test_track_id_deterministic():
    t1 = make_track_id("Track", "album", "artist", "1")
    t2 = make_track_id("Track", "album", "artist", "1")
    assert t1 == t2
