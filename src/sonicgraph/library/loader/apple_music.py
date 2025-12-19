import plistlib
from pathlib import Path

from sonicgraph import DATA_FOLDER
from sonicgraph.library.loader.loader import LibraryLoader
from sonicgraph.library.models import RawTrack

LIBRARY_PATH = Path(DATA_FOLDER / "am_library.xml")


class AppleMusicLibraryLoader(LibraryLoader):
    """Loads an Apple Music library from a plist file."""

    def __init__(self, path: Path = LIBRARY_PATH):
        self._plist = self._read_plist(path)

    def _read_plist(self, path: Path) -> dict:
        with path.open("rb") as f:
            library = plistlib.load(f)
        return library

    def parse(self) -> list[RawTrack]:
        if "Tracks" not in self._plist:
            raise ValueError("Invalid Apple Music library: missing 'Tracks'")
        tracks = []
        for _, t in self._plist.get("Tracks", {}).items():
            if not t.get("Name") or not t.get("Artist"):
                continue

            track = RawTrack(
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
    loader = AppleMusicLibraryLoader()
    tracks = loader.parse()
    print(tracks)
