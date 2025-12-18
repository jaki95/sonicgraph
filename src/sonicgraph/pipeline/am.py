import plistlib
from pathlib import Path

from sonicgraph.pipeline.models import RawAMTrack

LIBRARY_PATH = Path("data/am_library.xml")


def load_apple_music_library(path: Path) -> dict:
    with path.open("rb") as f:
        library = plistlib.load(f)
    return library


def extract_raw_tracks(library: dict) -> list[RawAMTrack]:
    tracks = []
    for _, t in library.get("Tracks", {}).items():
        if not t.get("Name") or not t.get("Artist"):
            continue

        track = RawAMTrack(
            name=t.get("Name"),
            artist=t.get("Artist"),
            album_artist=t.get("Album Artist"),
            album=t.get("Album"),
            genre=t.get("Genre"),
            total_time=t.get("Total Time"),
            track_number=t.get("Track Number"),
            track_count=t.get("Track Count"),
            year=t.get("Year"),
            release_date=t.get("Release Date"),
            date_added=t.get("Date Added"),
            compilation=t.get("Compilation"),
        )
        tracks.append(track)

    return tracks


if __name__ == "__main__":
    lib = load_apple_music_library(LIBRARY_PATH)
    print(f"Number of tracks: {len(lib.get('Tracks', {}))}")
    tracks = extract_raw_tracks(lib)
    print(f"First track: {tracks[0]}")
