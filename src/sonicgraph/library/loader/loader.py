from abc import ABC, abstractmethod

from sonicgraph.library.models import RawTrack


class LibraryLoader(ABC):
    """Loads a library from a source."""

    @abstractmethod
    def parse(self) -> list[RawTrack]: ...
