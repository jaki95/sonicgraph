from abc import ABC, abstractmethod

from sonicgraph.library.models import Library, RawTrack


class Builder(ABC):
    @abstractmethod
    def build(self, raw_tracks: list[RawTrack]) -> Library: ...
