"""Tests fuer den CrawlState."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawl_state import CrawlState


class TestCrawlState:
    def _state(self) -> tuple[CrawlState, Path]:
        tmp = Path(tempfile.mktemp(suffix=".json"))
        return CrawlState(tmp), tmp

    def test_initially_empty(self):
        state, _ = self._state()
        assert state.done_count() == 0
        assert state.error_count() == 0

    def test_mark_done(self):
        state, tmp = self._state()
        state.mark_done("spiegel.de")
        assert state.is_done("spiegel.de")
        assert not state.is_done("zeit.de")

    def test_persist_and_resume(self):
        state, tmp = self._state()
        state.mark_done("spiegel.de")
        state.mark_done("taz.de")

        # Reload from file
        state2 = CrawlState(tmp)
        assert state2.is_done("spiegel.de")
        assert state2.is_done("taz.de")
        assert state2.done_count() == 2

    def test_mark_error(self):
        state, _ = self._state()
        state.mark_error("broken.de", "ConnectionError")
        assert state.error_count() == 1
        assert "broken.de" in state.errors

    def test_reset(self):
        state, tmp = self._state()
        state.mark_done("a.de")
        state.mark_done("b.de")
        state.reset()
        assert state.done_count() == 0
        assert not tmp.exists()

    def test_no_duplicate_done(self):
        state, _ = self._state()
        state.mark_done("spiegel.de")
        state.mark_done("spiegel.de")
        assert state.done_count() == 1

    def test_corrupt_state_recovers(self):
        tmp = Path(tempfile.mktemp(suffix=".json"))
        tmp.write_text("not valid json", encoding="utf-8")
        state = CrawlState(tmp)
        assert state.done_count() == 0
