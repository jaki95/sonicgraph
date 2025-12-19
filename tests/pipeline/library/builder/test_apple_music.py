from sonicgraph.library.builder.apple_music import AppleMusicLibraryBuilder
from sonicgraph.library.models import RawTrack


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
    return RawTrack(**defaults)


def test_album_artist_missing_does_not_crash():
    raw = [
        make_track(artist="Artist A"),
        make_track(artist="Artist A", track_number=2),
    ]

    builder = AppleMusicLibraryBuilder()

    library = builder.build(raw)

    assert len(library.artists) == 1
    assert len(library.albums) == 1
    assert len(library.tracks) == 2


def test_multiple_artists_same_album_title():
    raw = [
        make_track(artist="Artist A"),
        make_track(artist="Artist B"),
    ]

    builder = AppleMusicLibraryBuilder()

    library = builder.build(raw)

    # Expect album fragmentation (documented behavior)
    assert len(library.albums) == 2


def test_track_number_disambiguates():
    raw = [
        make_track(name="Intro", track_number=1),
        make_track(name="Intro", track_number=2),
    ]

    builder = AppleMusicLibraryBuilder()

    library = builder.build(raw)

    assert len(library.tracks) == 2


def test_empty_artist_is_skipped():
    raw = [
        make_track(artist=""),
    ]

    builder = AppleMusicLibraryBuilder()

    library = builder.build(raw)

    assert len(library.artists) == 0
    assert len(library.tracks) == 0
