import hashlib
import re
from datetime import date

from am import LIBRARY_PATH, extract_raw_tracks, load_apple_music_library
from models import Album, Artist, RawAMTrack, Track


def make_id(prefix: str, *values: str) -> str:
    raw = f"{prefix}:" + "|".join(v.lower().strip() for v in values if v)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def normalise_artist(name: str) -> list[str]:
    name = " ".join(name.split())

    if "&" in name:
        return [n.strip() for n in name.split("&")]
    if "," in name:
        return [n.strip() for n in name.split(",")]

    return [name]


SUFFIXES = [
    r"\s*\(.*remaster.*\)",
    r"\s*\(.*original mix.*\)",
    r"\s*\(.*extended.*\)",
]


def clean_title(title: str) -> str:
    t = title.lower()
    for s in SUFFIXES:
        t = re.sub(s, "", t)
    return t.strip().title()


def normalise_tracks(raw_tracks: list[RawAMTrack]):
    artists = {}
    albums = {}
    tracks = {}

    for rt in raw_tracks:
        artist_names = normalise_artist(rt.artist)
        artist_ids = []

        for name in artist_names:
            aid = make_id("artist", name)
            artists.setdefault(aid, Artist(id=aid, name=name))
            artist_ids.append(aid)

        album_id: str | None = None
        if rt.album:
            album_title = clean_title(rt.album)
            if rt.album_artist:
                album_artist_ids = []
                album_artist_names = normalise_artist(rt.album_artist)
                for name in album_artist_names:
                    aid = make_id("artist", name)
                    artists.setdefault(aid, Artist(id=aid, name=name))
                    album_artist_ids.append(aid)

            album_id = make_id(
                "album",
                album_title,
                album_artist_ids[0] if len(album_artist_ids) > 0 else artist_ids[0],
            )
            albums.setdefault(
                album_id,
                Album(
                    id=album_id,
                    title=album_title,
                    artist_ids=album_artist_ids,
                    year=rt.year,
                ),
            )

        track_title = clean_title(rt.name)
        track_id = make_id("track", track_title, album_id or "")

        if rt.date_added:
            date_added = rt.date_added.date()
        if rt.release_date:
            release_date = rt.release_date.date()

        tracks.setdefault(
            track_id,
            Track(
                id=track_id,
                title=track_title,
                artist_ids=artist_ids,
                album_artist_ids=album_artist_ids,
                album_id=album_id,
                duration=rt.total_time,
                track_number=rt.track_number,
                track_count=rt.track_count,
                release_date=release_date,
                date_added=date_added,
                bpm=rt.bit_rate,
                genre=rt.genre,
                year=rt.year,
                compilation=rt.compilation,
            ),
        )

    return artists, albums, tracks


if __name__ == "__main__":
    lib = load_apple_music_library(LIBRARY_PATH)
    raw_tracks = extract_raw_tracks(lib)
    artists, albums, tracks = normalise_tracks(raw_tracks)
    print(len(artists), len(albums), len(tracks))
    first_album = list(albums.values())[0]
    print(f"First album: {first_album}")
    print(f"Album artist: {artists.get(first_album.artist_ids[0])}")
    print(f"First track: {list(tracks.values())[0]}")
