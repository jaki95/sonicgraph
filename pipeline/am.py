import plistlib
from pathlib import Path

from models import Track

LIBRARY_PATH = Path("data/am_library.xml")

def load_apple_music_library(path: Path) -> dict:
    with path.open("rb") as f:
        library = plistlib.load(f)
    return library

def extract_raw_tracks(library: dict) -> list[dict]:
    tracks = []
    for _, t in library.get("Tracks", {}).items():
        track = Track(
            title=t.get("Name"),
            artist_ids=[t.get("Artist")],
            album=t.get("Album"),
            album_id=t.get("Album"),
            bpm=t.get("BPM"),
            genre=t.get("Genre"),
            year=t.get("Year"),
            source="apple_music",
        )
        tracks.append(track)
    return tracks


if __name__ == "__main__":
    lib = load_apple_music_library(LIBRARY_PATH)
    print(f"Loaded keys: {lib.keys()}")
    print(f"Number of tracks: {len(lib.get('Tracks', {}))}")
    tracks = extract_raw_tracks(lib)
    print(f"First track: {tracks[0]}")
