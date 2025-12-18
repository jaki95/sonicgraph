from sonicgraph.pipeline.models import RawAMTrack
from sonicgraph.pipeline.normalise import (
    make_album_id,
    make_artist_id,
    make_track_id,
    normalise_tracks,
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


def make_track(**kwargs):
    defaults = dict(
        name="Track",
        artist="Artist",
        album="Album",
        album_artist=None,
        total_time=300000,
        track_number=1,
        track_count=10,
        release_date=None,
        date_added=None,
        genre="Techno",
        year=2024,
        compilation=False,
    )
    defaults.update(kwargs)
    return RawAMTrack(**defaults)


def test_album_artist_missing_does_not_crash():
    raw = [
        make_track(artist="Artist A"),
        make_track(artist="Artist A", track_number=2),
    ]

    artists, albums, tracks = normalise_tracks(raw)

    assert len(artists) == 1
    assert len(albums) == 1
    assert len(tracks) == 2


def test_multiple_artists_same_album_title():
    raw = [
        make_track(artist="Artist A"),
        make_track(artist="Artist B"),
    ]

    _, albums, _ = normalise_tracks(raw)

    # Expect album fragmentation (documented behavior)
    assert len(albums) == 2


def test_track_number_disambiguates():
    raw = [
        make_track(name="Intro", track_number=1),
        make_track(name="Intro", track_number=2),
    ]

    _, _, tracks = normalise_tracks(raw)
    assert len(tracks) == 2


def test_empty_artist_is_skipped():
    raw = [
        make_track(artist=""),
    ]

    artists, albums, tracks = normalise_tracks(raw)

    assert len(artists) == 0
    assert len(tracks) == 0
